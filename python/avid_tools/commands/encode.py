import click
from avid_tools.encoding import rowwise, bloom


@click.group("encoding")
def grp_encoding():
    """
    Encode database or perform actions on encoded database
    """


grp_encoding.add_command(rowwise.grp_rowwise)
grp_encoding.add_command(bloom.grp_bloom_filter)
