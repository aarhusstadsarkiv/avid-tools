from click import group

from avid_tools.commands.tables.trim import cmd_trim


@group("tables", no_args_is_help=True)
def grp_tables(): ...


grp_tables.add_command(cmd_trim, cmd_trim.name)
