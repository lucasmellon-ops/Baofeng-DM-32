"""
Script to convert a BrandMeister talkgroup list into the DM‑32/DMR CPS contact format.

The DM‑32 (and many other DMR radios) use a simple CSV contact list with the
following columns:

* ``No.``  – sequential index starting from 1
* ``Name`` – the descriptive name of the talkgroup or contact
* ``ID``   – the numerical talkgroup ID
* ``Type`` – either ``Group Call`` or ``Private Call``

BrandMeister publishes its talkgroups as a CSV file with at least the following
columns: ``Country``, ``Talkgroup``, ``Name``, and sometimes an extra field
with a hyperlink.  This script reads such a file, sanitises the data and
outputs a new CSV in the DM‑32 format.  By default all talkgroups are tagged
as ``Group Call``.  If you wish to mark specific IDs as private calls you can
edit the ``PRIVATE_CALL_IDS`` set below.

Usage:
    python format_talkgroups_to_dm32.py \
        --input "Talkgroups BrandMeister.csv" \
        --output "DM32_formatted.csv"

The script will create/overwrite the output file and print a short summary
including the number of entries written.  You can then import the resulting
CSV into your radio's CPS.
"""

import argparse
import csv
import sys
from pathlib import Path

import pandas as pd
from unidecode import unidecode
import re

# Set of talkgroup IDs that should be tagged as Private Call instead of Group Call.
# You can customise this list based on your radio's firmware or operating
# practices.  Common private call talkgroups include Parrot or Echo servers.
PRIVATE_CALL_IDS = {
    9990,  # Parrot/Echo test on some networks
    9998,  # BrandMeister Parrot (regional)
    # Add more IDs here if needed
}


def normalise_talkgroups(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the BrandMeister talkgroup DataFrame.

    Drops rows without a valid talkgroup ID or name, removes duplicate IDs
    (keeping the first occurrence), trims whitespace and ensures that the
    talkgroup ID is an integer.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame loaded from the BrandMeister CSV file.

    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame with columns ``ID`` and ``Name``.
    """
    # Rename columns to standard names
    df = df.rename(columns={
        'Talkgroup': 'ID',
        'ID': 'ID',
        'Name': 'Name',
    })

    # Drop rows with missing or NaN ID or Name
    df = df.dropna(subset=['ID', 'Name'])

    # Convert ID to integer if possible; some IDs may be floats or strings
    def to_int(x):
        try:
            # Some IDs may be specified as floats in the CSV (e.g., 91.0). Cast to int.
            return int(float(str(x).strip()))
        except (ValueError, TypeError):
            return None

    df['ID'] = df['ID'].apply(to_int)

    # Drop rows where conversion failed
    df = df.dropna(subset=['ID'])

    df['ID'] = df['ID'].astype(int)

    # Trim whitespace in names
    df['Name'] = df['Name'].astype(str).str.strip()

    # Remove duplicate IDs, keeping the first occurrence
    df = df.drop_duplicates(subset=['ID'], keep='first')

    # Sort by numeric ID for a consistent ordering
    df = df.sort_values(by='ID').reset_index(drop=True)

    return df[['ID', 'Name']]


def sanitise_name(name: str, max_length: int) -> str:
    """Transliterate to ASCII, remove disallowed characters and truncate.

    Parameters
    ----------
    name : str
        The original talkgroup name.
    max_length : int
        Maximum number of characters allowed.  If the transliterated name is
        longer than this value, it will be truncated.

    Returns
    -------
    str
        Sanitised name that fits within the character limit.
    """
    # Transliterate to closest ASCII representation
    ascii_name = unidecode(name)

    # Remove characters that are not printable ASCII (letters, numbers, space and
    # limited punctuation). We allow hyphens and underscores which are common in
    # talkgroup names.
    ascii_name = re.sub(r'[^A-Za-z0-9 _\-]', '', ascii_name)

    # Collapse multiple spaces into a single space
    ascii_name = re.sub(r'\s+', ' ', ascii_name).strip()

    # Truncate to the maximum allowed length
    if len(ascii_name) > max_length:
        ascii_name = ascii_name[:max_length]

    return ascii_name


def convert_to_dm32_format(df: pd.DataFrame, max_length: int) -> pd.DataFrame:
    """Convert normalised talkgroup DataFrame into DM‑32 CPS contact format.

    Adds sequential numbering starting from 1 and a Type column set to
    ``Group Call`` by default, or ``Private Call`` if the ID is found in
    ``PRIVATE_CALL_IDS``.  Talkgroup names are transliterated to ASCII, all
    disallowed characters removed, and truncated to ``max_length`` characters.

    Parameters
    ----------
    df : pandas.DataFrame
        Normalised DataFrame with columns ``ID`` and ``Name``.
    max_length : int
        Maximum length for the contact name.

    Returns
    -------
    pandas.DataFrame
        DataFrame in DM‑32 contact CSV format with columns ``No.``, ``Name``,
        ``ID``, and ``Type``.
    """
    df_dm32 = pd.DataFrame()
    df_dm32['No.'] = range(1, len(df) + 1)
    # Sanitise names
    df_dm32['Name'] = df['Name'].apply(lambda n: sanitise_name(str(n), max_length))
    df_dm32['ID'] = df['ID']
    df_dm32['Type'] = df_dm32['ID'].apply(
        lambda x: 'Private Call' if x in PRIVATE_CALL_IDS else 'Group Call'
    )
    return df_dm32


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Convert BrandMeister talkgroups CSV into DM‑32 CPS format.')
    parser.add_argument('--input', '-i', required=True, help='Path to BrandMeister talkgroup CSV')
    parser.add_argument('--output', '-o', required=True, help='Path to write the DM‑32 formatted CSV')
    parser.add_argument('--max-length', '-m', type=int, default=16,
                        help='Maximum length for contact names (default: 16 characters)')
    parser.add_argument('--encoding', '-e', default='ascii',
                        help=('Character encoding used to write the output CSV. ' \
                              'Default is "ascii", which matches many DMR CPS expectations. ' \
                              'Other values such as "utf-8" or "utf-8-sig" can be used if required.'))

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: input file {input_path} does not exist.", file=sys.stderr)
        return 1

    # Load the BrandMeister talkgroup CSV.  Use engine='python' to support uncommon
    # delimiters and encoding errors gracefully.
    try:
        df_raw = pd.read_csv(input_path, engine='python')
    except Exception as e:
        print(f"Failed to read {input_path}: {e}", file=sys.stderr)
        return 1

    # Normalise the talkgroups
    df_norm = normalise_talkgroups(df_raw)

    # Convert to DM‑32 format
    df_dm32 = convert_to_dm32_format(df_norm, args.max_length)

    # Write the result to CSV.  Ensure the index is not written.
    # Use the specified encoding to avoid errors in CPS and write Windows-style
    # line endings (\r\n).  Pandas has deprecated the ``line_terminator``
    # argument in favor of ``lineterminator``, so use the latter for forward
    # compatibility.
    df_dm32.to_csv(
        output_path,
        index=False,
        encoding=args.encoding,
        errors='ignore',
        lineterminator='\r\n'
    )

    print(f"Converted {len(df_dm32)} talkgroups to DM‑32 format and wrote to {output_path} using encoding {args.encoding}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())