def validate_tables_xsd() -> list[str]: ...

def encode_database(
    db_path: str,
    ignore_tables: list[str] | None,
    ignore_columns: list[str] | None,
    ignore_table_regexes: list[str] | None,
    ignore_column_regexes: list[str] | None,
    ): ...

def search_database(
    db_path: str,
    search_text: str,
    ignore_tables: list[str] | None,
    ignore_columns: list[str] | None,
    ignore_table_regexes: list[str] | None,
    ignore_column_regexes: list[str] | None,
    ): ...

def contains_database(
    search_text: str,
    ignore_tables: list[str] | None,
    ignore_columns: list[str] | None,
    ignore_table_regexes: list[str] | None,
    ignore_column_regexes: list[str] | None,
    ): ...
