from click import group
from click import version_option

from .__version__ import __version__
from .commands.context.context import grp_context
from .commands.documents import grp_documents
from .commands.finalize import cmd_finalize
from .commands.index import grp_index
from .commands.init import cmd_init
from .commands.sample import grp_sample
from .commands.search import cmd_search
from .commands.tables.tables import grp_tables


@group("avid-tools", no_args_is_help=True)
@version_option(__version__)
def app(): ...


app.add_command(cmd_init, cmd_init.name)
app.add_command(grp_context, grp_context.name)
app.add_command(grp_tables, grp_tables.name)
app.add_command(grp_index, grp_index.name)
app.add_command(grp_documents, grp_documents.name)
app.add_command(grp_sample, grp_sample.name)
app.add_command(cmd_search, cmd_search.name)
app.add_command(cmd_finalize, cmd_finalize.name)

app.list_commands = lambda _ctx: list(app.commands)
