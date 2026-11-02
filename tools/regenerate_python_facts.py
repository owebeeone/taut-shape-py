"""Development-only regeneration of bundled Python types and codec facts."""
from pathlib import Path
import hashlib

from taut.gen.scaffold import python_api
from taut.ir.load import load_schema
from taut.ir.validate import validate_or_raise

ROOT = Path(__file__).resolve().parents[1]


def main():
    for shape in ("atom", "crdt", "log", "stream", "swmr", "value"):
        source = ROOT / "src" / "taut_shape" / "schemas" / f"shape_{shape}.taut.py"
        schema = load_schema(source)
        validate_or_raise(schema)
        header = ("# VENDORED GENERATED CODE — DO NOT EDIT.\n"
                  f"# Source: taut-shape/ir/{source.name}\n"
                  f"# Schema sha256: {hashlib.sha256(source.read_bytes()).hexdigest()}\n"
                  "# Regenerate: python tools/regenerate_python_facts.py\n")
        target = ROOT / "src" / "taut_shape" / shape / "_generated.py"
        target.write_text(header + python_api(schema, identity=f"taut_shape.{shape}"), encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
