import os
import sys
from enum import Enum
from logging import ERROR, WARNING, Handler, basicConfig, getLogger

from loguru import logger


class Env(str, Enum):
    LOCAL = 'local'
    DEV = 'dev'
    PROD = 'prod'


ENV: Env = Env(os.getenv('ENV', 'local').lower())


# Intercepting standard logging
class InterceptHandler(Handler):
    def emit(self, record):
        # DEV: suppress SQLAlchemy below WARNING
        if ENV == Env.DEV and record.name.startswith('sqlalchemy') and record.levelno < WARNING:
            return

        # PROD: show only ERROR
        if ENV == Env.PROD and record.levelno < ERROR:
            return

        # LOCAL: don't filter anything
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


def setup_logging(env: str):
    # Removing old handlers
    logger.remove()

    os.makedirs('logs', exist_ok=True)

    # Loguru settings: maximum 10 files, each up to 1 MB
    logger.add(
        'logs/app.log',
        rotation='1 MB',  # rotation upon reaching 1 MB
        retention=10,  # store only 10 файлов
        level='INFO',
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Intercepting standard logging → loguru
    basicConfig(handlers=[InterceptHandler()], level=0)

    # Clearing default handlers for the root logger
    getLogger().handlers = []

    # Console output depending on the environment
    if env == 'local':
        # Console output
        logger.add(
            sys.stdout,
            level='INFO',
            colorize=True,
            format='<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}',
        )

    elif env == 'dev':
        # SQLAlchemy: turn off INFO
        sa_logger = getLogger('sqlalchemy')
        sa_logger.setLevel(WARNING)
        sa_logger.propagate = False

        # Uvicorn: request logs
        getLogger('uvicorn').handlers = [InterceptHandler()]
        getLogger('uvicorn.error').handlers = [InterceptHandler()]
        getLogger('uvicorn.access').handlers = [InterceptHandler()]

        logger.add(
            sys.stdout,
            level='INFO',
            format='{time} | {level} | {message}',
        )

    elif env == 'prod':
        getLogger('uvicorn.access').setLevel(ERROR)
        logger.add(sys.stdout, level='ERROR', format='{time} | {level} | {message}')
