import os

import pytest
from dotenv import load_dotenv

import cli
from tests.utils.helpers_cli_db import connect_db

load_dotenv()
db_name = os.getenv('TEST_CLI_DB')


@pytest.mark.integration
def test_create_database(tmp_path):
    # Run command create
    cli.create(db_name)

    # Check to connect to new db
    conn = connect_db(db_name=db_name)

    cur = conn.cursor()
    cur.execute('SELECT 1;')
    assert cur.fetchone()[0] == 1
    conn.close()
