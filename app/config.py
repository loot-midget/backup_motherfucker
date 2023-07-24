import argparse
import dataclasses
import os
import sys
from typing import List

from app.game_utils import get_folder_by_game, is_game_filename_for_monitoring
from app.utils import norm_path, BasenameFilter, backup_all_files


@dataclasses.dataclass(frozen=True)
class AppConfig:
    folder_to_monitor: str
    backup_folder: str
    basename_filter: BasenameFilter


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
    params = parser.parse_args(args)

    basename_filter: BasenameFilter

    if params.game is None:
        basename_filter = backup_all_files
        if params.folder_to_monitor is None:
            raise argparse.ArgumentError(None, 'you should specify one argument: --game or --folder-to-monitor')
        else:
            folder_to_monitor = norm_path(params.folder_to_monitor)
    else:
        basename_filter = is_game_filename_for_monitoring
        if params.folder_to_monitor is None:
            folder_to_monitor = norm_path(get_folder_by_game(params.game))
        else:
            raise argparse.ArgumentError(None, 'you should specify only one argument: --game or --folder-to-monitor')

    if not os.path.isdir(folder_to_monitor):
        raise argparse.ArgumentError(None, f'not a directory: {folder_to_monitor!r}')

    backup_folder = norm_path(params.backup_folder)
    if os.path.exists(backup_folder):
        if not os.path.isdir(backup_folder):
            raise argparse.ArgumentError(None, f'--backup-folder value is not a directory: {backup_folder}')
    else:
        os.makedirs(backup_folder, exist_ok=True)
        if not os.path.isdir(backup_folder):
            raise argparse.ArgumentError(None, f'--backup-folder: unable to create directory: {backup_folder}')

    if folder_to_monitor == backup_folder:
        raise argparse.ArgumentError(None, f'monitor and backup folder are the same')

    return AppConfig(
        folder_to_monitor=os.path.abspath(folder_to_monitor),
        backup_folder=backup_folder,
        basename_filter=basename_filter,
    )
