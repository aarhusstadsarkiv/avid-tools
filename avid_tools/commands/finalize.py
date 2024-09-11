from pathlib import Path

from click import command

from avid_tools.database import create_database
from avid_tools.database import update_md5
from avid_tools.indices import generate_doc_index
from avid_tools.indices import generate_file_index
from avid_tools.utils import argument_avid_dir
from avid_tools.utils import AVID


@command("finalize", no_args_is_help=True)
@argument_avid_dir(True)
def cmd_finalize(avid_dir: Path):
    db_path: Path = avid_dir.joinpath("_metadata", "avid.db")
    conn = create_database(db_path)
    avid = AVID(avid_dir)
    generate_doc_index(conn, avid)
    update_md5(conn, avid.indices.docIndex)
    generate_file_index(conn, avid)
