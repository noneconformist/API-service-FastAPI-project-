import os

import psycopg
from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url

load_dotenv()
test_user = os.getenv('TEST_USER')
test_pass = os.getenv('TEST_PASS')
test_host = os.getenv('TEST_HOST')
test_port = os.getenv('TEST_PORT')


# A universal PostgreSQL connection function for CLI tests
def connect_db(
    db_name=None, url=None, user=test_user, password=test_pass, host=test_host, port=test_port
):
    """Can pass either db_name or sqlalchemy.url"""
    if url:
        parsed = make_url(url)
        return psycopg.connect(
            dbname=parsed.database,
            user=parsed.username,
            password=parsed.password,
            host=parsed.host,
            port=parsed.port,
        )
    elif db_name:
        return psycopg.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port,
        )
    else:
        raise ValueError('Must specify either db_name or url')
