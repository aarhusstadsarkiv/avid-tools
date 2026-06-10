import sqlite3
from pathlib import Path
from typing import Optional


class FileHandler:
    """
    Context manager to manage files
    """

    conn: sqlite3.Connection
    db_filename = "validation.db"

    def _setup(self):
        cursor = self.conn.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS files(
                           path TEXT PRIMARY KEY,
                           mdate TEXT
                           )
                       """)

    def __enter__(self) -> "FileHandler":
        self.conn = sqlite3.connect(self.db_filename)
        self._setup()
        return self

    def _db_file_mdate(self, file: Path) -> Optional[str]:
        """
        Get recorded modification date for file
        """
        row = self.conn.execute("SELECT mdate FROM files WHERE path = ?", (str(file),)).fetchone()

        if row is None:
            return None

        return row[0]

    def is_modified(self, file: Path) -> bool:
        """
        Checks if file has been modified
        """
        mdate = str(file.stat().st_mtime)

        stored_mdate: Optional[str] = self._db_file_mdate(file)

        if stored_mdate is None:
            return True

        # unchanged
        if stored_mdate == mdate:
            return False

        return True

    def mark_clean(self, file: Path):
        """
        Record the file's current mtime so it is no longer considered modified
        """
        mdate = str(file.stat().st_mtime)
        self.conn.execute(
            """
            INSERT INTO files(path, mdate)
            VALUES (?, ?)
            ON CONFLICT(path) DO UPDATE SET mdate = excluded.mdate
        """,
            (str(file), mdate),
        )

    def commit(self) -> None:
        self.conn.commit()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()
