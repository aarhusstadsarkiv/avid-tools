import os
import traceback
from pathlib import Path

import click
import xmlschema
from click import group
from click import option
from xmlschema.resources.xml_resource import XMLResource
from xmlschema.validators.exceptions import XMLSchemaValidationError

from avid_validator import command


def _validate_file(xml_path: Path, xsd_path: Path) -> XMLSchemaValidationError | None:
    index_schema = xmlschema.XMLSchema(xsd_path)

    try:
        xml_resource = XMLResource(source=xml_path, lazy=True)
        index_schema.validate(xml_resource)
    except XMLSchemaValidationError as e:
        print(traceback.format_exc())
        return e


def _validate_indices(path: Path):
    path_files = os.listdir(path)
    indices_files = list((path / "Indices").glob("*.xml"))

    assert "Indices" in path_files and "Schemas" in path_files, "Both Indices and Schemas must be present in the given path!"
    assert len(indices_files) != 0, "No index files found!"

    for index_path in indices_files:
        schema_path = path / "Schemas" / "standard" / f"{index_path.stem}.xsd"

        if error := _validate_file(index_path, schema_path):
            print("Failed to validate indices:", error.reason)
    print("Done!")


@group("validate")
def grp_validate():
    """
    Validate AVID indices
    """


@grp_validate.command("indices")
@option("--path", default=Path.cwd(), type=click.Path(file_okay=False, dir_okay=True, path_type=Path))  # pyright: ignore
def cmd_validate_indices(path: Path):
    """
    Validate Indices against XSD schemas
    """
    _validate_indices(path)


@grp_validate.command("file")
@option("--xml-path", required=True, type=click.Path(file_okay=True, dir_okay=False, path_type=Path))  # pyright: ignore
@option("--xsd-path", required=True, type=click.Path(file_okay=True, dir_okay=False, path_type=Path))  # pyright: ignore
def cmd_validate_file(xml_path: Path, xsd_path: Path):
    """
    Validate XML file against XSD file
    """
    if error := _validate_file(xml_path, xsd_path):
        print("Error:", error.reason)
        print("Error:", traceback.format_exc())
    else:
        print("Is valid!")

grp_validate.add_command(command.cmd_validate_all, "all")
