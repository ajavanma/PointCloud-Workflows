# JSON execution protocol

Use the versioned protocol when invoking PCW from another program:

```sh
pcw --protocol-version 1 doctor
pcw --protocol-version 1 synthetic --output runs/data --seed 42
pcw --protocol-version 1 inspect --manifest runs/data/manifest.json
pcw --protocol-version 1 preprocess --manifest runs/data/manifest.json --output runs/prepared --voxel-size 0.1
pcw --protocol-version 1 run inspect --output runs/model
```

The global option must appear **once, before the command**.
`--protocol-version=1` is equivalent. The existing command-local `--json` remains
supported and is redundant in protocol mode. Omitting the protocol option keeps
the existing human-readable and `--json` behavior, including their error output.
Saved datasets, model bundles, checkpoints, and `rptu-*` identifiers are unchanged.

## Response envelope

A handled invocation emits exactly one JSON object on stdout, followed by a
newline. Progress and diagnostic output belong on stderr. JSON values are finite:
`NaN` and `Infinity` are not valid protocol values. Object key order and whitespace
are not part of the contract.

For example, a successful synthetic generation returns:

```json
{
  "protocol_version": 1,
  "pcw_version": "0.2.0.dev0",
  "command": "synthetic",
  "ok": true,
  "result": {"manifest": "/work/runs/data/manifest.json", "seed": 42},
  "error": null
}
```

The example path depends on the requested output and working directory. These
fields are present in every envelope:

| Field | Contract |
| --- | --- |
| `protocol_version` | Integer `1`; identifies this execution protocol. |
| `pcw_version` | String containing the installed PCW package version. |
| `command` | Canonical command name from the table below. Parse errors use the attempted name, or an empty string when it cannot be determined. |
| `ok` | Boolean; `true` only for a successful command. |
| `result` | Command-specific object on success; `null` on failure. |
| `error` | `null` on success; an object containing string `code` and `message` fields on failure. |

The success `result` is the same report object returned by the command's existing
`--json` option. Error messages are for people and may gain context or change
wording. Clients should branch on `code`, not parse `message`.

| Command name | Success result |
| --- | --- |
| `doctor` | Package/Python/platform versions, dependency metadata, and capabilities. It does not initialize or validate a GPU. |
| `config validate` | Resolved configuration: `schema_version`, `paths`, and `runtime`. |
| `synthetic` | Absolute `manifest` path and integer `seed`. |
| `inspect` with `--manifest` | Raw dataset report with `kind: "rptu-raw-dataset"`. |
| `inspect` with `--prepared` | Prepared dataset report with `kind: "rptu-prepared-dataset"`. |
| `preprocess` | Prepared dataset report with `kind: "rptu-prepared-dataset"`. |
| `train` | Training report with `kind: "rptu-training-report"`; completed resume returns the saved verified report. |
| `evaluate` | Original-point evaluation report with `kind: "rptu-evaluation"`. |
| `predict` | Prediction export report with `kind: "rptu-predictions"`. |
| `run inspect` | Read-only training-run snapshot described below. |

See [configuration](gitbook/configuration.md), [dataset reports](datasets.md),
[training](gitbook/train.md), and [evaluation](gitbook/test.md) for command data
and artifact semantics. `benchmark` remains unimplemented.

## Failures and process status

| Error code | Exit status | Meaning |
| --- | --- | --- |
| `usage_error` | `2` | Invalid command, arguments, protocol selection, or unavailable command. |
| `data_error` | `2` | Invalid configuration, dataset, or inspected run/artifacts. |
| `runtime_error` | `2` | Model runtime, device, checkpoint, or resume failure. |
| `io_error` | `2` | An uncategorized filesystem or operating-system failure. |
| `internal_error` | `1` | An unexpected implementation failure. |

Successful responses exit `0`. Data and runtime validators may wrap an I/O cause
in their domain error, so a missing input file can be `data_error` rather than
`io_error`.

A missing, unsupported, duplicate, or misplaced protocol version produces a
version-1 `usage_error` envelope without executing the command. Help (`-h` or
`--help`) and `--version` are rejected in protocol mode; call `doctor` for package
metadata and use ordinary help outside protocol mode.

Process launch failures, signals, forced termination, or a failed stdout stream
can prevent a complete response. A client must inspect both the process status
and the envelope. Treat absent, truncated, multiple, or invalid JSON responses as
transport failures, not successful commands. A client must not automatically
rerun a failed command: the process may already have written output.

## Read-only run inspection

```sh
pcw --protocol-version 1 run inspect --output runs/model
# Equivalent report without the envelope:
pcw run inspect --output runs/model --json
```

The result has these fields:

| Field | Value |
| --- | --- |
| `schema_version` | Integer `1`, for this inspection report. |
| `kind` | `"pcw-run-inspection"`. |
| `run_id` | Identity from the existing `run.json`. |
| `output` | Absolute run directory path. |
| `state` | `"completed"` or `"incomplete"`. |
| `spec` | The saved immutable training specification. |
| `completion` | Verified completion-marker object for a completed run; otherwise `null`. |

Inspection validates the run metadata and, when present, the completion marker,
its attempt reference, and checksums of the published model files. Corrupt
completion data is an error; it is not reported as an incomplete run. The command
does not import PyTorch, acquire or create a writer lock, change attempt records,
repair files, or create missing directories.

This is a snapshot of saved state. `incomplete` does not say whether a process is
running, whether a checkpoint exists, or whether the current runtime can resume
it. A writer can finish after inspection. Resume eligibility remains the
responsibility of `train --resume`, which enforces the original settings, data,
and runtime. Existing local POSIX locking does not establish ownership between
machines or on object storage.

## Client compatibility

Protocol, toolkit, and artifact versions serve different purposes. A PCW package
update can preserve protocol `1`; dataset/model schema changes need their own
compatibility decisions. This protocol does not relax training's strict runtime
checks or promise that every package version supports every future command.

Clients should require the requested protocol version, check the command name,
validate required field types and success/error consistency, and tolerate
additional fields. New optional response fields can be added within version `1`.
Removing required fields or changing their types or meaning requires a new
protocol version. Report `kind` and `schema_version` still select the relevant
artifact/report contract. Unknown error codes should remain failures and be
surfaced to the caller.

Pass arguments as an array, with an explicit executable and working directory.
Keep JSON response and diagnostic buffers bounded. Paths and metadata cross this
boundary; point arrays and model weights stay in their existing files.

The companion Go client, `pcw-go`, is being developed in a private repository.
Its local runner invokes this public protocol with cancellation, bounded output,
and explicit training resume. Python PCW continues to own numerical processing
and artifact verification. Container and Kubernetes runners are later extensions;
the local contract does not provide automatic retries or distributed scheduling.
