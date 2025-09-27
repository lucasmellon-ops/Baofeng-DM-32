
# DM‑32 Code‑Plug Builder – Beginner‑Friendly Guide


Welcome! This repository helps owners of the Baofeng DM‑32 digital mobile radio to build a complete code‑plug – that’s the set of channels and zones you load into your radio so it knows who to talk to. This guide assumes you’ve never used Python or the Windows command line before. Follow the steps below carefully, and you’ll end up with two CSV files (*_Channels.csv and *_Zones.csv) that you can import directly into the Baofeng CPS (Customer Programming Software).


## 🛠️ What’s in this repository?

| Folder/file                       | What it does                                                                                                                                                                                           | Needed for you?                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------- |
| `format_talkgroups_to_dm32.py`    | Converts a BrandMeister talkgroup export to a clean DM‑32 CSV format.                                                                                                                                  | Yes, if you have a talkgroup list from BrandMeister. |
| `generate_dm32_channels_zones.py` | A Python script with helper functions for channel/zone generation (used by the interactive builder).                                                                                                   | No direct use, the builder calls it.                 |
| `interactive_dm32_builder.py`     | **The main script**.  It asks you for your local frequencies, the number of talkgroups you want, which kinds of channels to include (FRS/GMRS, air band, etc.), and then creates your code‑plug files. | Yes, you’ll run this.                                |
| `run_dm32_interactive.bat`        | A Windows batch file that runs the interactive builder and installs any missing Python libraries.                                                                                                      | Yes, if you’re on Windows.                           |



You may also see DM32_formatted_ascii.csv or similar files – this is from [BM talkgroups](https://brandmeister.network/?page=talkgroups) with 1690 TGs formatted to be compliant with the CPS DMR V1.41 software 


## Step‑by‑step for complete beginners
### 1. Install Python (if you don’t already have it)

Go to python.org/downloads
.

Click [Download Python 3.x.x](https://www.python.org/downloads/windows/) (any 3.9 or newer version is fine) and run the installer.

Important: During installation, check the box that says “Add Python to PATH.” This makes the python and pip commands work at the command prompt.

Click through the installer until it finishes.

### 2. Download your BrandMeister talkgroup list (optional but recommended)

If you want BrandMeister talkgroups, log in to the BrandMeister website and export your talkgroup list to CSV. Name the file something like `BrandMeister_TGs.csv` and save it in the same folder you’re using for this project (for example, C:\Users\YourName\Desktop\DM32).

### 3. Prepare your talkgroup file

- Open a Command Prompt:

- Press the Windows key on your keyboard.

- Type cmd and press Enter. A black window will appear.

- Use the cd command to go to the folder where your files are. For example:

`cd %USERPROFILE%\Desktop\DM32`

- Run the formatter script to clean your BrandMeister CSV. Replace the file name with the actual name of your export:

      python format_talkgroups_to_dm32.py -i "BrandMeister_TGs.csv" -o "DM32_formatted_ascii.csv" --max-length 16


This step reads your BrandMeister talkgroups and makes sure all names are plain English characters, short enough for the DM‑32, with the right commas and line endings.

*Note: If you don’t have a BrandMeister file, skip this step. The interactive builder will still work and let you build channels for repeaters, hotspots, GMRS, etc.*

## 4. Run the interactive builder (the easiest way)

- The batch file **`run_dm32_interactive.bat`** does three things: installs necessary Python libraries, launches the interactive script, and pauses when done so you can read the messages.

- Make sure the following files are all together in one folder:

  <pre>interactive_dm32_builder.py (the main script)

  generate_dm32_channels_zones.py (helper functions)

  DM32_formatted_ascii.csv (only if you did step 3)

  run_dm32_interactive.bat (the batch file)</pre>

- In the Command Prompt (you should already be in the right folder), run:

      run_dm32_interactive.bat


The first time you run it, it may say “Installing required Python libraries...” and take a minute. That’s normal.

You’ll then see a welcome banner:

# DM‑32 Interactive Code‑Plug Builder
========================================


**Follow the prompts carefully. Here’s what you’ll be asked:**

1. Path to DM‑32 formatted talkgroups CSV – press Enter to use DM32_formatted_ascii.csv if you created it, or type the full path to your talkgroup file. If you don’t have a talkgroup file, just press Enter.

2. How many talkgroups to include – the default is 50. Enter a smaller number to keep your radio’s contact list manageable; larger values may cause the radio to freeze
miklor.com
.

3. Your DMR ID / callsign string – this appears in the CSV header and is optional. Enter your DMR ID, or leave the default and edit later in the CPS.

4. Name of your talkgroup zone – choose a name (e.g. “Hotspot” or “Repeater”). This becomes the zone label in the radio menu.

5. Is this talkgroup zone for a hotspot? – if yes, the default power level is Low. If you’re programming a repeater zone, choose no.

6. Power level for talkgroup channels – choose High, Middle or Low. Hotspots are usually Low.

7. Talkgroup receive/transmit frequency – type in your hotspot or simplex frequency (e.g. 430.1000). If you’re unsure, leave the default 430.0000 MHz.

8. Talkgroup colour code – for DMR hotspots, this is usually 1. Enter your repeater’s colour code if different.

9. Talkgroup time slot – most hotspots use slot 2. Enter 1 or 2.

10. For each category you’ll see “Include GMRS/FRS simplex channels? (Y/n)” and similar prompts for MURS, airband, marine VHF, ham simplex calling, and NOAA weather. Press Enter to say yes or type n to skip a category.

11. You can then add analog repeaters (name, RX/TX frequency and CTCSS tone) and an optional DMR repeater or hotspot (name, RX/TX frequency, colour code and talkgroups on TS 1 and TS 2). To stop adding repeaters, press Enter at the “Enter repeater name” prompt.

**When the script finishes, it will say something like:**

<pre>Generation complete.  Wrote 182 channels to DM_32_Custom_Channels.csv and 9 zones to DM_32_Custom_Zones.csv.
You can now import these files into the DM‑32 CPS.</pre>

### 5. Importing into the Baofeng CPS

1. Open the Baofeng DM‑32 CPS on your computer.

2. Connect your radio with its programming cable and turn it on.

3. Device Manager → `Ports (COM & LPT) → Look for USB-SERIAL CH*** (COM*) 

*Note: You can unplug and reconnect the radio and watch for what COM Port comes and goes*

4. In CPS go to Setting → COM Setting → COM Type: `COM` COM: `see step 3` Baudrate: `115200` → OK

5. In CPS Read Data `Ctrl + R` or Program(P) → Read Data

*Note: I might be superstitious or in an old way of thinking, but it is alway best practice to read from the radio first then back it up. You now have a base to edit from.*

6. In CPS import in order. DMR Radio → Public → TG, Channel, Zone → There is `Import` on the bottom of the page
  <pre>Talk Groups `DM32_formatted_ascii.csv`
Channel `****_Channels.csv`
Zone `****_Zones.csv`
</pre>

7. In CPS Read Data `Ctrl + W` or Program(P) → Write Data

**Again read the radio first to back up its existing code‑plug before writing a new one.**

Frequently asked questions


What’s a colour code? On DMR, a colour code is like a “sub‑channel.” Most hotspots use colour code 1. Your repeater’s colour code may be different—check with the repeater owner.

Why do I need Python? These scripts are written in Python, so they need the Python interpreter to run. Once installed, you don’t need to touch Python again.

Where can I find more talkgroups or frequencies? The scripts include common aviation frequencies
fly-ul.com
, marine channels
navcen.uscg.gov
, ham calling frequencies, weather channels, and a curated list of popular BrandMeister talkgroups
kf5iw.com
. If you need other channels, feel free to modify the scripts or add them manually in the CPS.

Contributing & support

If you discover a better way to program the DM‑32, have corrections, ideas for improvements, more features, or want to share your own code‑plug, please open an issue or pull request on GitHub. Contributors of all skill levels are welcome!

For troubleshooting or help with the scripts, open an issue on the repository. Provide details about your operating system, Python version, and any error messages you see.

Thank you for using this project. We hope it saves you time and helps you get on the air quickly!
