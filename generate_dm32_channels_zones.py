#!/usr/bin/env python3
"""
DM‑32 Channel & Zone Generator
==============================

This script assists in building a channel and zone CSV for the Baofeng DM‑32
DMR radio.  The DM‑32 stores its channel configuration in a CSV file with
dozens of columns and expects a separate zone file listing channel names
grouped into logical zones.  Programming these by hand can be time‑consuming,
especially when mixing digital DMR talkgroups with analog channels such as
FRS/GMRS, marine, aviation and ham calling frequencies.

Key features:

* Reads a BrandMeister talkgroup list (converted via ``format_talkgroups_to_dm32.py``).
* Lets you specify how many of the most popular talkgroups to include in a
  hotspot (Pi‑Star) zone.  The talkgroups are sorted by their numerical ID and
  filtered to ASCII names only, favouring English names.
* Generates FRS/GMRS simplex channels based on the FCC frequency table【556751487299399†L254-L286】.
* Includes a handful of commonly used aviation frequencies for airband reception【595039912717065†L11-L40】.
* Adds a short list of marine VHF channels covering calling and distress
  frequencies【260183210287028†L119-L140】.
* Provides the national simplex calling frequencies for the 2 m and 70 cm ham
  bands【963259110952447†L37-L42】.
* Incorporates local analog repeaters and a single DMR repeater as defined in
  this script (you can edit or extend these lists).  The example repeater
  definition for KB0P uses a colour code of 1 and assigns U.P.TG (31268) to
  time slot 2 and a generic “Open” channel to time slot 1.
* Writes ``DM_32_Channels.csv`` and ``DM_32_Zones.csv`` with the proper header,
  line endings and encoding expected by the DM‑32 CPS.  These files can be
  imported directly into the software.

Usage:
    python generate_dm32_channels_zones.py \
        --talkgroups DM32_formatted_ascii.csv \
        --output-prefix DM_32 \
        --pi-star-count 150 \
        --dmr-id "KE8MZT USA"

If run without command‑line arguments, the script will prompt you interactively
for a few key inputs and then write the output files in the current
directory.

Note: This script assumes the DM‑32 supports up to 50,000 contacts and that
channel names are limited to 16 characters as noted in the Connect Systems
CS800D manual【348470044762969†L1398-L1404】.
"""

import argparse
import csv
import sys
import os
import re
from typing import List, Dict, Tuple

import pandas as pd

# -----------------------------------------------------------------------------
# Static channel definitions
#
# Feel free to edit these lists to suit your needs.  Each entry is a tuple of
# (channel name, receive frequency MHz, transmit frequency MHz, additional
# parameters).  For analog channels, a tone (CTCSS) can be provided.  Digital
# channels include colour code and time slot, plus a talkgroup name and ID.

def build_frs_gmrs_channels() -> List[Dict[str, str]]:
    """Return a list of FRS/GMRS simplex channels.

    Frequencies and channel numbers are based on the FCC's GMRS/FRS frequency
    table【556751487299399†L254-L286】.  Only the 22 main simplex channels are
    included here; repeater input frequencies (467 MHz) are omitted for
    brevity.

    Each dictionary contains at least the keys ``name``, ``rx`` and ``tx``.
    """
    # Channel definitions: (channel number, frequency MHz)
    frs_channels = [
        (1, 462.5625), (2, 462.5875), (3, 462.6125), (4, 462.6375),
        (5, 462.6625), (6, 462.6875), (7, 462.7125), (8, 467.5625),
        (9, 467.5875), (10, 467.6125), (11, 467.6375), (12, 467.6625),
        (13, 467.6875), (14, 467.7125), (15, 462.55), (16, 462.575),
        (17, 462.6), (18, 462.625), (19, 462.65), (20, 462.675),
        (21, 462.7), (22, 462.725),
    ]
    channels = []
    for ch_num, freq in frs_channels:
        name = f"GMRS/FRS {ch_num:02d}"
        channels.append({
            "name": name,
            "rx": f"{freq:.5f}",
            "tx": f"{freq:.5f}",
            "type": "Analog",
            # Use high power and narrow bandwidth (12.5 kHz) for simplex channels
            "power": "High",
            "bandwidth": "12.5KHz",
            # Tone squelch not used on call channels; set CTCSS encode/decode to None
            "ctcss": None,
        })
    return channels


def build_airband_channels() -> List[Dict[str, str]]:
    """Return a list of commonly used aviation (airband) frequencies【595039912717065†L11-L40】.

    These frequencies cover emergency, air‑to‑air and unicom uses.  Each entry
    includes channel name and frequency (MHz).  All airband channels are
    treated as analog FM with a bandwidth of 25 kHz.
    """
    # Define common airband frequencies using plain ASCII names.  The hyphen in
    # "Air-to-Air" must be a regular ASCII hyphen to avoid encoding errors
    # when writing the CSV.  See 【595039912717065†L11-L40】 for a summary of
    # emergency and air-to-air channel assignments.
    air_freqs = [
        ("121.5 Emergency", 121.500),
        ("122.75 Air-to-Air", 122.750),
        ("122.8 Unicom", 122.800),
        ("123.0 Unicom", 123.000),
        ("123.025 Helicopter", 123.025),
        ("123.45 Air-to-Air", 123.450),
        ("123.1 SAR", 123.100),
    ]
    channels = []
    for name, freq in air_freqs:
        channels.append({
            "name": f"Air {name}",
            "rx": f"{freq:.3f}",
            "tx": f"{freq:.3f}",
            "type": "Analog",
            "power": "High",
            "bandwidth": "25KHz",
            "ctcss": None,
        })
    return channels


def build_marine_channels() -> List[Dict[str, str]]:
    """Return a list of commonly used marine VHF channels【260183210287028†L119-L140】.

    The list includes the international distress and calling channel (16),
    intership navigation (13), recreational hailing (9) and a Coast Guard
    liaison channel (22A).
    """
    marine = [
        ("Marine Ch16 Distress", 156.8),    # Distress, safety and calling【260183210287028†L130-L132】
        ("Marine Ch13 Nav", 156.65),        # Bridge‑to‑bridge navigation【260183210287028†L126-L127】
        ("Marine Ch09 Calling", 156.45),    # Boater calling【260183210287028†L122-L124】
        ("Marine Ch22A USCG", 157.1),       # Coast Guard liaison【260183210287028†L139-L140】
    ]
    channels = []
    for name, freq in marine:
        channels.append({
            "name": name,
            "rx": f"{freq:.3f}",
            "tx": f"{freq:.3f}",
            "type": "Analog",
            "power": "High",
            "bandwidth": "25KHz",
            "ctcss": None,
        })
    return channels


def build_ham_call_channels() -> List[Dict[str, str]]:
    """Return a list of national ham simplex calling frequencies【963259110952447†L37-L42】.

    Includes the 2 m and 70 cm FM simplex calling frequencies.  Additional
    optional frequencies (1.25 m, 6 m, 10 m) are included for convenience.
    """
    ham_calls = [
        ("2m Calling", 146.520),
        ("70cm Calling", 446.000),
        ("1.25m Calling", 223.500),
        ("6m Calling", 50.125),
        ("10m FM Calling", 29.600),
    ]
    channels = []
    for name, freq in ham_calls:
        channels.append({
            "name": name,
            "rx": f"{freq:.3f}",
            "tx": f"{freq:.3f}",
            "type": "Analog",
            "power": "High",
            "bandwidth": "12.5KHz",
            "ctcss": None,
        })
    return channels


def build_murs_channels() -> List[Dict[str, str]]:
    """Return a list of Multi‑Use Radio Service (MURS) channels.

    MURS is a license‑free VHF service in the United States that uses five
    discrete frequencies between 151.8 MHz and 154.6 MHz.  These channels are
    popular for short‑range communications and are sometimes referred to by
    their "blue dot" and "green dot" nicknames.  Channel assignments are
    defined in the FCC rules for the Multi‑Use Radio Service【451724331847063†L45-L59】.

    Each returned entry includes the channel number and frequency.  All MURS
    channels are treated as analog FM with a narrow 12.5 kHz bandwidth to
    remain within the DM‑32's channel constraints.  Users should consult
    current regulations regarding bandwidth and modulation types; channel 4
    and 5 technically allow wider bandwidth up to 20 kHz【451724331847063†L45-L59】.
    """
    # Define the five MURS channels with their center frequencies (MHz).
    # For simplicity we use a 12.5 kHz bandwidth for all channels.  If you
    # wish to differentiate channels 4 and 5 with a wider bandwidth, edit
    # the "bandwidth" field for those channels.
    murs_channels = [
        (1, 151.820),  # Unofficial MURS calling channel【451724331847063†L45-L59】
        (2, 151.880),  # Recommended simplex / repeater linking channel【451724331847063†L45-L59】
        (3, 151.940),  # Emergency / disaster response channel【451724331847063†L45-L59】
        (4, 154.570),  # "Blue Dot" business radio frequency【451724331847063†L45-L59】
        (5, 154.600),  # "Green Dot" business radio frequency【451724331847063†L45-L59】
    ]
    channels: List[Dict[str, str]] = []
    for ch_num, freq in murs_channels:
        channels.append({
            "name": f"MURS {ch_num}",
            "rx": f"{freq:.3f}",
            "tx": f"{freq:.3f}",
            "type": "Analog",
            "power": "High",
            "bandwidth": "12.5KHz",
            "ctcss": None,
        })
    return channels


def build_popular_talkgroups(hotspot_rx: str, hotspot_tx: str, include_id: bool = True) -> List[Dict[str, str]]:
    """Return a list of commonly used BrandMeister talkgroups.

    This helper defines a small set of popular or widely used talkgroups as
    recommended by various DMR communities【177991216181320†L11-L45】.  These
    talkgroups are added as separate digital channels on your hotspot
    frequency.  The channel names include an abbreviated version of the
    talkgroup name along with the TG number, truncated to fit the DM‑32's
    16‑character limit.

    Parameters
    ----------
    hotspot_rx : str
        Receive frequency (MHz) for your hotspot.
    hotspot_tx : str
        Transmit frequency (MHz) for your hotspot.
    include_id : bool, optional
        Whether to append the talkgroup ID to the channel name.  If False,
        only the abbreviated name is used.

    Returns
    -------
    list of dict
        Digital channel definitions compatible with the DM‑32 CSV schema.
    """
    # List of (talkgroup name, TG number) for popular BrandMeister talkgroups.
    popular_tgs: List[Tuple[str, int]] = [
        ("Worldwide", 91),
        ("North America", 93),
        ("USA Bridge", 3100),
        ("America Link", 31656),
        ("SkyHub Link", 310847),
        ("Midwest Regional", 3169),
        ("Northeast Regional", 3172),
        ("MidAtlantic Regional", 3173),
        ("TX-OK Regional", 3175),
        ("Southwest Regional", 3176),
        ("Mountain Regional", 3177),
        ("First Coast", 31121),
        ("TAC 310", 310),
        ("TAC 311", 311),
        ("TAC 312", 312),
        ("TAC 313", 313),
        ("TAC 314", 314),
        ("TAC 315", 315),
        ("TAC 316", 316),
        ("TAC 317", 317),
        ("TAC 318", 318),
        ("TAC 319", 319),
        ("JOTA", 907),
        ("POTA", 3181),
        ("SOTA", 973),
        ("Parrot", 9990),
    ]
    channels: List[Dict[str, str]] = []
    for name, tg_id in popular_tgs:
        # Abbreviate the talkgroup name to keep it concise
        abbr = abbreviate_name(name)
        if include_id:
            id_str = str(tg_id)
            max_name_len = max(1, 16 - len(id_str) - 1)
            ch_name = f"{abbr[:max_name_len]} {id_str}"
        else:
            ch_name = abbr[:16]
        channels.append({
            "name": ch_name,
            "rx": hotspot_rx,
            "tx": hotspot_tx,
            "type": "Digital",
            "power": "Middle",
            "bandwidth": "12.5KHz",
            "color": 1,
            "slot": "Slot 2",
            # Prefix the talkgroup name with "Fav" to differentiate these contacts
            # from the same talkgroup appearing in the main Pi‑Star list.  This
            # prevents duplicate entries when building the Pi‑Star zone.
            "tg_name": f"Fav {name}",
            "tg_id": tg_id,
        })
    return channels


def build_noaa_weather_channels() -> List[Dict[str, str]]:
    """Return a list of NOAA Weather Radio channels.

    NOAA and other North American weather services broadcast on seven VHF
    frequencies between 162.400 MHz and 162.550 MHz【372289208555435†L223-L234】.  Each
    channel here is assigned a sequential number (WX1–WX7).  Channels are
    configured as analog FM with 25 kHz bandwidth.
    """
    freqs = [162.400, 162.425, 162.450, 162.475, 162.500, 162.525, 162.550]
    channels = []
    for i, freq in enumerate(freqs, start=1):
        channels.append({
            "name": f"NOAA WX {i}",
            "rx": f"{freq:.3f}",
            "tx": f"{freq:.3f}",
            "type": "Analog",
            "power": "High",
            "bandwidth": "25KHz",
            "ctcss": None,
        })
    return channels


def abbreviate_name(name: str) -> str:
    """Return an abbreviated version of a talkgroup name.

    This helper shortens common words to better fit within the 16‑character
    limit when combined with a talkgroup ID.  For example, "North America" is
    abbreviated to "N America" and "South Korea" becomes "S Korea".  The
    function performs a few simple replacements and collapses multiple spaces.
    """
    substitutions = [
        # Replace compound phrases first (e.g., "North America") before individual words
        (r"\bNorth\s+America\b", "N Ameri"),
        (r"\bSouth\s+America\b", "S Ameri"),
        (r"\bNorth\b", "N"),
        (r"\bSouth\b", "S"),
        # Use "Amer" instead of "Am" to retain more of the word for readability
        (r"\bAmerica\b", "Amer"),
        (r"\bAustralia\b", "Aust"),
        (r"\bNew Zealand\b", "NZ"),
        (r"\bUnited\b", "U"),
        (r"\bKingdom\b", "K"),
        (r"\bRepublic\b", "Rep"),
        (r"\bDominican\b", "Dom"),
        (r"\bAnd\b", "&"),
        (r"\band\b", "&"),
    ]
    result = name
    for pattern, repl in substitutions:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
    # Collapse multiple spaces and strip
    result = re.sub(r"\s+", " ", result).strip()
    return result


def build_analog_repeaters() -> List[Dict[str, str]]:
    """Return a list of local analog repeater channels.

    These repeater definitions come from user input or the default example in
    this script.  Each repeater dictionary must include the keys ``name``,
    ``rx``, ``tx``, and a ``ctcss`` tone in hertz.
    """
    repeaters = [
        {"name": "KE8IL UHF", "rx": "444.80000", "tx": "449.80000", "ctcss": "100.0"},
        {"name": "K8LOD UHF", "rx": "443.45000", "tx": "448.45000", "ctcss": "100.0"},
        {"name": "K8LOD VHF", "rx": "147.27000", "tx": "147.87000", "ctcss": "100.0"},
        {"name": "KE8IL 2M", "rx": "146.97000", "tx": "146.37000", "ctcss": "100.0"},
    ]
    channels = []
    for rep in repeaters:
        channels.append({
            "name": rep["name"],
            "rx": rep["rx"],
            "tx": rep["tx"],
            "type": "Analog",
            "power": "High",
            "bandwidth": "12.5KHz",
            "ctcss": rep["ctcss"],
        })
    return channels


def build_dmr_repeater() -> List[Dict[str, str]]:
    """Return a list of DMR channels for a single repeater (KB0P example).

    Uses colour code 1 and defines two talkgroups: U.P.TG (31268) on slot 2 and
    an open slot on slot 1.
    """
    repeater = {
        "name_base": "KB0P DMR",
        "rx": "442.20000",
        "tx": "447.20000",
        "color": 1,
        "tg1": ("U.P.TG", 31268, "Slot 2"),
        "tg2": ("KB0P Open", 1, "Slot 1"),
    }
    channels = []
    for tg_name, tg_id, slot in [repeater["tg1"], repeater["tg2"]]:
        name = f"{repeater['name_base']} {tg_name}" if tg_name != "KB0P Open" else f"{repeater['name_base']} Local"
        channels.append({
            "name": name,
            "rx": repeater["rx"],
            "tx": repeater["tx"],
            "type": "Digital",
            "power": "High",
            "bandwidth": "12.5KHz",
            "color": repeater["color"],
            "slot": slot,
            "tg_name": tg_name,
            "tg_id": tg_id,
        })
    return channels


# -----------------------------------------------------------------------------
# CSV writing helpers

def sanitise_channel_name(name: str, max_len: int = 16) -> str:
    """Truncate channel names to the allowed length."""
    return name[:max_len]


def write_channels_csv(channels: List[Dict[str, str]], dmr_id: str, outfile: str) -> None:
    """Write the DM‑32 channel CSV.

    Parameters
    ----------
    channels : list of dict
        Each channel dict must contain at least ``name``, ``type``, ``rx`` and
        ``tx``.  For digital channels, include ``tg_name``, ``tg_id``, ``color``
        and ``slot``.  Analog channels may include a ``ctcss`` tone.
    dmr_id : str
        The radio ID / callsign string to put in the DMR ID field.
    outfile : str
        Path to the output CSV file.
    """
    # Header copied from an exported DM‑32 CPS file.  Do not change the order
    # unless your CPS expects a different format.
    header = [
        "No.", "Channel Name", "Channel Type", "RX Frequency[MHz]", "TX Frequency[MHz]",
        "Power", "Band Width", "Scan List", "TX Admit", "Emergency System",
        "Squelch Level", "APRS Report Type", "Forbid TX", "APRS Receive",
        "Forbid Talkaround", "Auto Scan", "Lone Work", "Emergency Indicator",
        "Emergency ACK", "Analog APRS PTT Mode", "Digital APRS PTT Mode",
        "TX Contact", "RX Group List", "Color Code", "Time Slot", "Encryption",
        "Encryption ID", "APRS Report Channel", "Direct Dual Mode",
        "Private Confirm", "Short Data Confirm", "DMR ID", "CTC/DCS Decode",
        "CTC/DCS Encode", "Scramble", "RX Squelch Mode", "Signaling Type",
        "PTT ID", "VOX Function", "PTT ID Display"
    ]
    rows = []
    for idx, ch in enumerate(channels, start=1):
        row = {
            "No.": str(idx),
            "Channel Name": sanitise_channel_name(ch["name"]),
            "Channel Type": ch.get("type", "Analog"),
            "RX Frequency[MHz]": ch["rx"],
            "TX Frequency[MHz]": ch["tx"],
            "Power": ch.get("power", "High"),
            "Band Width": ch.get("bandwidth", "12.5KHz"),
            "Scan List": "Scan List 1",
            "TX Admit": "Always" if ch.get("type", "Analog") == "Digital" else "Allow TX",
            "Emergency System": "None",
            "Squelch Level": "3",
            "APRS Report Type": "Digital" if ch.get("type") == "Digital" else "Off",
            "Forbid TX": "0",
            "APRS Receive": "1" if ch.get("type") == "Digital" else "0",
            "Forbid Talkaround": "0",
            "Auto Scan": "0",
            "Lone Work": "0",
            "Emergency Indicator": "0",
            "Emergency ACK": "0",
            "Analog APRS PTT Mode": "0",
            "Digital APRS PTT Mode": "0",
            "TX Contact": ch.get("tg_name", "None"),
            "RX Group List": "None",  # can be customised if group lists are defined
            "Color Code": str(ch.get("color", 0)),
            "Time Slot": ch.get("slot", "Slot 1"),
            "Encryption": "0",
            "Encryption ID": "None",
            "APRS Report Channel": "1",
            "Direct Dual Mode": "0",
            "Private Confirm": "0",
            "Short Data Confirm": "0",
            "DMR ID": dmr_id,
            "CTC/DCS Decode": ch.get("ctcss", "None"),
            "CTC/DCS Encode": ch.get("ctcss", "None"),
            "Scramble": "None",
            "RX Squelch Mode": "Carrier/CTC",
            "Signaling Type": "None",
            "PTT ID": "OFF",
            "VOX Function": "0",
            "PTT ID Display": "0",
        }
        rows.append(row)

    # Write file with CRLF line endings
    with open(outfile, "w", newline="", encoding="ascii") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_zones_csv(zone_map: Dict[str, List[str]], outfile: str) -> None:
    """Write the DM‑32 zones CSV.

    Parameters
    ----------
    zone_map : dict
        Mapping of zone names to a list of channel names.  Channel names should
        match the ``Channel Name`` field in the channel CSV (after truncation
        to 16 characters).
    outfile : str
        Path to the output CSV file.
    """
    header = ["No.", "Zone Name", "Channel Members"]
    rows = []
    for idx, (zone_name, ch_names) in enumerate(zone_map.items(), start=1):
        member_str = "|".join(ch_names)
        rows.append({
            "No.": str(idx),
            "Zone Name": zone_name,
            "Channel Members": member_str
        })
    with open(outfile, "w", newline="", encoding="ascii") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


# -----------------------------------------------------------------------------
# Talkgroup selection

def load_talkgroups(path: str, count: int) -> List[Tuple[str, int]]:
    """Load talkgroups from a DM‑32 formatted CSV and return a limited list.

    Parameters
    ----------
    path : str
        Path to the DM‑32 formatted talkgroup CSV (output of
        ``format_talkgroups_to_dm32.py``).  Expected columns: ``Name`` and ``ID``.
    count : int
        Maximum number of talkgroups to return.  Talkgroups are sorted by ID
        ascending.  Only names containing letters, digits or spaces are kept,
        ignoring obviously non‑English names.

    Returns
    -------
    list of (name, id)
        Selected talkgroups as tuples of name and numeric ID.
    """
    df = pd.read_csv(path)
    # Keep only relevant columns
    df = df[["Name", "ID"]]
    # Filter to names containing mostly ASCII letters, digits, spaces and a few
    # punctuation characters (-, /, &, .).  This heuristic avoids names with
    # accented or non‑Latin characters while preserving common talkgroup names
    # like “World‑wide” or “UK Call - QSY to 2351”.
    df = df[df["Name"].str.contains(r"^[A-Za-z0-9 .&/-]+$", regex=True, na=False)]
    # Sort by numeric ID
    df = df.sort_values(by="ID")
    df = df.reset_index(drop=True)
    # Limit to requested count
    df = df.head(count)
    return list(zip(df["Name"].tolist(), df["ID"].tolist()))


# -----------------------------------------------------------------------------
# Main interactive routine

def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate DM‑32 channel and zone CSV files.")
    parser.add_argument("--talkgroups", "-t", help="Path to DM‑32 formatted talkgroup CSV (from previous script)")
    parser.add_argument("--output-prefix", "-o", default="DM_32", help="Prefix for the output CSV files")
    parser.add_argument("--pi-star-count", "-c", type=int, default=150, help="Number of talkgroups to include in the Pi‑Star zone")
    parser.add_argument("--dmr-id", "-d", default="1234567", help="DMR ID or callsign string to embed in channel entries")
    parser.add_argument("--no-interactive", action="store_true", help="Do not prompt for input; use defaults and command‑line options")
    parser.add_argument("--no-tg-id-in-name", action="store_true", help="Do not append the talkgroup ID to Pi‑Star channel names")
    args = parser.parse_args(argv)

    # Gather user inputs if interactive
    if not args.no_interactive:
        if not args.talkgroups:
            tg_path = input("Enter path to DM‑32 formatted talkgroups CSV [DM32_formatted_ascii.csv]: ") or "DM32_formatted_ascii.csv"
            args.talkgroups = tg_path
        args.pi_star_count = int(input(f"How many talkgroups to include in the Pi‑Star zone? [{args.pi_star_count}]: ") or args.pi_star_count)
        args.dmr_id = input(f"Enter your DMR ID / callsign string [{args.dmr_id}]: ") or args.dmr_id

    # Validate talkgroups path
    if not args.talkgroups or not os.path.exists(args.talkgroups):
        print(f"Talkgroup file {args.talkgroups} does not exist.", file=sys.stderr)
        return 1

    # Load talkgroups
    tg_list = load_talkgroups(args.talkgroups, args.pi_star_count)

    # Build channel objects for each category
    channels: List[Dict[str, str]] = []
    # 1. Local analog repeaters
    analog = build_analog_repeaters()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in analog])

    # 2. DMR repeater channels
    dmr_rep = build_dmr_repeater()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Digital", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "color": ch["color"], "slot": ch["slot"], "tg_name": ch["tg_name"], "tg_id": ch["tg_id"]
    } for ch in dmr_rep])

    # 3. Pi‑Star talkgroup channels (digital simplex on hotspot frequency)
    hotspot_rx = "430.00000"
    hotspot_tx = "430.00000"
    for name, tg_id in tg_list:
        # Abbreviate the talkgroup name for brevity
        abbr = abbreviate_name(name)
        if args.no_tg_id_in_name:
            # Truncate to 16 characters if the user wants only the name
            ch_name = abbr[:16]
        else:
            # Append the talkgroup ID to the name while respecting the 16‑character limit
            id_str = str(tg_id)
            max_name_len = max(1, 16 - len(id_str) - 1)
            ch_name = f"{abbr[:max_name_len]} {id_str}"
        channels.append({
            "name": ch_name,
            "rx": hotspot_rx,
            "tx": hotspot_tx,
            "type": "Digital",
            "power": "Middle",
            "bandwidth": "12.5KHz",
            "color": 1,
            "slot": "Slot 2",
            "tg_name": name,
            "tg_id": tg_id,
        })

    # 4. FRS/GMRS channels (analog simplex)
    frs = build_frs_gmrs_channels()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in frs])

    # 5. Airband channels
    air = build_airband_channels()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in air])

    # 6. Marine channels
    marine = build_marine_channels()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in marine])

    # 7. Ham calling frequencies
    ham_calls = build_ham_call_channels()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in ham_calls])

    # 8. NOAA weather radio channels
    weather = build_noaa_weather_channels()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in weather])

    # 9. MURS channels (license‑free VHF service)
    murs = build_murs_channels()
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Analog", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "ctcss": ch["ctcss"]
    } for ch in murs])

    # 10. Popular BrandMeister talkgroups (digital, on the hotspot frequency)
    popular = build_popular_talkgroups(hotspot_rx, hotspot_tx, include_id=not args.no_tg_id_in_name)
    channels.extend([{
        "name": ch["name"], "rx": ch["rx"], "tx": ch["tx"],
        "type": "Digital", "power": ch["power"], "bandwidth": ch["bandwidth"],
        "color": ch["color"], "slot": ch["slot"], "tg_name": ch["tg_name"], "tg_id": ch["tg_id"]
    } for ch in popular])

    # Build zone mapping with channel names truncated to 16 chars to match the CSV
    zone_map: Dict[str, List[str]] = {}
    # Add analog repeaters zone
    zone_map["Analog Repeaters"] = [sanitise_channel_name(ch["name"]) for ch in build_analog_repeaters()]
    # DMR repeater zone
    zone_map["KB0P DMR"] = [sanitise_channel_name(ch["name"]) for ch in build_dmr_repeater()]
    # Pi-Star zone (use ASCII hyphen)
    # Build a list of all Pi‑Star digital channels (Slot 2 channels) generated above
    # Build the Pi‑Star zone using only talkgroups loaded from the input file.
    imported_tg_names = {name for name, _ in tg_list}
    pi_star_names: List[str] = []
    for ch in channels:
        if (
            ch.get("type") == "Digital" and
            ch.get("rx") == hotspot_rx and ch.get("tx") == hotspot_tx and
            ch.get("tg_name") in imported_tg_names
        ):
            pi_star_names.append(sanitise_channel_name(ch["name"]))
    zone_map["Pi-Star"] = pi_star_names
    # GMRS/FRS zone
    zone_map["GMRS/FRS"] = [sanitise_channel_name(ch["name"]) for ch in build_frs_gmrs_channels()]
    # Air band zone
    zone_map["Air Band"] = [sanitise_channel_name(ch["name"]) for ch in build_airband_channels()]
    # Marine zone
    zone_map["Marine"] = [sanitise_channel_name(ch["name"]) for ch in build_marine_channels()]
    # Ham calling zone
    zone_map["Ham Calls"] = [sanitise_channel_name(ch["name"]) for ch in build_ham_call_channels()]
    # NOAA weather zone
    zone_map["NOAA"] = [sanitise_channel_name(ch["name"]) for ch in build_noaa_weather_channels()]

    # MURS zone
    zone_map["MURS"] = [sanitise_channel_name(ch["name"]) for ch in build_murs_channels()]

    # Popular talkgroups zone
    zone_map["Popular TGs"] = [sanitise_channel_name(ch["name"]) for ch in build_popular_talkgroups(hotspot_rx, hotspot_tx, include_id=not args.no_tg_id_in_name)]

    # Write output CSV files
    channels_file = f"{args.output_prefix}_Channels.csv"
    zones_file = f"{args.output_prefix}_Zones.csv"
    write_channels_csv(channels, args.dmr_id, channels_file)
    write_zones_csv(zone_map, zones_file)
    print(f"Wrote {len(channels)} channels to {channels_file}")
    print(f"Wrote {len(zone_map)} zones to {zones_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())