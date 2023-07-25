# Backup, Motherfucker

### Why this name?
This is reference to Pulp Fiction movie scene:
https://www.youtube.com/watch?v=a0x6vIAtFcI

## What is it for
To monitor file changes/additions inside specific folder (non-recursively!) and make a backup copies in dedicated folder.

Original goal was to save Borderlands 3 savegame files that could be broken during Steam/SHiFT synchronization process.

### Disclaimer
This program will make copies of files only. It will not restore files back to original places.

## How it works
- monitor specific directory for file addition/changes (non-recursively!) and copy changed files to back up folder in directory which name equal to file basename
- add current time stamp to every copied file, e.g. file `data.bin` will become `%BACKUIP_FOLDER%/data.bin/data.bin.2023-08-01--22-00-05` after copy complete
- cleanup periodically to keep only files for N last days with change events. If you specified to keep files for 2 days and monitored file was changed on Monday/Wednesday/Saturday then there will be left only copies made on Wednesday/Saturday
- files moving/deletion is not monitored

## How to install

### 1. install Python 3.8 or higher

- go to https://www.python.org/downloads/
- download and install bundle for your system
- check version by running command 
```
python -V
```

### 2. download source code

- find green 'Code' button on project main page (https://github.com/loot-midget/backup_motherfucker)
- click on it
- choose 'download ZIP'
- uncompress downloaded file upon completion

### 3. install dependencies

- go to project folder, e.g. `backup_motherfucker`
- run command
```shell
python -m pip install -r requirements.txt --user
```

### 4. run backup
This short sample for Borderlands 3:  
```shell
python bmf.py --game=BL3 
```
backup directory will be auto-discovered and backup copies will be put in `backup_files` inside program directory.

Full command line options are described below.

## Command-line options

### `--game`
Specify type of the game for save game folder auto-discovery.

Valid values are:
- `BL2` - for Borderlands 2 (on macos)
- `BL3` - for Borderlands 2 (on Windows)

Default value: none

Example:
`--game=BL3`

### `--backup-folder`
Path to back up folder where all copies will be stored.

**Default value**
folder `backup_files` inside program folder.

**Examples**
- Windows: `--backup-folder=C:\bl3_backup`
- Other platforms: `--backup-folder=/users/JohnDoe/bl3_backup`

### `--min-backup-interval-sec`
Minimum time between making backup copies of same file.

- minimum value: 1
- default value: 10

### `--backup-depth-days`

History depth in days.

- minimum value: 2 (see explanation below)
- default value: 7

#### Cleanup algorithm
Cleanup runs separately for each file on new backup event.

Steps:
- extract day of backup file, e.g. `2023-07-24` from `Save0001.sav.2023-07-24--23-38-01`
- group backup copies by day
- keep the newest files for {`--backup-depth-days`} days and remove older copies

That's why minimum required value is 2.

### `--cleanup-period-hours`
Period between cleanup older backup copies in hours.

- minimum: 1
- maximum: 24
- default: 8