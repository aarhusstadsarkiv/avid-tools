import logging
import sys

from click import group
from click import version_option

from avid_tools.commands.context.context import grp_context
from avid_tools.commands.documents import grp_documents
from avid_tools.commands.finalize import cmd_finalize
from avid_tools.commands.index import grp_index
from avid_tools.commands.init import cmd_init
from avid_tools.commands.sample import grp_sample
from avid_tools.commands.search import cmd_search
from avid_tools.commands.tables.tables import grp_tables
from avid_tools.commands.validate import grp_validate
from avid_tools.commands.encode import grp_encoding
from avid_tools.utils import option_help


logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


@group("avid-tools", no_args_is_help=True, add_help_option=False)
@version_option()
@option_help()
def app():
    """
    Arbejd med arkiveringsversioner.
    """


app.add_command(cmd_init, cmd_init.name)
app.add_command(grp_context, grp_context.name)
app.add_command(grp_tables, grp_tables.name)
app.add_command(grp_index, grp_index.name)
app.add_command(grp_documents, grp_documents.name)
app.add_command(grp_sample, grp_sample.name)
app.add_command(cmd_search, cmd_search.name)
app.add_command(cmd_finalize, cmd_finalize.name)
app.add_command(grp_validate, grp_validate.name)
app.add_command(grp_encoding, grp_encoding.name)

app.list_commands = lambda _ctx: list(app.commands)
