@echo off
REM -----------------------------------------------------------------------------
REM DM‑32 Interactive Builder Batch Script
REM -----------------------------------------------------------------------------
REM This batch file runs the interactive code‑plug builder for the Baofeng DM‑32.
REM It installs the required Python libraries and then launches
REM interactive_dm32_builder.py, which will prompt you for frequencies,
REM talkgroup counts and channel categories.  Use this if you prefer to
REM customise your code plug via questions instead of editing variables.

echo Installing required Python libraries...

REM Use the Python launcher (py) with -3 to ensure Python 3 is used and
REM to avoid the Windows Store alias issue【678783621713730†L223-L259】.
py -3 -m pip install pandas unidecode >nul 2>&1

echo Launching the interactive DM‑32 builder...

py -3 interactive_dm32_builder.py

echo.
echo Interactive generation complete.  If you answered all prompts, the
echo channel and zone CSV files will be created in this directory.
echo You can now import them into the DM‑32 CPS.
echo.
pause