"""
This file interfaces Rust implmented Bloom filters.
"""


import click
from avid_tools import whitespacevalidate


def _ignore_args(func):
    options = [
        click.option("--ignore_tables", type=str, multiple=True, default=[], help="Name(s) of tables to ignore"),
        click.option("--ignore_columns", type=str, multiple=True, default=[], help="Name(s) of columns to ignore"),
        click.option("--ignore_table_regexes", type=str, multiple=True, default=[], help="Regex(es) of tables to ignore"),
        click.option("--ignore_column_regexes", type=str, multiple=True, default=[], help="Regex(es) of columns to ignore")
    ]

    for option in reversed(options):
        option(func)

    return func


@click.group("bloom")
def grp_bloom_filter():
    """
    Encode and search a database using Bloom filters

    Bloom filters is a space-efficient probabilistic data structure used to test whether
    an element is a member of a set. It can return false positives, but never false negatives.
    """


@grp_bloom_filter.command("encode")
@click.argument("db_path", type=click.Path(exists=True, dir_okay=False))
@_ignore_args
def cmd_encode(db_path: str, ignore_tables: list[str], ignore_columns: list[str], ignore_table_regexes: list[str], ignore_column_regexes: list[str]):
    """
    Encode an SQLite database in bloom filters
    """
    whitespacevalidate.encode_database(db_path, ignore_tables, ignore_columns, ignore_table_regexes, ignore_column_regexes)


@grp_bloom_filter.command("search")
@click.argument("db_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("text", type=str)
@_ignore_args
def cmd_search(db_path: str, text: str, ignore_tables: list[str], ignore_columns: list[str], ignore_table_regexes: list[str], ignore_column_regexes: list[str]):
    """
    Search an SQLite database encoded in bloom filters
    """
    whitespacevalidate.search_database(db_path, text, ignore_tables, ignore_columns, ignore_table_regexes, ignore_column_regexes)


@grp_bloom_filter.command("contains")
@click.argument("text", type=str)
@_ignore_args
def cmd_contains(text: str, ignore_tables: list[str], ignore_columns: list[str], ignore_table_regexes: list[str], ignore_column_regexes: list[str]):
    """
    Test if text string may be contained in an SQLite database encoded in bloom filters
    """
    whitespacevalidate.contains_database(text, ignore_tables, ignore_columns, ignore_table_regexes, ignore_column_regexes)
