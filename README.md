DM-32 Talkgroup Converter

A Python utility to convert BrandMeister
 talkgroup lists into a CSV format compatible with the Baofeng DM-32 CPS (Customer Programming Software).

✨ Features

Reads the official BrandMeister talkgroup CSV export

Cleans and deduplicates entries

Transliterates names to plain ASCII (e.g., removes accents, converts Greek → English letters)

Truncates names to a configurable max length (default: 16 characters — safe for DM-32)

Assigns Group Call or Private Call automatically

Outputs a CSV in the exact format required by the DM-32 CPS (No.,Name,ID,Type)

Uses Windows CRLF line endings to prevent import errors

📂 File workflow

Input:

Talkgroups BrandMeister.csv → from BrandMeister

DM32.csv → exported once from DM-32 CPS (to confirm structure)

Output:

DM32_formatted_ascii.csv → ready for import into CPS

🔧 Requirements

Python 3.8 or higher

Install dependencies:

pip install pandas unidecode

🚀 Usage

On Windows (if your files are on your Desktop):

cd %USERPROFILE%\Desktop

python format_talkgroups_to_dm32.py ^
  -i "Talkgroups BrandMeister.csv" ^
  -o "DM32_formatted_ascii.csv" ^
  --max-length 16 ^
  --encoding ascii


On Linux / macOS:

python format_talkgroups_to_dm32.py \
  -i "Talkgroups BrandMeister.csv" \
  -o "DM32_formatted_ascii.csv" \
  --max-length 16 \
  --encoding ascii

⚙️ Arguments
Argument	Default	Description
-i, --input	none	Input CSV file (BrandMeister talkgroups)
-o, --output	none	Output CSV file for DM-32 CPS
-m, --max-length	16	Maximum length for contact names
-e, --encoding	ascii	Output file encoding (use ascii for DM-32 CPS compatibility)
📌 Notes

The DM-32 supports up to 50,000 DMR contacts, but names should not exceed 16 characters.

The CPS import will fail if:

The CSV contains a blank line at the top

The file uses Unix line endings (\n instead of \r\n)

Non-ASCII characters are present in names

Always check the generated CSV with a text editor before importing.

📝 Example Output
No.,Name,ID,Type
1,World-wide,91,Group Call
2,Europe,92,Group Call
3,North America,93,Group Call
4,Parrot,9990,Private Call
