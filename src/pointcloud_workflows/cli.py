"""Noninteractive commands with optional ML imports at execution boundaries."""

import argparse
from contextlib import redirect_stdout
from importlib import metadata
import json
import platform
import sys
from collections.abc import Sequence

from . import __version__
from .protocol import ProtocolError, ProtocolParser


PLANNED_COMMANDS = ("benchmark",)


def _package_version(name: str) -> str | None:
    """Inspect distribution metadata without importing optional dependencies."""
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _doctor(as_json: bool, protocol: bool = False):
    report = {
        "version": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            name: _package_version(name)
            for name in ("PyYAML", "numpy", "plyfile", "torch", "safetensors", "warpconvnet")
        },
        "capabilities": {
            "config_validation": True,
            "dataset_preparation": True,
            "prepared_dataset_validation": True,
            "ml_pipeline": True,
            "gpu_runtime": "not_checked",
        },
    }
    if protocol:
        return report
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print(f"PointCloud Workflows {report['version']}")
        print(f"Python: {report['python']}")
        print(f"Platform: {report['platform']}")
        for name, version in report["packages"].items():
            print(f"{name}: {version or 'not installed'}")
        print("Configuration validation: available")
        print("CPU dataset preparation: available (PLY requires the io extra)")
        print("Prepared dataset validation: available")
        print("Training, evaluation and prediction: available with the ml extra")
        print("Backends: WarpConvNet (CUDA), PyTorch (CPU or CUDA)")
        print("Device selection runs when an ML command starts.")
    return 0


def _failure(error, code, protocol):
    if protocol:
        raise ProtocolError(code, str(error)) from error
    print(f"pcw: error: {error}", file=sys.stderr)
    return 2


def _validate_config(path: str, as_json: bool, protocol: bool = False):
    # Help, version, and diagnostics also work before any YAML is loaded.
    from .config import ConfigError, load_config

    try:
        config = load_config(path)
    except ConfigError as error:
        return _failure(error, "data_error", protocol)
    if protocol:
        return config.to_dict()
    if as_json:
        print(json.dumps(config.to_dict(), indent=2))
    else:
        print(f"Configuration is valid: {path}")
        print(f"Input directory: {config.paths.input_dir}")
        print(f"Output directory: {config.paths.output_dir}")
        print("Dataset paths and GPU availability have not been checked.")
    return 0


def _data_command(args: argparse.Namespace):
    from .datasets import DatasetError

    try:
        if args.command == "synthetic":
            from .synthetic import generate_synthetic

            path = generate_synthetic(args.output, args.seed)
            report = {"manifest": str(path), "seed": args.seed}
            message = f"Synthetic dataset written: {path}"
        elif args.command == "inspect":
            from .data_commands import inspect_dataset, inspect_prepared_dataset

            if args.prepared is not None:
                report = inspect_prepared_dataset(args.prepared)
                message = (
                    f"Prepared dataset is valid: {len(report['scenes'])} scenes, "
                    f"{report['total_input_points']} input points, "
                    f"{report['total_valid_points']} valid points, "
                    f"{report['total_invalid_points']} invalid rows removed, "
                    f"{report['total_voxels']} voxels "
                    f"(voxel size: {report['voxel_size']} {report['coordinate_unit']})."
                )
            else:
                report = inspect_dataset(args.manifest)
                message = (
                    f"Dataset is valid: {len(report['scenes'])} scenes, "
                    f"{report['total_points']} points, "
                    f"{report['total_invalid_points']} invalid rows to remove."
                )
        else:
            from .data_commands import preprocess_dataset

            report = preprocess_dataset(args.manifest, args.output, args.voxel_size)
            message = f"Prepared {len(report['scenes'])} scenes in {args.output}"
    except DatasetError as error:
        return _failure(error, "data_error", args.protocol_version is not None)
    if args.protocol_version is not None:
        return report
    if args.json:
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print(message)
    return 0


def _parser(protocol: bool = False) -> argparse.ArgumentParser:
    parser_type = ProtocolParser if protocol else argparse.ArgumentParser
    parser = parser_type(
        prog="pcw",
        description="PointCloud Workflows: GPU point-cloud segmentation with a CPU fallback.",
        allow_abbrev=False,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--protocol-version", metavar="VERSION", choices=("1",),
        help="emit the versioned JSON subprocess contract (must precede the command)",
    )
    commands = parser.add_subparsers(dest="command")

    doctor = commands.add_parser(
        "doctor", help="report the environment without loading ML libraries", allow_abbrev=False
    )
    doctor.add_argument("--json", action="store_true", help="print machine-readable diagnostics")

    config = commands.add_parser(
        "config", help="validate application configuration", allow_abbrev=False
    )
    config_commands = config.add_subparsers(dest="config_command", required=True)
    validate = config_commands.add_parser(
        "validate", help="check configuration without running a pipeline", allow_abbrev=False
    )
    validate.add_argument("--config", required=True, metavar="PATH", help="YAML configuration file")
    validate.add_argument("--json", action="store_true", help="print the resolved configuration")

    synthetic = commands.add_parser(
        "synthetic", help="generate a small seeded CPU demonstration dataset", allow_abbrev=False
    )
    synthetic.add_argument("--output", required=True, metavar="DIR", help="new output directory")
    synthetic.add_argument("--seed", type=int, default=0, help="integer seed in 0..4294967295")
    synthetic.add_argument("--json", action="store_true", help="print the generated manifest path")

    inspect = commands.add_parser(
        "inspect", help="validate a raw or prepared dataset and all scene arrays", allow_abbrev=False
    )
    inspect_source = inspect.add_mutually_exclusive_group(required=True)
    inspect_source.add_argument("--manifest", metavar="PATH", help="raw dataset manifest JSON")
    inspect_source.add_argument("--prepared", metavar="PATH", help="prepared dataset metadata JSON")
    inspect.add_argument("--json", action="store_true", help="print scene and label statistics")

    preprocess = commands.add_parser(
        "preprocess", help="filter and voxelize a dataset on the CPU", allow_abbrev=False
    )
    preprocess.add_argument("--manifest", required=True, metavar="PATH", help="dataset manifest JSON")
    preprocess.add_argument("--output", required=True, metavar="DIR", help="new output directory")
    preprocess.add_argument(
        "--voxel-size", type=float, required=True,
        help="positive voxel edge length in the manifest's coordinate unit",
    )
    preprocess.add_argument("--json", action="store_true", help="print the prepared dataset metadata")

    run = commands.add_parser(
        "run", help="inspect durable training runs without modifying them", allow_abbrev=False
    )
    run_commands = run.add_subparsers(dest="run_command", required=True)
    run_inspect = run_commands.add_parser(
        "inspect", help="verify completion and read a training run snapshot", allow_abbrev=False
    )
    run_inspect.add_argument("--output", required=True, metavar="DIR", help="existing training run directory")
    run_inspect.add_argument("--json", action="store_true", help="print the read-only run snapshot")

    for name, summary in (
        ("train", "train a segmentation model from prepared scenes"),
        ("evaluate", "evaluate a saved model at original point resolution"),
        ("predict", "export predicted dataset class IDs in original point order"),
    ):
        command = commands.add_parser(name, help=summary, allow_abbrev=False)
        command.add_argument("--prepared", required=True, metavar="PATH", help="prepared.json metadata")
        command.add_argument(
            "--output", required=True, metavar="DIR",
            help="training run directory (new unless --resume)" if name == "train" else "new output directory",
        )
        command.add_argument(
            "--device", choices=("auto", "cpu", "cuda"), default="auto",
            help="execution device (default: auto)",
        )
        command.add_argument(
            "--max-voxels", type=int, default=None if name == "train" else 100000,
            help="maximum voxels per scene; larger scenes fail without truncation (default: 100000)",
        )
        command.add_argument("--json", action="store_true", help="print the run report as JSON")
        if name == "train":
            command.add_argument(
                "--backend", choices=("auto", "torch", "warpconvnet"), default="auto",
                help="WarpConvNet MinkUNet18 or portable PyTorch voxel MLP (default: auto)",
            )
            command.add_argument("--epochs", type=int, help="total epochs for a new run (default: 20)")
            command.add_argument("--learning-rate", type=float, help="Adam learning rate (default: 0.001)")
            command.add_argument("--seed", type=int, help="initial random seed (default: 0)")
            command.add_argument(
                "--resume", action="store_true",
                help="resume the run in --output using saved settings and the latest complete epoch",
            )
        else:
            command.add_argument("--model", required=True, metavar="DIR", help="saved model bundle")
            command.add_argument(
                "--split", choices=("train", "val", "test", "predict"),
                default="test" if name == "evaluate" else "predict",
                help="dataset split to process",
            )

    for name in PLANNED_COMMANDS:
        commands.add_parser(
            name,
            help="planned; not implemented",
            description=f"{name} is not implemented in this version.",
            allow_abbrev=False,
        )
    return parser


def _ml_command(args: argparse.Namespace):
    from .datasets import DatasetError
    from .models import MLRuntimeError

    try:
        from .ml import evaluate_model, predict_model, train_model

        common = {"device": args.device, "max_voxels": args.max_voxels}
        if args.command == "train":
            report = train_model(
                args.prepared, args.output, backend=args.backend, epochs=args.epochs,
                learning_rate=args.learning_rate, seed=args.seed, resume=args.resume, **common,
            )
        else:
            operation = evaluate_model if args.command == "evaluate" else predict_model
            report = operation(
                args.prepared, args.model, args.output, split=args.split, **common,
            )
    except DatasetError as error:
        return _failure(error, "data_error", args.protocol_version is not None)
    except OSError as error:
        return _failure(error, "io_error", args.protocol_version is not None)
    except (MLRuntimeError, RuntimeError) as error:
        return _failure(error, "runtime_error", args.protocol_version is not None)
    if args.protocol_version is not None:
        return report
    if args.json:
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print(f"{args.command.capitalize()} complete: {args.output}")
        print(json.dumps(report, indent=2, allow_nan=False))
    return 0


def _run_command(args):
    from .models import MLRuntimeError
    from .runs import inspect_run

    try:
        report = inspect_run(args.output)
    except MLRuntimeError as error:
        return _failure(error, "data_error", args.protocol_version is not None)
    if args.protocol_version is not None:
        return report
    if args.json:
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print(f"Run {report['run_id']}: {report['state']} ({report['output']})")
        print("Read-only snapshot; execution activity and resume compatibility are not checked.")
    return 0


def _dispatch(args, parser):
    protocol = args.protocol_version is not None
    if args.command is None:
        if protocol:
            raise ProtocolError("usage_error", "a command is required in protocol mode")
        parser.print_help()
        return 0
    if args.command == "doctor":
        return _doctor(args.json, protocol)
    if args.command == "config":
        return _validate_config(args.config, args.json, protocol)
    if args.command in {"synthetic", "inspect", "preprocess"}:
        return _data_command(args)
    if args.command in {"train", "evaluate", "predict"}:
        return _ml_command(args)
    if args.command == "run":
        return _run_command(args)
    return _failure(
        ValueError(f"'{args.command}' is not implemented in this version. "
                   "Use 'pcw --help' to see the available commands."),
        "usage_error", protocol,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Return a process exit status; never start an interactive menu."""
    from .protocol import command_hint, encode, requested, validate_request

    arguments = list(sys.argv[1:] if argv is None else argv)
    protocol = requested(arguments)
    parser = _parser(protocol)
    if not protocol:
        return _dispatch(parser.parse_args(arguments), parser)

    command = command_hint(arguments)
    try:
        validate_request(arguments)
        args = parser.parse_args(arguments)
        # Third-party progress messages belong on stderr. Results are passed as
        # objects, never recovered by parsing our own printed output.
        with redirect_stdout(sys.stderr):
            result = _dispatch(args, parser)
        response = encode(command, result=result)
        status = 0
    except ProtocolError as error:
        response = encode(command, error=error)
        status = 2
    except OSError as error:
        response = encode(command, error=ProtocolError("io_error", str(error)))
        status = 2
    except Exception as error:
        response = encode(command, error=ProtocolError("internal_error", str(error)))
        status = 1
    print(response)
    return status
