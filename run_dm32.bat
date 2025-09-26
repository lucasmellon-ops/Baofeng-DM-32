@echo off
REM -----------------------------------------------------------------------------
REM DM‑32 Channel & Zone Generator Batch Script
REM -----------------------------------------------------------------------------
REM This Windows batch file makes it easy to run the DM‑32 channel generator
REM without opening the command prompt manually.  It installs the required
REM Python libraries and executes the script with sensible defaults.  Feel free
REM to edit the variables below to change the number of talkgroups or your DMR
REM ID.

REM ------------- Configuration -------------------------------------------------
REM Path to your talkgroup list (make sure the file exists in this folder)
set TG_FILE=DM32_formatted_ascii.csv

REM Number of BrandMeister talkgroups to include in the Pi‑Star zone.  Reduce
REM this number if your radio freezes due to too many contacts.
set PI_STAR_COUNT=100

REM Your DMR ID and callsign.  Replace 1234567 with your actual ID.
set DMR_ID=1234567

REM Output file prefix.  The script will create <prefix>_Channels.csv and
REM <prefix>_Zones.csv
set OUT_PREFIX=DM_32_Custom

REM ------------- Execution -----------------------------------------------------
echo Installing required Python libraries...
pip install pandas unidecode >nul 2>&1

echo Running DM‑32 channel generator...
python generate_dm32_channels_zones.py ^
  --talkgroups "%TG_FILE%" ^
  --output-prefix "%OUT_PREFIX%" ^
  --pi-star-count %PI_STAR_COUNT% ^
  --dmr-id "%DMR_ID%" ^
  --no-interactive

echo.
echo Generation complete.  The files %OUT_PREFIX%_Channels.csv and %OUT_PREFIX%_Zones.csv
echo have been created in this folder.  You can now import them into the DM‑32 CPS.
echo.
pause