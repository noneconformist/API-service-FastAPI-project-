import os

import pytest
from dotenv import load_dotenv

import cli
from tests.utils.helpers_cli_db import connect_db

load_dotenv()
url_test_db = os.getenv('TEST_DB_URL')


@pytest.mark.integration
def test_check_database():
    # Run the command "check"
    cli.check()

    # Get parameters from DATABASE_URL
    conn = connect_db(url=url_test_db)

    # Check database connection
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1;')
        assert cur.fetchone()[0] == 1
    finally:
        conn.close()
