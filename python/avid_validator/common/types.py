"""
This file defines the allowed data types for tableIndex and table schema files,
enabling validation of both.
"""

from dataclasses import dataclass
import re


STRIP_NONASCII_RE = re.compile("[^a-zA-Z ]+")


def _strip_nonascii(text: str) -> str:
    return STRIP_NONASCII_RE.sub("", text)


@dataclass()
class AllowedTableTypes:
    sql_types: list[str]
    xml_datatype: list[str]

    def allowed(self, xml_type: str) -> bool:
        return xml_type.lower() in self.xml_datatype


@dataclass()
class AllowedTableTypesBundle:
    types: list[AllowedTableTypes]

    def match(self, sql_type: str) -> AllowedTableTypes | None:
        for att_type in self.types:
            # Risky to use _strip_nonascii here. Believe it should only replace (\d+) if its exists
            if _strip_nonascii(sql_type.lower()) in att_type.sql_types:
                return att_type


def get_allowed_table_types() -> AllowedTableTypesBundle:
    allowed_types: list[AllowedTableTypes] = []

    # Text and hexadecimal - Der er en fejl i vejledningen, ingen komma mellem nchar og national character varying...
    allowed_types.append(
        AllowedTableTypes(
            sql_types=[
                "character",
                "char",
                "character varying",
                "char varying",
                "varchar",
                "national character",
                "national char",
                "nchar",
                "national character varying",
                "national char varying",
                "nchar varying",
            ],
            xml_datatype=["string", "hexbinary"],
        )
    )

    # whole numbers
    allowed_types.append(AllowedTableTypes(sql_types=["integer", "int", "smallint"], xml_datatype=["integer"]))

    # decimal numbers
    allowed_types.append(AllowedTableTypes(sql_types=["numeric", "decimal", "dec"], xml_datatype=["decimal"]))

    # float
    allowed_types.append(AllowedTableTypes(sql_types=["float"], xml_datatype=["float"]))

    # real, double precision
    allowed_types.append(AllowedTableTypes(sql_types=["real", "double precision"], xml_datatype=["double"]))

    # boolean
    allowed_types.append(AllowedTableTypes(sql_types=["boolean"], xml_datatype=["boolean"]))

    # date
    allowed_types.append(AllowedTableTypes(sql_types=["date"], xml_datatype=["date"]))

    # time
    allowed_types.append(
        AllowedTableTypes(
            sql_types=["time"],  # TIME[WITH TIME ZONE]
            xml_datatype=["datetime"],
        )
    )

    # timestamp
    allowed_types.append(
        AllowedTableTypes(
            sql_types=["timestamp"],  # TIME[WITH TIME ZONE]
            xml_datatype=["datetime"],
        )
    )

    # timeperiod
    allowed_types.append(
        AllowedTableTypes(
            sql_types=["interval"],  # TIME[WITH TIME ZONE]
            xml_datatype=["duration"],
        )
    )

    return AllowedTableTypesBundle(types=allowed_types)
