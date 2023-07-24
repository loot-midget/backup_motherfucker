import datetime
import logging
from typing import List

from watchdog.observers import Observer

from app.config import read_config
from app.file_backup import FileBackupHandler, BackupManager, BackupOptions
from app.utils import init_logging

logger = logging.getLogger(__name__)


def monitor_and_backup_files(args: List[str]) -> None:
    config = read_config(args)
    init_logging()

    logger.info('start watching directory for updates: %r', config.folder_to_monitor)
    logger.info('file copies will be put under %r', config.backup_folder)

    backup_options = BackupOptions(
        min_update_interval_sec=10,
        backup_depth_days=7,
        cleanup_period_sec=int(datetime.timedelta(hours=8).total_seconds()),
    )

    backup_manager = BackupManager(
        folder_to_monitor=config.folder_to_monitor,
        backup_folder=config.backup_folder,
        backup_options=backup_options,
        basename_filter=config.basename_filter,
    )
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
