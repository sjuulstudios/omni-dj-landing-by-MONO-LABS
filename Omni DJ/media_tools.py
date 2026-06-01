"""
media_tools — centrale resolver voor de ffmpeg/ffprobe-binaries.

Waarom dit bestaat (sessie 66): in de gesignde .app faalde elke video-upload
met "ffprobe failed". Oorzaak: de code riep kaal 'ffprobe'/'ffmpeg' aan en
leunde op PATH. In de gebundelde app is dat PATH afhankelijk van de
launcher-wrapper en subprocess kreeg soms een schoner env mee, waardoor de
gebundelde binary niet gevonden werd (of de Homebrew-versie, die onder de
hardened runtime weigert te laden vanwege externe dylibs).

Deze module geeft ALTIJD een absoluut pad terug:
  1. Eerst de in de bundle meegeleverde static binary (Contents/Resources/bin).
  2. Anders een via PATH gevonden binary (dev-server / systeem-ffmpeg).
  3. Als laatste de kale naam (laat subprocess zelf falen met een nette error).

Zowel app.py als cutter.py importeren dit, zodat er één bron van waarheid is.
"""

import os
import shutil
import sys
from pathlib import Path


def _bundle_bin_dir():
    """
    Pad naar de map met de meegebundelde ffmpeg/ffprobe binaries.

    In een PyInstaller .app draaien we vanuit Contents/MacOS/ (via de
    launcher-wrapper) en staan de binaries in Contents/Resources/bin/.
    build_macos.sh kopieert ze daarheen. We leiden dat pad af van de
    locatie van het uitvoerbare bestand, niet van sys._MEIPASS (die wijst
    naar de uitgepakte Frameworks-map, niet naar Resources/bin).
    """
    if getattr(sys, "frozen", False):
        # sys.executable = .../Contents/MacOS/Omni DJ(.bin)
        macos_dir = Path(sys.executable).resolve().parent
        candidate = macos_dir.parent / "Resources" / "bin"
        if candidate.is_dir():
            return candidate
    # Dev-flow: een optionele vendor/ffmpeg map naast de broncode mag ook.
    vendored = Path(__file__).resolve().parent / "vendor" / "ffmpeg"
    if vendored.is_dir():
        return vendored
    return None


def resolve(name):
    """
    Geef een absoluut pad naar `name` ('ffmpeg' of 'ffprobe').

    Volgorde: meegebundelde binary → PATH → kale naam (fallback).
    """
    bin_dir = _bundle_bin_dir()
    if bin_dir is not None:
        candidate = bin_dir / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)

    found = shutil.which(name)
    if found:
        return found

    # Laatste redmiddel: kale naam. subprocess geeft dan een duidelijke
    # FileNotFoundError i.p.v. stil falen.
    return name


def ffmpeg():
    """Absoluut pad (of fallback-naam) voor de ffmpeg-binary."""
    return resolve("ffmpeg")


def ffprobe():
    """Absoluut pad (of fallback-naam) voor de ffprobe-binary."""
    return resolve("ffprobe")
