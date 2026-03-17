from dataclasses import dataclass


@dataclass
class TableNode:
    name: str
    primarykeys: list[str]
    referenced_tables: list[str]
    referenced_columns: list[str]
