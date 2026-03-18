from dataclasses import dataclass
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

from tqdm import tqdm
from avid_validator.common import utils
from avid_validator.common.archive import ValidationContext, ValidationType, XMLIndices
from avid_validator.common.database import FileHandler
from avid_validator.common.description import categorize, describe
from avid_validator.common.graph import TableNode
from avid_validator.common.report import GenReport, fail, ok
from avid_validator.common.rules import require_files


from avid_validator.common.rules import (
    require_files,
    require_node_connectivity,
    validate_xml_against_standard_schema as standard_xml_schema_validate,
)

logger = logging.getLogger(__name__)


@describe(
    """Mappen Indices skal indeholde følgende indeksfiler med oplysninger om arkiveringsversionen og dens indhold:
– fileIndex.xml
– archiveIndex.xml
– contextDocumentationIndex.xml
– tableIndex.xml"""
)
@categorize(ValidationType.INDICES)
def validate_4c1a(ctx: ValidationContext) -> GenReport:
    yield require_files(
        ctx.indices,
        "fileIndex.xml",
        "archiveIndex.xml",
        "contextDocumentationIndex.xml",
        "tableIndex.xml",
    )


@describe(
    """Hvis arkiveringsversionen indeholder digitale dokumenter, lyd, video eller geodata, skal mappen Indices endvidere indeholde følgende indeksfil:
– docIndex.xml"""
)
@categorize(ValidationType.INDICES)
def validate_4c1b(ctx: ValidationContext) -> GenReport:
    if ctx.documents.exists():
        yield require_files(ctx.indices, "docIndex.xml")
    else:
        yield ok()


@describe("""Hvis arkiveringsversionen indeholder data, som er skabt i forbindels 
med forskning med anvendelse af videnskabelig metode og er afleveret efter reglerne i bilag 9,
skal mappen Indices endvidere indeholde følgende indeksfil:
– researchIndex.xml""")
@categorize(ValidationType.INDICES)
def validate_4c1c(ctx: ValidationContext, indeces: XMLIndices) -> GenReport:
    if archive_idx := indeces.archiveIndex:
        contains_research = archive_idx["archiveIndex"]["containsResearchData"]

        if contains_research == "1" or contains_research == "true":
            yield require_files(ctx.indices, "researchIndex.xml")
            yield standard_xml_schema_validate(ctx, ctx.indices / "researchIndex.xml")
    else:
        yield ok()


@describe("Alle indeksfiler skal overholde deres tilhørende skema, jf. bilag 8.")
@categorize(ValidationType.INDICES)
def validate_4c1d(ctx: ValidationContext) -> GenReport:
    for xml_file in ctx.indices.glob("*.xml"):
        if r := standard_xml_schema_validate(ctx, xml_file):
            yield r


@describe("""fileIndex.xml skal indeholde en komplet liste over samtlige filer,
der findes i arkiveringsversionen. fileIndex.xml er dog undtaget fra denne regel.""")
@categorize(ValidationType.INDICES)
def validate_4c2a(ctx: ValidationContext) -> GenReport:
    # TODO: Add hex validation
    file_index = utils.prepare_xml(ctx.indices / "fileIndex.xml")

    has_failed = False
    if file_index is None:
        yield fail("fileIndex.xml does not exist!")
        return

    file_paths = []
    for item in file_index["fileIndex"]["f"]:
        file_path: str = item["foN"]
        file_path = (
            file_path.replace("\\", "/").replace(f"{ctx.root.name}/", "")
            + f"/{item["fiN"]}"
        )
        file_paths.append(file_path)

    doc_containers = [
        "Documents",
        "Indices",
        "ContextDocumentation",
        "Tables",
        "Schemas",
    ]
    for doc_container in doc_containers:
        for path in (ctx.root / doc_container).rglob("*"):
            if path.name == "fileIndex.xml":
                continue

            if path.is_file():
                rel_path = path.relative_to(ctx.root)

                if str(rel_path) not in file_paths:
                    has_failed = True
                    yield fail(f"fileIndex file, {rel_path}, not contained in archive!")
    if not has_failed:
        yield ok()


@describe(
    """[fileIndex.xml] For hver enkelt fil i arkiveringsversionen angives de oplysninger, som fremgår af figur 4.2."""
)
@categorize(ValidationType.INDICES)
def validate_4c2b(ctx: ValidationContext, indeces: XMLIndices) -> GenReport:
    file_index = ctx.indices / "fileIndex.xml"
    yield standard_xml_schema_validate(ctx, file_index)

    assert indeces.fileIndex is not None
    files = indeces.fileIndex["fileIndex"]["f"]

    logger.info("Run file md5 checks")
    with FileHandler() as handler:
        for file in tqdm(files):
            path = "/".join(file["foN"].split("\\")[1:])
            filename = file["fiN"]
            filehash = file["md5"]
            file_path: Path = Path(path) / filename

            if handler.is_modified(file_path):
                if not file_path.exists():
                    logger.warning("Invalid file path found")
                    yield fail(f"{file_path} is not valid!")
                    continue

                calc_hash = hashlib.md5(file_path.read_bytes()).hexdigest().upper()

                if not calc_hash == filehash:
                    yield fail(f"{file_path} has incorrect hash compared to fileIndex!")
                else:
                    handler.mark_clean(file_path)


# 4c4b --||--


@describe("""contextDocumentationIndex.xml skal indeholde et indeks over de dokumenter,
som findes i arkiveringsversionens kontekstdokumentation.""")
@categorize(ValidationType.INDICES)
def validate_4c4a(ctx: ValidationContext, indeces: XMLIndices) -> GenReport:
    yield standard_xml_schema_validate(
        ctx, ctx.indices / "contextDocumentationIndex.xml"
    )

    documents = indeces.contextIndex["contextDocumentationIndex"][  # pyright: ignore
        "document"
    ]
    ids = [doc["documentID"] for doc in documents]
    context_dir_ids = os.listdir(
        ctx.context_docs.joinpath("docCollection1")
    )  # Assume that no more than 10,000 documents will ever appear in contextDoc

    for id in ids:
        if id not in context_dir_ids:
            yield fail(
                f"contextDocumentationIndex document entry {id} not present in contextDocumentation folder!"
            )

    for id in context_dir_ids:
        if id not in ids:
            yield fail(
                f"contextDocumentation folder document entry {id} not present in contextDocumentationIndex!"
            )


@describe(
    """tableIndex.xml skal indeholde en angivelse af en relationel databasestruktur på 1. normalform 
eller højere. Samtlige tabeller i arkiveringsversionen skal angives."""
)
@categorize(ValidationType.INDICES)
def validate_4c5a(ctx: ValidationContext) -> GenReport:
    """
    As per https://www.rigsarkivet.dk/wp-content/uploads/2025/08/Vejledning-til-bekendtgoerelse-128.pdf
    following rules must apply:
        1. Enhver tabel skal for alle rækker have samme antal kolonner (dvs. multivariable attributter er
        ikke tilladt).
        2. Alle tabeller skal have et navn, og navnet skal være entydigt.
        3. Alle kolonner skal have et navn, og navnet skal være entydigt inden for den pågældende tabel.
        4. Rækkefølgen af rækker må ikke være betydningsbærende i nogen tabel.
        5. Rækkefølgen af kolonner må ikke være betydningsbærende i nogen tabel.
        6. Enhver tabel skal have defineret et eller flere felter, som udgør en entydig primærnøgle (ingen
        rækker må være ens).
        7. En fremmednøgle skal være relateret til en primærnøgle.
        8. En fremmednøgle må ikke være relateret til dele af en sammensat primærnøgle. Der skal
        således være sammenfald mellem antal felter i primærnøgle og fremmednøgle.
        9. Alle forbindelser mellem tabeller er udtrykkelige (direkte). Således kan der ikke forekomme
        forbindelser mellem tabeller på baggrund af fortolkning af deres feltindhold. (Hierarkiske
        databaser, netværksdatabaser og objektrelationelle databaser er således per definition ikke
        relationelle databaser).
        Det følger heraf, at en fremmednøgle kun må relateres til en specifik tabel (ved dennes
        primærnøgle). Fremmednøglen må altså ikke angives at være relateret til flere tabeller med
        henblik på, at konkrete poster vil være relateret til én ud af flere forskellige tabeller alt efter
        ”henvisningens art”.
        10. Der bør ikke være tabeller uden relation til en eller flere andre tabeller
    """

    table_idx = ctx.indices / "tableIndex.xml"
    xml_dict = utils.prepare_xml(table_idx)

    if not xml_dict:
        yield fail("No tableIndex.xml content found!")
        return

    tables = xml_dict["siardDiark"]["tables"]["table"]
    nodes: list[TableNode] = []
    for table in tables:
        name = table["name"]
        referenced_tables = []
        referenced_columns = []

        if "foreignKeys" in table:
            foreignkeys = table["foreignKeys"]["foreignKey"]
            if isinstance(foreignkeys, dict):
                foreignkeys = [foreignkeys]

            for foreignkey in foreignkeys:
                ref_tables = foreignkey["referencedTable"]
                xml_references = foreignkey["reference"]
                if isinstance(xml_references, dict):
                    xml_references = [xml_references]

                ref_columns = [item["referenced"] for item in xml_references]

                for ref_column in ref_columns:
                    referenced_tables.append(ref_tables)
                    referenced_columns.append(ref_column)

        primary_keys: list[str] | str = table["primaryKey"]["column"]

        nodes.append(
            TableNode(
                name=name,
                referenced_tables=referenced_tables,
                primarykeys=(
                    [primary_keys] if isinstance(primary_keys, str) else primary_keys
                ),
                referenced_columns=referenced_columns,
            )
        )
    yield require_node_connectivity(nodes)

    def _node_from_name(name: str) -> Optional[TableNode]:
        for node in nodes:
            if node.name == name:
                return node

    # Assert that point 7 in above docstring is followed
    for node in nodes:
        if len(node.primarykeys) == 0:
            yield fail(f"table {node.name} has no primary keys!")
        for reference_tablename, reference_columnname in zip(
            node.referenced_tables, node.referenced_columns
        ):
            ref_node = _node_from_name(reference_tablename)
            if ref_node is None:
                yield fail(
                    f"{node.name} references table {reference_tablename} that does not exist!"
                )
                continue
            if reference_columnname not in ref_node.primarykeys:
                yield fail(
                    f"table {node.name}.{reference_columnname} did not reference the primary key of table {reference_tablename} ({ref_node.primarykeys})"
                )


# TODO: Add validate 4c1c


# 4c2b  -- Tilstrækkeligt med Schema validering?
# 4c3  archiveIndex.xml validering  -- XML Schema validering tilstrækkeligt?

# 4c4b --||--


@describe(
    """»tableIndex.xml« skal overholde det generelle XML-skema »tableIndex.xsd«, jf. 4. F."""
)
@categorize(ValidationType.INDICES)
def validate_4c5b(ctx: ValidationContext) -> GenReport:
    yield standard_xml_schema_validate(ctx, ctx.indices / "tableIndex.xml")


# 4c5c NULL felter skal tillades i tableIndex.xml


@describe(
    """docIndex.xml skal danne forbindelsen mellem hvert dokument og dets placering.
»docIndex.xml« skal desuden indeholde oplysninger om dokumenternes oprindelige filnavne,
filtype i arkiveringsversionen samt eventuelle overordnede dokumenter.
»docIndex.xml« skal ikke indeholde oplysninger om dokumenterne i kontekstdokumentationen."""
)
@categorize((ValidationType.INDICES, ValidationType.DOCS))
def validate_4c6a(ctx: ValidationContext, indeces: XMLIndices) -> GenReport:
    @dataclass(frozen=True)
    class DocumentFile:
        docId: int
        ext: str
        _source: str

        def __hash__(self) -> int:
            return hash((self.docId, self.ext))

        def __eq__(self, value: object, /) -> bool:
            return self.__hash__() == value.__hash__()

    doc_file: list[DocumentFile] = []
    index_file: list[DocumentFile] = []

    directories = os.listdir(ctx.documents)
    for directory in directories:
        for docid in os.listdir(ctx.documents / directory):
            docid_id = int(docid)
            file_ext = os.listdir(ctx.documents / directory / docid)[0].split(".")[1]
            doc_file.append(
                DocumentFile(docId=int(docid_id), ext=file_ext, _source="dir")
            )

    doc_index = indeces.docIndex
    if doc_index is None:
        yield fail("No docindex!")
        return

    docs = doc_index["docIndex"]["doc"]
    for doc in docs:
        index_file.append(
            DocumentFile(docId=int(doc["dID"]), ext=doc["aFt"], _source="idx")
        )

    differences = set(doc_file) - set(index_file)

    for difference in differences:
        yield fail(f"File {difference} is missing its docIndex/doc file counterpart")


@describe(
    """For hvert enkelt dokument i docIndex.xml angives de oplysninger, som fremgår af figur 4.4."""
)
@categorize(ValidationType.INDICES)
def validate_4c6b(ctx: ValidationContext) -> GenReport:
    """
    docIndex.xml schema validering
    """
    table_index_path = ctx.indices / "docIndex.xml"
    xsd_path = ctx.schemas / "standard" / "docIndex.xsd"

    utils.lazy_xml_validate(table_index_path, xsd_path)

    yield ok()


@describe(
    """researchIndex.xml skal indeholde angivelse af hovedtabeller og koder for manglende værdier, jf. figur 4.5:"""
)
@categorize(ValidationType.INDICES)
def validate_4c7a(ctx: ValidationContext):
    xml_path = ctx.indices.joinpath("researchIndex.xml")
    if xml_path.exists():
        schemas_path = ctx.schemas / "standard" / "researchIndex.xsd"
        utils.lazy_xml_validate(xml_path, schemas_path)
