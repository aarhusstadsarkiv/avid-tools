def validate_tables_xsd() -> list[str]: ...

def encode_database(
    db_path: str,
    ignore_tables: list[str] | None,
    ignore_columns: list[str] | None,
    ignore_table_regexes: list[str] | None,
    ignore_column_regexes: list[str] | None,
    ):
    """
    Encode an SQLite database in Bloom filter (bloom.bin)

    Args:
        db_path: Path to SQLite database file to encode
        ignore_tables: List of table names to ignore
        ignore_columns: List of column names to ignore
        ignore_table_regexes: List of regex strings to ignore tables by name
        ignore_column_regexes: List of regex strings to ignore columns by name
    """

def search_database(
    db_path: str,
    search_text: str,
    ignore_tables: list[str] | None,
    ignore_columns: list[str] | None,
    ignore_table_regexes: list[str] | None,
    ignore_column_regexes: list[str] | None,
    ):
    """
    Search a database file encoded into a Bloom filter (bloom.bin)

    Args:
        db_path: Path to SQLite database file to search
        ignore_tables: List of table names to ignore
        ignore_columns: List of column names to ignore
        ignore_table_regexes: List of regex strings to ignore tables by name
        ignore_column_regexes: List of regex strings to ignore columns by name
    """

def contains_database(
    search_text: str,
    ignore_tables: list[str] | None,
    ignore_columns: list[str] | None,
    ignore_table_regexes: list[str] | None,
    ignore_column_regexes: list[str] | None,
    ):
    """
    Test if text is contained in Bloom filter (bloom.bin)

    Args:
        db_path: Path to SQLite database file to search
        ignore_tables: List of table names to ignore
        ignore_columns: List of column names to ignore
        ignore_table_regexes: List of regex strings to ignore tables by name
        ignore_column_regexes: List of regex strings to ignore columns by name
    """
