"""Create fixtures with the historical package selected through PYTHONPATH.

Run only through test_legacy_artifacts: it extracts the pinned historical
source first. This process must never import the current compatibility shims.
"""

import json
from pathlib import Path
import shutil
import sys
from unittest.mock import patch

import torch

import rptu_ai_toolkit
from rptu_ai_toolkit import ml
from rptu_ai_toolkit.artifacts import write_json
from rptu_ai_toolkit.data_commands import (
    inspect_dataset,
    inspect_prepared_dataset,
    preprocess_dataset,
)
from rptu_ai_toolkit.synthetic import generate_synthetic


def main():
    source, output = (Path(argument).resolve() for argument in sys.argv[1:])
    loaded = Path(rptu_ai_toolkit.__file__).resolve()
    if loaded != source / "rptu_ai_toolkit/__init__.py":
        raise RuntimeError(f"expected the extracted historical package, loaded {loaded}")
    if rptu_ai_toolkit.__version__ != "0.2.0.dev0":
        raise RuntimeError("unexpected historical toolkit version")
    torch.set_num_threads(1)
    output.mkdir()
    manifest = generate_synthetic(output / "raw", seed=12)
    preprocess_dataset(manifest, output / "prepared", 0.5)
    prepared = output / "prepared/prepared.json"
    write_json(output / "raw-report.json", inspect_dataset(manifest))
    write_json(output / "prepared-report.json", inspect_prepared_dataset(prepared))
    ml.train_model(prepared, output / "completed", device="cpu", backend="torch", epochs=3, seed=9)

    # Export the original standalone inference bundle: only its metadata and
    # numeric weights are required, without a training run or completion marker.
    inference = output / "inference"
    inference.mkdir()
    for name in ("bundle.json", "weights.safetensors"):
        shutil.copyfile(output / "completed" / name, inference / name)
    ml.evaluate_model(prepared, inference, output / "evaluation", device="cpu")
    ml.predict_model(prepared, inference, output / "prediction", device="cpu")

    original = ml.save_checkpoint

    def interrupt_after_first_epoch(*arguments, **keywords):
        result = original(*arguments, **keywords)
        if len(arguments[3]) == 1:
            raise KeyboardInterrupt("compatibility fixture: completed epoch one")
        return result

    with patch.object(ml, "save_checkpoint", side_effect=interrupt_after_first_epoch):
        try:
            ml.train_model(prepared, output / "interrupted", device="cpu", backend="torch", epochs=3, seed=9)
        except KeyboardInterrupt:
            pass
        else:
            raise RuntimeError("fixture generation did not interrupt training")
    if (output / "interrupted/complete.json").exists():
        raise RuntimeError("interrupted fixture is unexpectedly complete")
    checkpoint = json.loads((output / "interrupted/latest.json").read_text())
    state = json.loads((output / "interrupted" / checkpoint["path"]).read_text())
    if state["epoch"] != 1:
        raise RuntimeError("interrupted fixture does not retain epoch one")


if __name__ == "__main__":
    main()
