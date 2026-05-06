import asyncio
from typing import Optional

import typer
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.elements import quoted_name

from database import DATABASE_URL

app = typer.Typer(help='Database management commands')


# helper for administrative operations (create/drop database)
def get_db_url(db_name: Optional[str] = None) -> str:
    url = make_url(DATABASE_URL)
    if db_name:
        url = url.set(database=db_name)
    return url.render_as_string(hide_password=False)


@app.command()
def create(db_name) -> None:
    target_db = db_name or 'postgres'
    safe_db_name = quoted_name(target_db, quote=True)

    async def _create():
        url = get_db_url(safe_db_name)
        base_url = url.rsplit('/', 1)[0] + '/template1'
        engine = create_async_engine(base_url, isolation_level='AUTOCOMMIT')

        async with engine.connect() as conn:
            await conn.execute(text(f'DROP DATABASE IF EXISTS "{safe_db_name}"'))
            await conn.execute(text(f'CREATE DATABASE "{safe_db_name}"'))
        typer.echo(f'Database created (recreated if existed): {url}')

    try:
        asyncio.run(_create())
    except Exception as e:
        typer.echo(f'Error dropping database: {e}')
        raise typer.Exit(1)


@app.command()
def migrate() -> None:
    alembic_cfg = Config('alembic.ini')
    typer.echo('Launch alembic upgrade head ...')
    command.upgrade(alembic_cfg, 'head')
    typer.echo('Migrations have been successfully applied')


@app.command()
def check() -> None:
    async def _check():
        engine = create_async_engine(DATABASE_URL)

        async with engine.connect() as connection:
            result = await connection.execute(text('SELECT 1'))
            value = result.scalar()
            typer.echo(f'Async connection successful: SELECT 1 → {value}')
        await engine.dispose()

    try:
        asyncio.run(_check())
    except Exception as e:
        typer.echo(f'Connection error: {e}')
        raise typer.Exit(1)

    typer.echo('The async connection is stable.')


@app.command()
def drop(db_name: Optional[str] = None) -> None:
    target_db = db_name or 'postgres'
    safe_db_name = quoted_name(target_db, quote=True)

    async def _drop():
        url = get_db_url(safe_db_name)

        base_url = url.rsplit('/', 1)[0] + '/template1'
        engine = create_async_engine(base_url, isolation_level='AUTOCOMMIT')

        async with engine.connect() as conn:
            # проверяем наличие базы
            result = await conn.execute(
                text('SELECT 1 FROM pg_database WHERE datname=:name'),
                {'name': target_db},
            )
            exists = result.scalar() is not None

            if exists:
                await conn.execute(text(f'DROP DATABASE "{safe_db_name}"'))
                typer.echo(f'Database dropped: {url}')
            else:
                typer.echo(f'Database {safe_db_name or "default"} does not exist.')

    try:
        asyncio.run(_drop())
    except Exception as e:
        typer.echo(f'Error dropping database: {e}')
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
