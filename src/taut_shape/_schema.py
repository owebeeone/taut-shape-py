"""Load canonical shape schemas bundled in the installed distribution."""

from __future__ import annotations

from importlib.resources import as_file, files

from taut.ir.load import load_schema
from taut.ir.model import Schema


def load_packaged_schema(shape: str) -> Schema:
    """Load one bundled ``shape_<name>.taut.py`` schema.

    ``as_file`` also supports importers that do not expose package resources as
    ordinary filesystem paths.  The temporary path only needs to live for the
    duration of ``load_schema`` because the returned model is self-contained.
    """

    resource = files("taut_shape").joinpath("schemas", f"shape_{shape}.taut.py")
    with as_file(resource) as path:
        return load_schema(path)
