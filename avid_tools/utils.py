from hashlib import md5
from pathlib import Path
from re import match
from typing import BinaryIO
from typing import Callable
from typing import TextIO

from click import ClickException
from click import Context
from click import Parameter
from xmlschema import XMLSchema
from xmlschema import XMLSchemaValidationError


# noinspection PyPep8Naming
class Indices:
    def __init__(self, avid_dir: Path):
        self.avid_dir = avid_dir

    @property
    def archiveIndex(self) -> Path:
        """Indices/archiveIndex.xml"""
        return self.avid_dir / "Indices" / "archiveIndex.xml"

    @property
    def contextDocumentationIndex(self) -> Path:
        """Indices/contextDocumentationIndex.xml"""
        return self.avid_dir / "Indices" / "contextDocumentationIndex.xml"

    @property
    def docIndex(self) -> Path:
        """Indices/docIndex.xml"""
        return self.avid_dir / "Indices" / "docIndex.xml"

    @property
    def fileIndex(self) -> Path:
        """Indices/fileIndex.xml"""
        return self.avid_dir / "Indices" / "fileIndex.xml"

    @property
    def tableIndex(self) -> Path:
        """Indices/tableIndex.xml"""
        return self.avid_dir / "Indices" / "tableIndex.xml"


# noinspection PyPep8Naming
class Schemas:
    def __init__(self, avid_dir: Path):
        self.avid_dir: Path = avid_dir

    @property
    def archiveIndex(self) -> Path:
        """Schemas/standard/archiveIndex.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "archiveIndex.xsd"

    @property
    def contextDocumentationIndex(self) -> Path:
        """Schemas/standard/contextDocumentationIndex.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "contextDocumentationIndex.xsd"

    @property
    def docIndex(self) -> Path:
        """Schemas/standard/docIndex.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "docIndex.xsd"

    @property
    def fileIndex(self) -> Path:
        """Schemas/standard/fileIndex.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "fileIndex.xsd"

    @property
    def researchIndex(self) -> Path:
        """Schemas/standard/researchIndex.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "researchIndex.xsd"

    @property
    def tableIndex(self) -> Path:
        """Schemas/standard/tableIndex.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "tableIndex.xsd"

    @property
    def XMLSchema(self) -> Path:
        """Schemas/standard/XMLSchema.xsd"""
        return self.avid_dir / "Schemas" / "standard" / "XMLSchema.xsd"

    @property
    def tables(self) -> dict[int, Path]:
        """Tables/tableN/tableN.xsd"""
        return {
            int(f.name.removeprefix("table")): f.joinpath(f.name).with_suffix(".xsd")
            for f in self.avid_dir.joinpath("Tables").iterdir()
            if f.is_dir() and match(r"table\d+", f.name)
        }


class AVID:
    def __init__(self, avid_dir: Path):
        self.dir: Path = avid_dir

    @property
    def indices(self) -> Indices:
        """Indices"""
        return Indices(self.dir)

    @property
    def schemas(self) -> Schemas:
        """Schemas"""
        return Schemas(self.dir)

    @property
    def tables(self) -> dict[int, Path]:
        """Tables"""
        return {
            int(f.name.removeprefix("table")): f.joinpath(f.name).with_suffix(".xml")
            for f in self.dir.joinpath("Tables").iterdir()
            if f.is_dir() and match(r"table\d+", f.name)
        }


def find_avid_dir(path: Path, *, raise_on_error: bool = True) -> Path | None:
    def inner(p: Path) -> Path | None:
        if p.joinpath("_metadata", "avid.db").is_file():
            return p
        elif p.parent != p:
            return inner(p.parent)
        else:
            return None

    avid_dir = inner(path)

    if raise_on_error and not avid_dir:
        raise ClickException(f"No _metadata/avid.db found from {path}")

    return avid_dir


def ctx_params(ctx: Context) -> dict[str, Parameter]:
    return {p.name: p for p in ctx.command.params}


def is_valid_suffix(suffix: str) -> bool:
    return match(r"^\.[a-zA-Z0-9]+$", suffix) is not None


def path_suffix(path: Path):
    if is_valid_suffix(suffix := path.suffix):
        return suffix
    return None


def remove_empty_dir(root: Path, path: Path) -> None:
    if path == root:
        return None
    elif not path.is_relative_to(root):
        return None
    elif not path.is_dir():
        return None
    elif next(path.iterdir(), None):
        return None

    path.rmdir()

    return remove_empty_dir(root, path.parent)


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


def print_line(
    *values: object,
    sep: str | None = " ",
    end: str | None = "\n",
    file: TextIO | BinaryIO | None = None,
    flush: bool = False,
) -> tuple[str, Callable[[], None]]:
    msg: str = sep.join(map(str, values))
    print(msg, end=end, file=file, flush=flush)
    return (
        msg,
        (lambda: None) if file else (lambda: print("\r" + (" " * len(msg)) + "\r", end="", flush=True)),
    )
