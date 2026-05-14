import os
import sys
from enum import Enum
from logging import WARNING, Handler, basicConfig, getLogger

from loguru import logger


class Env(str, Enum):
    LOCAL = 'local'
    DEV = 'dev'
    PROD = 'prod'


ENV: Env = Env(os.getenv('ENV', 'local').lower())


# Loguru settings: maximum 10 files, each up to 1 MB
logger.add(
    'logs/app.log',
    rotation='1 MB',  # rotation upon reaching 1 MB
    retention=10,  # store only 10 файлов
)


# Intercepting standard logging
class InterceptHandler(Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())


basicConfig(handlers=[InterceptHandler()], level=0)


def setup_logging(env: str):
    # Removing old handlers
    logger.remove()

    if env == 'local':
        level = 'INFO'
        # Console output
        logger.add(
            sys.stdout,
            level=level,
            colorize=True,
            format='<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}',
        )

    if env == 'dev':

        def db_filter(record):
            if record['name'].startswith('sqlalchemy'):
                return record['level'].no >= WARNING
            return True

        level = 'INFO'
        logger.add(sys.stdout, level=level, filter=db_filter, format='{time} | {level} | {message}')
