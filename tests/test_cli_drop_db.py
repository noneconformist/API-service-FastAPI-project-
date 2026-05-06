import os

import psycopg
import pytest
from dotenv import load_dotenv

import cli
from tests.utils.helpers_cli_db import connect_db

load_dotenv()

system_db = os.getenv('TEST_BASE_DB')
db_name = os.getenv('TEST_CLI_DB')


@pytest.mark.integration
def test_drop_database(tmp_path):
    # Run create DB
    cli.create(db_name)

    # Run command drop
    cli.drop(db_name)

    conn = connect_db(db_name=system_db)

    # Database no longer appears in \l (list databases)
    cur = conn.cursor()
    cur.execute('SELECT datname FROM pg_database WHERE datname = %s', (db_name,))
    assert cur.fetchone() is None
    conn.close()

    # Attempt to connect fails with “database does not exist.”
    with pytest.raises(psycopg.OperationalError):
        connect_db(db_name=db_name)


# Re‑creation of the database succeeds without conflicts
@pytest.mark.integration
def test_recreate_database(tmp_path):
    # Run command create
    cli.create(db_name)

    # Check to connect to new db
    conn = connect_db(db_name=db_name)

    cur = conn.cursor()
    cur.execute('SELECT 1;')
    assert cur.fetchone()[0] == 1
    conn.close()
