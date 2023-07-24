import sys

from app.core import monitor_and_backup_files
from app.utils import python_version_check

if __name__ == '__main__':
    python_version_check()
    monitor_and_backup_files(sys.argv[1:])
