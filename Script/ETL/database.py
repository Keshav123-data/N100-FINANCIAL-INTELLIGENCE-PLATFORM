import sqlite3
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH")

SCHEMA_PATH = Path("db/schema.sql")


def create_database():

    print("Creating SQLite Database...")

    connection = sqlite3.connect(DB_PATH)

    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as file:

        schema = file.read()

    cursor.executescript(schema)

    connection.commit()

    connection.close()

    print("Database Created Successfully")


if __name__ == "__main__":

    create_database()