from pathlib import Path
from sqlite3 import Connection

from avid_tools.database import insert_file
from avid_tools.utils import AVID


def _get_property_paths_from(class_properties: object) -> list[Path]:
    return [
        getattr(class_properties, name)
        for name, value in type(class_properties).__dict__.items()
        if isinstance(value, property) and isinstance(getattr(class_properties, name), Path)
    ]


def save_all_archive_paths(conn: Connection, avid: AVID):
    """
    Find all file paths in an archive
    """
    tables = list(avid.tables.values())
    tables_xsd = list(avid.tables_xsd.values())
    documents = avid.documents
    context_documents = avid.context_documents
    indices = list(filter(lambda x: x.name == "fileIndex.xml", _get_property_paths_from(avid.indices)))
    schemas = _get_property_paths_from(avid.schemas)

    paths = tables + tables_xsd + documents + context_documents + indices + schemas

    for file_path in paths:
        print("File path")
        print(file_path)
        relative_file_path = file_path.relative_to(avid.dir)
        insert_file(conn=conn, avid_dir=avid.dir, file_path=relative_file_path)

    conn.commit()
