import dataclasses
import datetime
import logging
import os
import re
import shutil
import time
from typing import Dict, Final, Optional, List

from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.utils import remove_file, BasenameFilter

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class BackupOptions:
    min_update_interval_sec: int
    backup_depth_days: int
    cleanup_period_sec: int


@dataclasses.dataclass(frozen=True)
class FileInfo:
    basename: str
    file_path: str
    file_backup_folder: str
    last_copy_time: float
    last_cleanup_time: float

    def touch_last_update_time(self) -> 'FileInfo':
        return FileInfo(
            basename=self.basename,
            file_path=self.file_path,
            file_backup_folder=self.file_backup_folder,
            last_copy_time=time.time(),
            last_cleanup_time=self.last_cleanup_time,
        )

    def touch_last_cleanup_time(self) -> 'FileInfo':
        return FileInfo(
            basename=self.basename,
            file_path=self.file_path,
            file_backup_folder=self.file_backup_folder,
            last_copy_time=self.last_copy_time,
            last_cleanup_time=time.time(),
        )


def create_backup_extension() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d--%H-%M-%S')


EXT_DATE_RE = re.compile(r'^(\d\d\d\d-\d\d-\d\d)--\d\d-\d\d-\d\d$')


def extract_day_from_extension(ext: str) -> Optional[str]:
    match = EXT_DATE_RE.match(ext.lstrip('.'))
    if match is None:
        return None
    return match.group(1)


def cleanup_old_versions(*, job: FileInfo, backup_options: BackupOptions) -> FileInfo:
    next_cleanup_time = job.last_cleanup_time + backup_options.cleanup_period_sec
    overtime = time.time() - next_cleanup_time
    if overtime < 0:
        return job

    if not os.path.isdir(job.file_backup_folder):
        logger.error('%r: cleanup error: directory is missing: %r', job.basename, job.file_backup_folder)
        return job

    files: List[str] = next(os.walk(job.file_backup_folder))[2]

    # (yyyy-mm-dd, filename)
    common_prefix = job.basename + '.'
    day_to_files: Dict[str, List[str]] = {}
    for filename in files:
        if not filename.startswith(common_prefix):
            continue
        extension = filename[len(common_prefix) :]
        ymd = extract_day_from_extension(extension)
        if ymd is None:
            continue
        day_to_files.setdefault(ymd, list()).append(filename)
    keys = list(day_to_files.keys())
    if len(keys) <= backup_options.backup_depth_days:
        return job
    keys.sort(reverse=True)
    for _ in range(backup_options.backup_depth_days):
        key = keys.pop(0)
        day_to_files.pop(key, None)

    # remove files by list
    for files in day_to_files.values():
        for f in files:
            remove_file(os.path.join(job.file_backup_folder, f))

    return job.touch_last_cleanup_time()


def backup_one_file(*, job: FileInfo, backup_options: BackupOptions) -> FileInfo:
    # backup if some interval since last update
    next_update_time = job.last_copy_time + backup_options.min_update_interval_sec
    overtime = time.time() - next_update_time
    if overtime < 0:
        logger.debug('%r: skip backup: too early', job.basename)
        return job

    if not os.path.exists(job.file_path):
        logger.error('%r: skip backup: file not found: %r', job.basename, job.file_path)
        return job

    target_dir = job.file_backup_folder
    if os.path.exists(target_dir):
        if not os.path.isdir(target_dir):
            logger.error(
                '%r: skip backup: unable to create target dir (path already exists and is not directory): %r',
                job.basename,
                target_dir,
            )
            return job
    else:
        os.makedirs(target_dir, exist_ok=True)
        if not os.path.isdir(target_dir):
            logger.error('%r: skip backup: unable to create target dir: %r', job.basename, target_dir)
            return job

    backup_extension = create_backup_extension()
    target_filename = job.basename + '.' + backup_extension
    target_path = os.path.join(target_dir, target_filename)

    try:
        shutil.copyfile(job.file_path, target_path, follow_symlinks=False)
        logger.debug('%r copied to %r', job.file_path, target_path)
    except Exception as exc:
        logger.error('unable to copy file %r to %r: %s', job.file_path, target_path, exc)
        return job

    return job.touch_last_update_time()


class BackupManager:
    def __init__(
        self,
        *,
        folder_to_monitor: str,
        backup_folder: str,
        backup_options: BackupOptions,
        basename_filter: BasenameFilter
    ) -> None:
        self.folder_to_monitor: Final = folder_to_monitor
        self.backup_folder: Final = backup_folder
        self.backup_options: Final = backup_options
        self.basename_filter: Final = basename_filter
        self.file_records: Final[Dict[str, FileInfo]] = {}

    def backup_all_files(self) -> None:
        files = next(os.walk(self.folder_to_monitor))[2]
        for filename in files:
            self.backup_file(filename)

    def backup_file(self, basename: str) -> None:
        if not self.basename_filter(basename):
            return
        logger.info('backup %r', basename)
        file_record = self.file_records.get(basename)
        if file_record is None:
            file_record = FileInfo(
                basename=basename,
                file_path=os.path.join(self.folder_to_monitor, basename),
                file_backup_folder=os.path.join(self.backup_folder, basename),
                last_copy_time=time.time() - self.backup_options.min_update_interval_sec - 1,
                last_cleanup_time=time.time() - self.backup_options.cleanup_period_sec - 1,
            )
        new_record = backup_one_file(job=file_record, backup_options=self.backup_options)
        record_after_cleanup = cleanup_old_versions(job=new_record, backup_options=self.backup_options)

        self.file_records[basename] = record_after_cleanup


class FileBackupHandler(FileSystemEventHandler):
    """backup files on creation or update"""

    def __init__(self, backup_manager: BackupManager) -> None:
        super().__init__()
        self.backup_manager = backup_manager

    def on_created(self, event: FileSystemEvent) -> None:
        super().on_created(event)

        if event.is_directory:
            return

        basename = os.path.basename(event.src_path)
        self.backup_manager.backup_file(basename)

    def on_modified(self, event: FileSystemEvent) -> None:
        super().on_modified(event)

        if event.is_directory:
            return

        basename = os.path.basename(event.src_path)
        self.backup_manager.backup_file(basename)
