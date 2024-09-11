from dataclasses import dataclass
from pathlib import Path

from xmltodict import parse as parse_xml


@dataclass
class Column:
    name: str
    type: str
    min_occurs: int | None = None
    nullable: bool = False


def read_table_schema(schema_xsd: Path) -> list[Column]:
    columns: list[Column] = []
    schema = parse_xml(schema_xsd.read_text(), force_list=True)

    return [
        Column(
            col["@name"],
            col["@type"],
            int(min_occurs) if (min_occurs := col.get("@minOccurs")) is not None else None,
            col.get("@nillable") == "true",
        )
        for col in schema["xs:schema"][0]["xs:complexType"][0]["xs:sequence"][0]["xs:element"]
    ]
