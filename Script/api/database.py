"""
SQLite database utilities for the N100 API.
"""

import sqlite3

from Script.api.config import DATABASE_PATH


def get_db_connection():
    """
    Create and return a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection