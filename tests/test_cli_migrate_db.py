import os

import pytest
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

import cli
from tests.utils.helpers_cli_db import connect_db

load_dotenv()
db_name = os.getenv('TEST_CLI_DB')


@pytest.mark.integration
def test_migrate(tmp_path):
    # Run command create
    cli.create(db_name)

    # Run migrate
    alembic_cfg = Config('alembic.ini')
    alembic_cfg.set_main_option(
        'sqlalchemy.url', f'postgresql+psycopg://docker_user:docker_password@db:5432/{db_name}'
    )
    command.upgrade(alembic_cfg, 'head')

    # Check migrate
    conn = connect_db(db_name=db_name)

    cur = conn.cursor()

    # Check alembic
    cur.execute('SELECT version_num FROM alembic_version;')
    version = cur.fetchone()[0]
    assert version is not None

    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    tables = [row[0] for row in cur.fetchall()]
    assert 'users' in tables

    cur.execute(
        'INSERT INTO users (email, password) VALUES (%s, %s) RETURNING id;',
        ('anton@foxminded.com', 'Strongpass123!'),
    )
    user_id = cur.fetchone()[0]
    conn.commit()

    cur.execute('SELECT email FROM users WHERE id = %s;', (user_id,))
    assert cur.fetchone()[0] == 'anton@foxminded.com'
    conn.close()
