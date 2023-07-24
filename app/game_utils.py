import argparse
import os
import re
import sys

from app.utils import get_user_home_dir, is_windows


def get_single_digits_sub_folder(profiles_folder: str) -> str:
    if not os.path.isdir(profiles_folder):
        raise argparse.ArgumentError(None, f'save folder not found: {profiles_folder!r}')

    inside_folders = next(os.walk(profiles_folder))[1]
    digits_folders = [x for x in inside_folders if re.match('^[0-9]+$', x)]
    if not digits_folders:
        raise argparse.ArgumentError(None, f'there is no folders made form digits in {profiles_folder!r}')

    if len(digits_folders) > 1:
        raise argparse.ArgumentError(
            None,
            f'There are many ({len(digits_folders)}) folders made form digits'
            + f' in {profiles_folder!r}: {digits_folders!r}.'
            + ' Please use --folder-to-monitor option to specify directory to monitor.',
        )

    return os.path.join(profiles_folder, digits_folders[0])


def get_macos_bl2_folder() -> str:
    profiles_folder = os.path.join(
        get_user_home_dir(),
        'Library',
        'Application Support',
        'Borderlands 2',
        'WillowGame',
        'SaveData',
    )
    return get_single_digits_sub_folder(profiles_folder)


def get_windows_bl3_folder() -> str:
    r"""
    "Documents\My Games\Borderlands 3\Saved\SaveGames\"
    https://support.2k.com/hc/en-us/articles/360044405913-Transferring-Save-Files-Between-Epic-and-Steam-on-PC
    """
    profiles_folder = os.path.join(
        get_user_home_dir(),
        'Documents',
        'My Games',
        'Borderlands 3',
        'Saved',
        'SaveGames',
    )
    return get_single_digits_sub_folder(profiles_folder)


def get_folder_by_game(game_code: str) -> str:
    if game_code == 'BL2':
        if not is_windows():
            return get_macos_bl2_folder()
    elif game_code == 'BL3':
        if is_windows():
            return get_windows_bl3_folder()

    raise RuntimeError(f'{game_code} save folder autodiscovery not supported on platform {sys.platform!r} yet')


def is_game_filename_for_monitoring(basename: str) -> bool:
    if basename.lower().endswith('.bak'):
        return False
    if basename.lower() == 'steam_autocloud.vdf':
        return False
    return True
