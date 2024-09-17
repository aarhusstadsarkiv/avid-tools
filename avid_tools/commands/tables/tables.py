from click import group

from avid_tools.commands.tables.row_count import cmd_update_row_count
from avid_tools.commands.tables.trim import cmd_trim


@group("tables", no_args_is_help=True)
def grp_tables():
    """Arbejd med tabellerne."""


grp_tables.add_command(cmd_trim, cmd_trim.name)
grp_tables.add_command(cmd_update_row_count, cmd_update_row_count.name)
