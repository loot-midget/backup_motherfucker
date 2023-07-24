import logging
import os
import sys
from typing import Callable

logger = logging.getLogger(__name__)

MIN_PYTHON = (3, 8)


BasenameFilter = Callable[[str], bool]


def python_version_check() -> None:
    if sys.version_info < MIN_PYTHON:
        sys.exit(
            f'ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher is required to run this utility'
            + f' but you use {sys.version_info[0]}.{sys.version_info[1]}'
        )


def init_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def remove_file(filepath: str) -> None:
    if not os.path.exists(filepath):
        return
    try:
        os.unlink(filepath)
    except OSError as exc:
        logger.error('unable to remove file: its a directory: %r -- %s', filepath, exc)
    except Exception as exc:
        logger.error('unable to remove file %r -- %s', filepath, exc)


def get_user_home_dir() -> str:
    if sys.platform == 'win32':
        return os.path.expandvars('%USERPROFILE%')
    else:
        return os.path.expanduser('~')


def norm_path(path: str) -> str:
    return os.path.abspath(path)


def is_windows() -> bool:
    return sys.platform == 'win32'


def backup_all_files(_basename: str) -> bool:
    return True
