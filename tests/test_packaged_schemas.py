"""Keep the wheel's runtime schemas byte-identical to the contract repo."""

from importlib.resources import files
from pathlib import Path

import pytest

_SHAPES = ("atom", "crdt", "log", "stream", "swmr", "value")


@pytest.mark.parametrize("shape", _SHAPES)
def test_packaged_schema_matches_contract(shape: str) -> None:
    contract = (
        Path(__file__).parents[2] / "taut-shape" / "ir" / f"shape_{shape}.taut.py"
    )
    packaged = files("taut_shape").joinpath("schemas", f"shape_{shape}.taut.py")

    assert packaged.read_bytes() == contract.read_bytes()
