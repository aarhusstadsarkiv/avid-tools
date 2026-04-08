from avid_tools.commands.tables.search import cmd_search_tables
from click import group

from avid_tools.commands.tables.row_count import cmd_update_row_count
from avid_tools.commands.tables.trim import cmd_trim
from avid_tools.commands.tables.load import cmd_load_table
from avid_tools.utils import option_help


@group("tables", no_args_is_help=True, add_help_option=False)
@option_help()
def grp_tables():
    """Arbejd med tabellerne."""


grp_tables.add_command(cmd_trim, cmd_trim.name)
grp_tables.add_command(cmd_update_row_count, cmd_update_row_count.name)
grp_tables.add_command(cmd_load_table, cmd_load_table.name)
grp_tables.add_command(cmd_search_tables, cmd_search_tables.name)
