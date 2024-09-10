from hashlib import md5
from pathlib import Path

from acacore.utils.functions import is_valid_suffix
from click import argument
from click import BadParameter
from click import Context
from click import Parameter
from click import Path as ClickPath
from xmlschema import XMLSchema
from xmlschema import XMLSchemaValidationError


def argument_avid_dir(database_exists: bool):
    if database_exists:

        def _callback(ctx: Context, param: Parameter, value: str) -> Path:
            if not (path := Path(value)).joinpath("_metadata", "avid.db").is_file():
                raise BadParameter(f"No _metadata/avid.db found in {path}", ctx, param)
            return path

        return argument(
            "AVID_DIR",
            type=ClickPath(exists=True, file_okay=False, writable=True, readable=True),
            callback=_callback,
        )
    else:

        def _callback(_ctx: Context, _param: Parameter, value: str) -> Path:
            return Path(value)

        return argument(
            "AVID_DIR",
            type=ClickPath(exists=True, file_okay=False, writable=True, readable=True),
            callback=_callback,
        )


def ctx_params(ctx: Context) -> dict[str, Parameter]:
    return {p.name: p for p in ctx.command.params}


def path_suffix(path: Path):
    if is_valid_suffix(suffix := path.suffix):
        return suffix
    return None


def file_md5(path: Path) -> str:
    file_hash = md5()
    with path.open("rb") as f:
        chunk = f.read(2**20)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(2**20)
    return file_hash.hexdigest().upper()


def validate_xml(xml: str | Path, schema: XMLSchema | Path) -> XMLSchemaValidationError | None:
    if isinstance(schema, Path):
        schema = XMLSchema(schema)

    try:
        schema.validate(xml)
    except XMLSchemaValidationError as e:
        return e
