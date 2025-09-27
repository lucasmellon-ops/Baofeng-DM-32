#!/usr/bin/env python3
"""
Interactive DM‑32 Builder
========================

This script provides a guided, interactive way to build a channel and zone
configuration for the Baofeng DM‑32 DMR radio.  It prompts the user for
common parameters such as the talkgroup list, DMR ID, number of talkgroups
to include, and whether to include various categories of channels (FRS/GMRS,
MURS, airband, marine, ham simplex, NOAA weather, popular talkgroups).

Users can also optionally define their own local analog repeaters and a
single DMR repeater or hotspot by entering the appropriate frequencies,
colour code and talkgroup assignments for time slots 1 and 2.  The script
then generates CSV files for channels and zones that can be imported into
the DM‑32 CPS.

The goal is to make the code‑plug generation process accessible to anyone,
even those who have never used a command prompt.  Defaults are provided for
all inputs, and answering with an empty response will accept the default.

Usage:
    python interactive_dm32_builder.py

This script depends on ``generate_dm32_channels_zones.py`` for many helper
functions.  Ensure both scripts are in the same directory or install
``generate_dm32_channels_zones`` on the Python path.

"""

import os
from typing import List, Dict, Tuple

from generate_dm32_channels_zones import (
    build_frs_gmrs_channels,
    build_airband_channels,
    build_marine_channels,
    build_ham_call_channels,
    build_noaa_weather_channels,
    build_murs_channels,
    build_popular_talkgroups,
    abbreviate_name,
    load_talkgroups,
    write_channels_csv,
    write_zones_csv,
    sanitise_channel_name,
)


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt the user for a yes/no answer.

    Parameters
    ----------
    question : str
        The question to present to the user (without trailing space).
    default : bool, optional
        The default value if the user simply presses Enter.

    Returns
    -------
    bool
        True if the user answers yes, False otherwise.
    """
    default_str = "Y" if default else "N"
    other_str = "n" if default else "y"
    prompt = f"{question} [{default_str}/{other_str}]: "
    while True:
        ans = input(prompt).strip().lower()
        if not ans:
            return default
        if ans in {"y", "yes"}:
            return True
        if ans in {"n", "no"}:
            return False
        print("Please enter Y or N.")


def prompt_string(question: str, default: str) -> str:
    """Prompt the user for a string, returning the default if empty."""
    ans = input(f"{question} [{default}]: ").strip()
    return ans or default


def prompt_int(question: str, default: int) -> int:
    """Prompt the user for an integer, returning the default if empty."""
    while True:
        ans = input(f"{question} [{default}]: ").strip()
        if not ans:
            return default
        try:
            return int(ans)
        except ValueError:
            print("Please enter a valid integer.")


def prompt_float(question: str, default: float) -> float:
    """Prompt the user for a floating‑point number (MHz), returning the default if empty."""
    while True:
        ans = input(f"{question} [{default:.5f}]: ").strip()
        if not ans:
            return default
        try:
            return float(ans)
        except ValueError:
            print("Please enter a valid number (e.g., 146.520).")


def prompt_repeater() -> List[Dict[str, str]]:
    """Ask the user to define one or more analog repeaters.

    Returns a list of repeater dictionaries with keys ``name``, ``rx``, ``tx``,
    and ``ctcss``.  If the user chooses not to define any repeaters, an empty
    list is returned.
    """
    repeaters: List[Dict[str, str]] = []
    add = prompt_yes_no("Would you like to add a local analog repeater?", default=False)
    while add:
        name = input("  Enter repeater name (blank to stop adding): ").strip()
        if not name:
            break
        rx = prompt_float("    Receive frequency (MHz)", 146.520)
        tx = prompt_float("    Transmit frequency (MHz)", rx)
        tone = prompt_string("    CTCSS tone (Hz)", "100.0")
        repeaters.append({
            "name": name,
            "rx": f"{rx:.5f}",
            "tx": f"{tx:.5f}",
            "ctcss": tone,
        })
        add = prompt_yes_no("  Add another analog repeater?", default=False)
    return repeaters


def prompt_dmr_repeater() -> List[Dict[str, str]]:
    """Ask the user to define a DMR repeater or hotspot channel list.

    Returns a list of DMR channels.  If the user does not wish to add a
    repeater, an empty list is returned.  Each channel dictionary includes
    keys ``name``, ``rx``, ``tx``, ``type``, ``power``, ``bandwidth``,
    ``color``, ``slot``, ``tg_name`` and ``tg_id``.
    """
    if not prompt_yes_no("Would you like to add a DMR repeater or hotspot?", default=False):
        return []
    base_name = prompt_string("  Repeater/hotspot base name", "DMR Repeater")
    rx = prompt_float("  Receive frequency (MHz)", 442.000)
    tx = prompt_float("  Transmit frequency (MHz)", rx)
    color = prompt_int("  Colour code", 1)
    # Prompt for talkgroup assignments on Slot 1 and Slot 2
    tg1_id = prompt_string("  Slot 1 talkgroup ID (enter 0 or blank for 'Open')", "0")
    tg1_name_default = "Local" if tg1_id in {"", "0"} else f"TG {tg1_id}"
    tg1_name = prompt_string("  Slot 1 talkgroup name", tg1_name_default)
    tg2_id = prompt_string("  Slot 2 talkgroup ID (enter 0 or blank for 'Open')", "0")
    tg2_name_default = "Local" if tg2_id in {"", "0"} else f"TG {tg2_id}"
    tg2_name = prompt_string("  Slot 2 talkgroup name", tg2_name_default)
    channels: List[Dict[str, str]] = []
    for tg_name, tg_id, slot in [
        (tg1_name, tg1_id, "Slot 1"),
        (tg2_name, tg2_id, "Slot 2"),
    ]:
        # Use 'Local' for open slots
        tg_id_int: int
        try:
            tg_id_int = int(tg_id)
        except ValueError:
            tg_id_int = 0
        display_name = f"{base_name} {tg_name}" if tg_id_int != 0 else f"{base_name} Local"
        channels.append({
            "name": display_name,
            "rx": f"{rx:.5f}",
            "tx": f"{tx:.5f}",
            "type": "Digital",
            "power": "High",
            "bandwidth": "12.5KHz",
            "color": color,
            "slot": slot,
            "tg_name": tg_name,
            "tg_id": tg_id_int if tg_id_int != 0 else 1,
        })
    return channels


def main() -> None:
    print("\nDM‑32 Interactive Code‑Plug Builder\n" + "=" * 40)
    # Prompt for talkgroup file
    tg_default = "DM32_formatted_ascii.csv"
    tg_path = prompt_string("Path to DM‑32 formatted talkgroups CSV", tg_default)
    # Strip surrounding quotes in case the user includes them
    tg_path = tg_path.strip().strip('"').strip("'")
    if not os.path.exists(tg_path):
        print(f"Talkgroup file '{tg_path}' not found.  Please run format_talkgroups_to_dm32.py first and ensure the file is in this folder.")
        return
    # Number of talkgroups to include
    # Default to 50 talkgroups to avoid overloading the radio contact list.  The
    # user can override this value, but typical codeplugs include a modest
    # number of talkgroups (30–50) for smoother operation.
    tg_count = prompt_int("How many talkgroups to include in the Pi-Star zone?", 50)
    # DMR ID / callsign string
    dmr_id = prompt_string("Enter your DMR ID / callsign string", "1234567")


    # Name for the talkgroup zone (hotspot zone).
    tg_zone_name = prompt_string("Name of your talkgroup zone (e.g. hotspot)", "Hotspot")

    # Is this zone for a hotspot (digital simplex)?  Hotspots typically use low
    # power, and users may wish to include popular talkgroups directly in the
    # same zone.  If this is not a hotspot, the talkgroup channels will use
    # middle power by default.
    is_hotspot = prompt_yes_no("Is this talkgroup zone for a hotspot (digital simplex)?", default=True)
    # Determine power level for digital simplex channels.  Default to Low for
    # hotspots and Middle otherwise.  The user may override this value.
    power_default = "Low" if is_hotspot else "Middle"
    digital_power = prompt_string("Power level for talkgroup channels (High/Middle/Low)", power_default)

    # Prompt for the talkgroup simplex frequency, colour code and time slot.
    # These values will be applied to both the imported talkgroup channels and
    # the popular talkgroup channels (if included).  Defaults match common
    # hotspot settings (430.000 MHz, colour code 1, slot 2).
    tg_rx_freq = prompt_float("Talkgroup receive frequency (MHz)", 430.000)
    tg_tx_freq = prompt_float("Talkgroup transmit frequency (MHz)", tg_rx_freq)
    tg_color = prompt_int("Talkgroup colour code (1‑15)", 1)
    # Restrict time slot to 1 or 2; re‑prompt if invalid
    while True:
        tg_slot = prompt_int("Talkgroup time slot (1 or 2)", 2)
        if tg_slot in (1, 2):
            break
        print("Please enter 1 or 2 for the time slot.")
    # Decide how to handle popular talkgroups.  If this is a hotspot, ask if
    # the popular talkgroups should be included in the same zone.  Otherwise,
    # ask if the user wants a separate popular talkgroups zone.
    include_popular_in_hotspot = False
    include_popular_zone = False
    if is_hotspot:
        include_popular_in_hotspot = prompt_yes_no(
            "Include popular talkgroups in this zone?", default=True
        )
    else:
        include_popular_zone = prompt_yes_no(
            "Include a separate zone of popular talkgroups?", default=True
        )

    # Category inclusion
    include_frs = prompt_yes_no("Include GMRS/FRS simplex channels?", default=True)
    include_murs = prompt_yes_no("Include MURS channels?", default=True)
    include_air = prompt_yes_no("Include common airband frequencies?", default=True)
    include_marine = prompt_yes_no("Include marine VHF channels?", default=True)
    include_ham = prompt_yes_no("Include ham simplex calling frequencies?", default=True)
    include_noaa = prompt_yes_no("Include NOAA weather channels?", default=True)

    # Optional analog repeaters
    analog_repeaters = prompt_repeater()
    # Optional DMR repeater/hotspot
    dmr_repeater = prompt_dmr_repeater()

    # Load talkgroups
    tg_list: List[Tuple[str, int]] = load_talkgroups(tg_path, tg_count)

    channels: List[Dict[str, str]] = []
    # Add user‑defined analog repeaters
    for rep in analog_repeaters:
        channels.append({
            "name": rep["name"],
            "rx": rep["rx"],
            "tx": rep["tx"],
            "type": "Analog",
            "power": "High",
            "bandwidth": "12.5KHz",
            "ctcss": rep["ctcss"],
        })
    # Add user‑defined DMR repeater
    for ch in dmr_repeater:
        channels.append(ch)

    # Talkgroup channels: digital simplex on the hotspot/simplex frequency.  Use
    # the user‑specified power level for all talkgroup channels.  These are
    # generated from the imported talkgroup list and truncated to fit the
    # 16‑character name limit.
    # Format the talkgroup RX/TX frequencies as fixed 5‑decimal strings for
    # consistency in the CSV output.  These values are used for all
    # imported talkgroups and popular talkgroups.
    tg_rx_str = f"{tg_rx_freq:.5f}"
    tg_tx_str = f"{tg_tx_freq:.5f}"
    for name, tg_id in tg_list:
        abbr = abbreviate_name(name)
        id_str = str(tg_id)
        max_name_len = max(1, 16 - len(id_str) - 1)
        ch_name = f"{abbr[:max_name_len]} {id_str}"
        channels.append({
            "name": ch_name,
            "rx": tg_rx_str,
            "tx": tg_tx_str,
            "type": "Digital",
            "power": digital_power,
            "bandwidth": "12.5KHz",
            "color": tg_color,
            "slot": f"Slot {tg_slot}",
            "tg_name": name,
            "tg_id": tg_id,
        })

    # Add categories based on user choice
    if include_frs:
        for ch in build_frs_gmrs_channels():
            channels.append({
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Analog",
                "power": ch["power"],
                "bandwidth": ch["bandwidth"],
                "ctcss": ch["ctcss"],
            })
    if include_murs:
        for ch in build_murs_channels():
            channels.append({
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Analog",
                "power": ch["power"],
                "bandwidth": ch["bandwidth"],
                "ctcss": ch["ctcss"],
            })
    if include_air:
        for ch in build_airband_channels():
            channels.append({
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Analog",
                "power": ch["power"],
                "bandwidth": ch["bandwidth"],
                "ctcss": ch["ctcss"],
            })
    if include_marine:
        for ch in build_marine_channels():
            channels.append({
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Analog",
                "power": ch["power"],
                "bandwidth": ch["bandwidth"],
                "ctcss": ch["ctcss"],
            })
    if include_ham:
        for ch in build_ham_call_channels():
            channels.append({
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Analog",
                "power": ch["power"],
                "bandwidth": ch["bandwidth"],
                "ctcss": ch["ctcss"],
            })
    if include_noaa:
        for ch in build_noaa_weather_channels():
            channels.append({
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Analog",
                "power": ch["power"],
                "bandwidth": ch["bandwidth"],
                "ctcss": ch["ctcss"],
            })

    # Build and append popular talkgroups depending on user choices.  If
    # include_popular_in_hotspot is True, assign the user‑selected power
    # level and add them to the same list of channels.  If include_popular_zone
    # is True, keep the default settings.
    if include_popular_in_hotspot or include_popular_zone:
        pop_list = build_popular_talkgroups(tg_rx_str, tg_tx_str, include_id=True)
        for ch in pop_list:
            ch_entry = {
                "name": ch["name"],
                "rx": ch["rx"],
                "tx": ch["tx"],
                "type": "Digital",
                "power": digital_power if include_popular_in_hotspot else ch["power"],
                "bandwidth": ch["bandwidth"],
                "color": ch["color"],
                "slot": ch["slot"],
                "tg_name": ch["tg_name"],
                "tg_id": ch["tg_id"],
            }
            channels.append(ch_entry)

    # Build zones; group by category names
    zone_map: Dict[str, List[str]] = {}
    # Add user analog repeaters zone
    if analog_repeaters:
        zone_map["Analog Repeaters"] = [sanitise_channel_name(rep["name"]) for rep in analog_repeaters]
    # Add user DMR repeater zone
    if dmr_repeater:
        zone_map["DMR Repeater"] = [sanitise_channel_name(ch["name"]) for ch in dmr_repeater]
    # Hotspot talkgroup zone with imported talkgroups.  The zone name comes from
    # user input (tg_zone_name) and may not include non-ASCII characters.
    imported_names = {name for name, _ in tg_list}
    pi_star_names: List[str] = []
    for ch in channels:
        if (
            ch.get("type") == "Digital"
            and ch.get("rx") == tg_rx_str
            and ch.get("tx") == tg_tx_str
            and (
                ch.get("tg_name") in imported_names
                or str(ch.get("tg_name")).startswith("Fav ")
            )
        ):
            pi_star_names.append(sanitise_channel_name(ch["name"]))
    zone_map[tg_zone_name] = pi_star_names
    # Category zones
    if include_frs:
        zone_map["GMRS/FRS"] = [sanitise_channel_name(ch["name"]) for ch in build_frs_gmrs_channels()]
    if include_murs:
        zone_map["MURS"] = [sanitise_channel_name(ch["name"]) for ch in build_murs_channels()]
    if include_air:
        zone_map["Air Band"] = [sanitise_channel_name(ch["name"]) for ch in build_airband_channels()]
    if include_marine:
        zone_map["Marine"] = [sanitise_channel_name(ch["name"]) for ch in build_marine_channels()]
    if include_ham:
        zone_map["Ham Calls"] = [sanitise_channel_name(ch["name"]) for ch in build_ham_call_channels()]
    if include_noaa:
        zone_map["NOAA"] = [sanitise_channel_name(ch["name"]) for ch in build_noaa_weather_channels()]
    if include_popular_zone:
        # When creating a separate popular talkgroups zone, we reuse the
        # channel definitions generated earlier.  The names will already be
        # sanitised by sanitise_channel_name within the list comprehension.
        zone_map["Popular TGs"] = [
            sanitise_channel_name(ch["name"]) for ch in build_popular_talkgroups(tg_rx_str, tg_tx_str, include_id=True)
        ]

    # Write output files
    out_prefix = prompt_string("Output file prefix", "DM_32_Custom")
    channels_file = f"{out_prefix}_Channels.csv"
    zones_file = f"{out_prefix}_Zones.csv"
    write_channels_csv(channels, dmr_id, channels_file)
    write_zones_csv(zone_map, zones_file)
    print(f"\nGeneration complete.  Wrote {len(channels)} channels to {channels_file} and {len(zone_map)} zones to {zones_file}.")
    print("You can now import these files into the DM‑32 CPS.")


if __name__ == "__main__":
    main()