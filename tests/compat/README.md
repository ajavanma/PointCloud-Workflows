# External compatibility reference

PCW does not retain research source or historical Git ancestry. These explicit
suites generate temporary synthetic fixtures from the public RPTU revision in
`provenance.json` and verify its exact package tree before executing it.
The external source and generated outputs are never shipped in PCW.

Prepare a separate checkout:

```sh
git clone https://github.com/ajavanma/RPTU_AI_Toolkit.git /tmp/pcw-compat-reference
git -C /tmp/pcw-compat-reference checkout --detach 73319745a0aacb410401df71ec890a1cecc00cf8
export PCW_LEGACY_SOURCE=/tmp/pcw-compat-reference
python -m unittest discover -s tests/compat -p test_legacy_artifacts.py -v
```

This suite runs both implementations with the current interpreter and dependencies.
It checks identical raw/prepared data, inference outputs, completed retries, and
interrupted-run continuation. It isolates the package rename from a runtime upgrade.

To test the actual PyTorch upgrade, also supply a separate interpreter containing
PyTorch 2.10.0, NumPy, PyYAML and safetensors 0.7.0. The main interpreter must use
PyTorch 2.13.0:

```sh
export PCW_LEGACY_PYTHON=/path/to/torch210-env/bin/python
python -m unittest discover -s tests/compat -p test_runtime_upgrade.py -v
```

That suite tests loading completed 2.10 models for 2.13 inference and rejecting
2.10 training resumes without modifying files. It does not rewrite runtime fields
to simulate an older producer. CI runs both suites explicitly. Missing or incorrect
reference/interpreter settings fail clearly; the ordinary unit, CLI, and ML suites
work without either external dependency.
