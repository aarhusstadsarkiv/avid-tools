from enum import Enum
from functools import lru_cache
from typing import Any, Mapping, Optional, Protocol
from pathlib import Path
from dataclasses import dataclass
from avid_validator import config as av_config
from avid_validator.common import utils


class Loadable(Protocol):
    @staticmethod
    def load() -> Any: ...


@dataclass
class XMLIndices:
    """
    Dicts of index XMLs
    """

    archiveIndex: Optional[Mapping[str, Any]]
    tableIndex: Optional[Mapping[str, Any]]
    docIndex: Optional[Mapping[str, Any]]
    fileIndex: Optional[Mapping[str, Any]]
    researchIndex: Optional[Mapping[str, Any]]
    contextIndex: Optional[Mapping[str, Any]]

    @lru_cache()
    @staticmethod
    def load() -> XMLIndices:
        def _prepend(path: str) -> Optional[dict[Any, Any]]:
            return utils.prepare_xml(av_config.avid_dir / path)

        return XMLIndices(
            archiveIndex=_prepend("Indices/archiveIndex.xml"),
            tableIndex=_prepend("Indices/tableIndex.xml"),
            contextIndex=_prepend("Indices/contextDocumentationIndex.xml"),
            docIndex=_prepend("Indices/docIndex.xml"),
            fileIndex=_prepend("Indices/fileIndex.xml"),
            researchIndex=_prepend("Indices/researchIndex.xml"),
        )


@dataclass
class ValidationContext:
    """
    Context for validation functions
    """

    root: Path

    @property
    def indices(self) -> Path:
        return self.root / "Indices"

    @property
    def tables(self) -> Path:
        return self.root / "Tables"

    @property
    def schemas(self) -> Path:
        return self.root / "Schemas"

    @property
    def documents(self) -> Path:
        return self.root / "Documents"

    @property
    def context_docs(self) -> Path:
        return self.root / "ContextDocumentation"

    @lru_cache()
    @staticmethod
    def load() -> ValidationContext:
        return ValidationContext(root=av_config.avid_dir)


class ValidationType(Enum):
    DOCS = "docs"
    INDICES = "indices"
    SCHEMAS = "schemas"
    CONTEXTDOCS = "contextdocs"
    TABLES = "tables"
