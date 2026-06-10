import csv
import os
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import click
import xmltodict
from avid_tools.exceptions import TableLoadExtensionNotRecognized
from avid_tools.utils import AVID
from avid_tools.utils import find_avid_dir


@dataclass()
class Table:
    name: str
    columns: list[str]
    table_id: int


def _default_type_input(msg):
    inptype = input(msg + "(default=VARCHAR): ")
    return inptype if len(inptype) != 0 else "VARCHAR"


def tableIndex_add(table: Table, *, avid: AVID):
    table_idx_path = avid.indices.tableIndex
    tableIndexText = table_idx_path.read_text(encoding="utf8")

    dobj = xmltodict.parse(tableIndexText)

    print(f"Adding table, {table}, to tableIndex")
    table_desc = input("Table description: ")
    tables: list[dict] = dobj["siardDiark"]["tables"]["table"]

    table_obj = {
        "name": table.name,
        "folder": f"table{table.table_id}",
        "description": table_desc,
        "columns": {
            "column": [
                {
                    "name": col,
                    "columnID": f"c{cid + 1}",
                    "type": _default_type_input(f"Type for {col}"),
                    "nullable": str(_prompt(f"Is {col} nullable?")).lower(),
                }
                for cid, col in enumerate(table.columns)
            ]
        },
    }
    shutil.copy(table_idx_path, table_idx_path.parent.joinpath("backup_tableIndex.xml"))
    tables.append(table_obj)

    with open(table_idx_path, "w") as f:
        xmltodict.unparse(dobj, f, pretty=True)


def docs_add(table: Table, *, avid: AVID, conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute(f"select * from {table.name}")
    rows = cursor.fetchall()

    table_name = f"table{table.table_id}"
    table_path = avid.dir.joinpath("Tables").joinpath(table_name)
    table_path.mkdir()

    # Write XML file
    with open(table_path.joinpath(table_name + ".xml"), "w") as f:
        first_lines = [
            """<?xml version="1.0" encoding="utf-8"?>\n""",
            f"""<table xsi:schemaLocation="http://www.sa.dk/xmlns/siard/1.0/schema0/{table_name}.xsd {table_name}.xsd" xmlns="http://www.sa.dk/xmlns/siard/1.0/schema0/{table_name}.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n""",
        ]
        f.writelines(first_lines)
        for row in rows:
            f.write("   <row>\n")

            for cidx, c in enumerate(row):
                f.write(f"      <c{cidx}>{c}</{cidx}>\n")

            f.write("   </row>\n")
        f.write("</table>")

    # Write XSD file
    with open(table_path.joinpath(table_name + ".xsd"), "w") as f:
        f.write(f"""<?xml version="1.0" encoding="utf-8"?>
<xs:schema xmlns="http://www.sa.dk/xmlns/siard/1.0/schema0/table3.xsd" attributeFormDefault="unqualified" elementFormDefault="qualified" targetNamespace="http://www.sa.dk/xmlns/siard/1.0/schema0/table3.xsd" xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="table">
    <xs:complexType>
      <xs:sequence>
        <xs:element minOccurs="0" maxOccurs="unbounded" name="row" type="rowType" />
      </xs:sequence>
    </xs:complexType>
  </xs:element>
  <xs:complexType name="rowType">
    <xs:sequence>
{"".join(f'      <xs:element minOccurs="1" name="c{cidx + 1}" nillable="false" type="xs:string" />\n' for cidx in range(len(table.columns)))}
    </xs:sequence>
  </xs:complexType>
</xs:schema>
""")


def _prompt(msg: str = "") -> bool:
    print(msg)
    while True:
        yn = input("Y/n?").lower()
        if yn != "y" and yn != "n" and yn != "":
            continue

        return yn == "y" or yn == ""


def _db_load(csv_file: Path, *, conn: sqlite3.Connection, avid: AVID) -> Table | None:
    cursor = conn.cursor()

    with open(csv_file, newline="") as file:
        reader = csv.reader(file)
        header = next(reader)

        print("Are these column names correct? ", header)
        can_continue = _prompt()
        if not can_continue:
            return None

        print("Enter table name")
        table_name = input("Name: ")

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(header)}
        )
        """)

        insert_str = f"INSERT INTO {table_name} VALUES ({', '.join('?' * len(header))})"
        for row in reader:
            cursor.execute(insert_str, row)

    conn.commit()

    table_id = int(sorted(os.listdir(avid.dir.joinpath("Tables")))[-1].removeprefix("table")) + 1

    return Table(name=table_name, columns=header, table_id=table_id)


@click.command("load", no_args_is_help=True, help="Load table into DB from CSV file")
@click.option("--load-file", "file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))  # pyright: ignore
@click.option("--db-file", "db", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))  # pyright: ignore
def cmd_load_table(file: Path, db: Path):
    """
    Load table into DB from CSV file
    """
    avid = AVID(find_avid_dir(Path.cwd()))
    with sqlite3.connect(db) as conn:
        match file.suffix:
            case ".csv":
                table = _db_load(file, conn=conn, avid=avid)
            case _:
                raise TableLoadExtensionNotRecognized(f"Not recognized: {db.suffix}")

    if table is None:
        return

    tableIndex_add(table, avid=avid)
    docs_add(table, avid=avid, conn=conn)
