import argparse
import dataclasses
import datetime
import os
import sys
from typing import List, Optional

from app.game_utils import get_folder_by_game, is_game_filename_for_monitoring
from app.utils import norm_path, BasenameFilter, backup_all_files


@dataclasses.dataclass(frozen=True)
class BackupOptions:
    min_update_interval_sec: int
    backup_depth_days: int
    cleanup_period_sec: int


@dataclasses.dataclass(frozen=True)
class AppConfig:
    folder_to_monitor: str
    backup_folder: str
    basename_filter: BasenameFilter
    backup_options: BackupOptions
    copy_all_files_at_start: bool


class IntRange:
    """
    Origin:
        https://stackoverflow.com/a/61411431/116373
    """

    def __init__(self, *, min_value: Optional[int] = None, max_value: Optional[int] = None) -> None:
        self.min_value = min_value
        self.max_value = max_value
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise RuntimeError(f'wrong values: min={self.min_value}, max={self.max_value}')

    def __call__(self, arg: str) -> int:
        try:
            value = int(arg)
        except ValueError:
            raise argparse.ArgumentTypeError(f'must be an integer but got {arg!r}')
        if self.min_value is not None and value < self.min_value:
            raise argparse.ArgumentTypeError(f'must be an integer >= {self.min_value}')
        if self.max_value is not None and value > self.max_value:
            raise argparse.ArgumentTypeError(f'must be an integer <= {self.max_value}')
        return value


def read_config(args: List[str]) -> AppConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--game',
        choices=('BL2', 'BL3'),
        help='autodiscovery save game folder to protect',
    )
    parser.add_argument('--folder-to-monitor', help='folder to monitor files inside it')
    parser.add_argument(
        '--backup-folder',
        default=os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'backup_files'),
        help='directory to save backups',
    )
    parser.add_argument(
        '--min-backup-interval-sec',
        type=IntRange(min_value=1),
        default=10,
        help='minimum time between making backup copies of same file',
    )
    parser.add_argument(
        '--backup-depth-days',
        type=IntRange(min_value=2),
        default=7,
        help='how many days to keep backup of. 2 days is minimal to avoid losing files on day change',
    )
    parser.add_argument(
        '--cleanup-period-hours',
        type=IntRange(min_value=1, max_value=24),
        default=8,
        help='period between cleanup older backup copies. Cleanup runs separately for each file on new backup event.',
    )
    parser.add_argument(
        '--skip-copy-all-files-at-start',
        action='store_true',
        help='Disable copying all files at program startup',
    )
    params = parser.parse_args(args)

    basename_filter: BasenameFilter

    if params.game is None:
        basename_filter = backup_all_files
        if params.folder_to_monitor is None:
            raise argparse.ArgumentTypeError('you should specify one argument: --game or --folder-to-monitor')
        else:
            folder_to_monitor = norm_path(params.folder_to_monitor)
    else:
        basename_filter = is_game_filename_for_monitoring
        if params.folder_to_monitor is None:
            folder_to_monitor = norm_path(get_folder_by_game(params.game))
        else:
            raise argparse.ArgumentTypeError('you should specify only one argument: --game or --folder-to-monitor')

    if not os.path.isdir(folder_to_monitor):
        raise argparse.ArgumentTypeError(f'not a directory: {folder_to_monitor!r}')

    backup_folder = norm_path(params.backup_folder)
    if os.path.exists(backup_folder):
        if not os.path.isdir(backup_folder):
            raise argparse.ArgumentTypeError(f'--backup-folder value is not a directory: {backup_folder}')
    else:
        os.makedirs(backup_folder, exist_ok=True)
        if not os.path.isdir(backup_folder):
            raise argparse.ArgumentTypeError(f'--backup-folder: unable to create directory: {backup_folder}')

    if folder_to_monitor == backup_folder:
        raise argparse.ArgumentTypeError(f'monitor and backup folder are the same')

    backup_options = BackupOptions(
        min_update_interval_sec=params.min_backup_interval_sec,
        backup_depth_days=params.backup_depth_days,
        cleanup_period_sec=int(datetime.timedelta(hours=params.cleanup_period_hours).total_seconds()),
    )

    copy_all_files_at_start = not params.skip_copy_all_files_at_start

    return AppConfig(
        folder_to_monitor=os.path.abspath(folder_to_monitor),
        backup_folder=backup_folder,
        basename_filter=basename_filter,
        backup_options=backup_options,
        copy_all_files_at_start=copy_all_files_at_start,
    )
