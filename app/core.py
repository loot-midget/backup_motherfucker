import logging
from typing import List

from watchdog.observers import Observer

from app.config import read_config
from app.file_backup import FileBackupHandler, BackupManager
from app.utils import init_logging

logger = logging.getLogger(__name__)


def monitor_and_backup_files(args: List[str]) -> None:
    config = read_config(args)
    init_logging()

    logger.info('start watching directory for updates: %r', config.folder_to_monitor)
    logger.info('file copies will be put under %r', config.backup_folder)

    backup_manager = BackupManager(config)
    backup_manager.backup_all_files()

    event_handler = FileBackupHandler(backup_manager)
    observer = Observer()
    observer.schedule(event_handler, config.folder_to_monitor, recursive=False)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()

    logger.info('Stop.')
