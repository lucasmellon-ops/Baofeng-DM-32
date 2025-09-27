
# DM‑32 Talkgroup & Channel Generator (Windows Edition)


This guide walks you through converting a BrandMeister talkgroup list into a
codeplug for the Baofeng **DM‑32** handheld radio using a Windows PC. It is
written for beginners who may have never opened the command prompt. Follow
each step carefully and you’ll be able to generate and import your own
channels and zones in a few minutes.


## 🛠️ What you need


* A Windows computer with an internet connection.
* Your BrandMeister talkgroup export in CSV format, converted to
`DM32_formatted_ascii.csv` using the provided Python script
`format_talkgroups_to_dm32.py`. The one included is from 9/26/2025
* The generator script: `generate_dm32_channels_zones.py`.
* (Optional) The batch file `run_dm32.bat` for one‑click operation.


If you don’t yet have a talkgroup CSV, see the **Talkgroup export** section
below.


## 📦 Step 1: Gather your files


1. Create a folder on your computer (for example on your **Desktop**) and
copy these files into it:
- `generate_dm32_channels_zones.py` – the Python generator script.
- `DM32_formatted_ascii.csv` – your talkgroup list in the DM‑32 format.
- `run_dm32.bat` – a batch file that runs the generator with safe defaults.
2. If any of these files are missing, download them from this repository.


## 🐍 Step 2: Install Python


The script requires Python 3. If Python isn’t already installed on your
computer:


1. Open your web browser and visit [python.org](https://www.python.org/).
2. Click **Downloads** and choose the latest **Python 3** installer for
Windows.
3. Run the installer. On the first screen **check the box labeled
“Add Python to PATH”**, then click **Install Now** and follow the
prompts. When the installer finishes, close the window.


## 📦 Step 3: Install the required libraries


The generator uses two small helper libraries, `pandas` and `unidecode`. If
you use the batch file, it will install them for you automatically. If you
prefer to install them manually:


1. Press **Win + R**, type `cmd` and press **Enter**. This opens the
Command Prompt.
2. In the black window, type the following and press **Enter**:


```
pip install pandas unidecode
```


3. Wait until the installation completes. You can close the window or leave
it open for the next step.


## ▶️ Step 4: Run the script (easy method)


For most users the easiest way to run the generator is to double‑click the
batch file provided in this repo:


1. In the folder you created in **Step 1**, locate `run_dm32.bat`.
2. Double‑click it. A Command Prompt window will open and automatically:
- Install `pandas` and `unidecode` (if they aren’t already installed).
- Run `generate_dm32_channels_zones.py` with a safe default of **100
talkgroups** and your DMR ID (you can edit these values in the
batch file).
3. When the script finishes, the window will say **“Press any key to
continue…”**. After you press a key, two new files will appear in
the folder:
- `DM_32_Custom_Channels.csv`
- `DM_32_Custom_Zones.csv`


You’re now ready to import these files into the DM‑32 CPS.


### 🎛️ Customising the batch file


Open `run_dm32.bat` in **Notepad** to change two settings:


* **Talkgroup count** – Adjust the number after `--pi-star-count` to reduce
the number of talkgroups in your Pi‑Star zone. Limiting the count can
prevent the radio from freezing if too many contacts are loaded. The
DM‑32 supports up to **50 000 digital contacts**【528264452442009†L39-L43】, but
some users report freezing if the list is too large【528264452442009†L170-L173】.
* **DMR ID / Callsign** – Replace `1234567` with your own DMR ID and callsign.


Save the file after editing and double‑click it again to generate a new
codeplug.


## 🔄 Step 5: Import into the DM‑32 CPS


1. Launch the **Baofeng DM‑32 CPS** on your computer.
2. Go to **File → Open**, choose `DM_32_Custom_Channels.csv` and click
**Open**. This loads your channels.
3. Go to the **Zone Management** section and import
`DM_32_Custom_Zones.csv`.
4. Finally, write the new codeplug to your radio using **Program → Write
to Radio**. Follow any prompts to complete the upload.


## 📝 Talkgroup export (optional)


If you haven’t yet created a `DM32_formatted_ascii.csv` file, you can
convert a BrandMeister talkgroup export using the `format_talkgroups_to_dm32.py`
script provided in this repo:


```bat
python format_talkgroups_to_dm32.py -i "Talkgroups BrandMeister.csv" -o "DM32_formatted_ascii.csv" --max-length 16
```


This command takes your raw BrandMeister CSV, cleans it up and trims
talkgroup names to 16 characters.


## ⚠️ Reducing the contact list size


The DM‑32’s firmware and software are limited to **50 000 digital
contacts**【528264452442009†L39-L43】 and the software cannot load more than
50 K records【528264452442009†L170-L173】. If your radio freezes when you open
the contacts menu, reduce the number of talkgroups you include. You can do
this by lowering the value of `--pi-star-count` in the batch file. The
script always adds a small **Popular TGs** zone with widely used talkgroups
like Worldwide 91, North America 93 and USA Bridge 3100【177991216181320†L19-L45】,
so you still have quick access to these even if you reduce the main list.


---


If you get stuck, ask a friend who is comfortable with installing software
to give you a hand. Once everything is set up, you’ll be able to
regenerate your codeplug simply by double‑clicking the batch file.
chatgpt-agent %
