#!/usr/bin/env python3
"""
Omni DJ — cleanup tool voor owner-less jobs in output/ (SESSIE 29)

Achtergrond
-----------
Vóór SESSIE 28 schreef de app job-snapshots zonder `user_id`. Sinds de
library-scoping fix in SESSIE 28 zijn die snapshots onzichtbaar voor
elke gebruiker (private by default — geen leak), maar ze blijven wel
op disk staan en kosten ruimte (vaak 100-1500 MB per set).

Wat dit script doet
-------------------
1. Loopt door alle subfolders van OUTPUT_DIR (= Omni DJ/output/)
2. Markeert een folder als 'cleanup-kandidaat' als:
   - job.json ontbreekt, OF
   - job.json bestaat maar user_id is None / ontbreekt
3. Toont een dry-run preview (default) of verplaatst de folders naar
   een quarantine-locatie (--apply).
4. Verwijdert NIETS rechtstreeks — quarantine kan je later zelf wissen
   als je zeker weet dat je niets mist.

Gebruik
-------
    cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"

    # Dry-run (verandert niks, toont alleen wat het zou doen):
    python3 scripts/cleanup_legacy_jobs.py

    # Quarantine-folder verplaatsen (echte actie):
    python3 scripts/cleanup_legacy_jobs.py --apply

    # Eventueel daarna pas wissen (handmatig, na controle):
    rm -rf "output/.quarantine-YYYYMMDD-HHMMSS"

Veiligheidsnetten
-----------------
- Stopt direct als er een job met user_id wordt gevonden in de
  kandidaatlijst (mag nooit).
- Vereist bevestiging "yes" wanneer je --apply meegeeft.
- Schrijft een rapport naar output/.quarantine-*/REPORT.txt met
  tijdstempel en lijst van verplaatste folders.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output'


def find_candidates(output_dir: Path):
    """Returns (candidates, owned, errors).

    candidate = (dirname, reason, size_bytes)
    """
    candidates = []
    owned = 0
    errors = []
    if not output_dir.is_dir():
        errors.append(f'OUTPUT_DIR niet gevonden: {output_dir}')
        return candidates, owned, errors

    for entry in sorted(output_dir.iterdir()):
        if not entry.is_dir():
            continue
        # Sla quarantine-folders zelf over.
        if entry.name.startswith('.quarantine'):
            continue
        job_json = entry / 'job.json'
        size = _dir_size(entry)
        if not job_json.is_file():
            candidates.append((entry.name, 'job.json ontbreekt', size))
            continue
        try:
            with job_json.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            candidates.append((entry.name, f'job.json corrupt: {e!r}', size))
            continue
        uid = data.get('user_id')
        if uid:
            owned += 1
        else:
            candidates.append((entry.name, 'user_id ontbreekt of None', size))
    return candidates, owned, errors


def _dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def _human(n: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if n < 1024:
            return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} PB'


def main():
    ap = argparse.ArgumentParser(description='Clean up owner-less job folders from Omni DJ output/')
    ap.add_argument('--apply', action='store_true', help='Daadwerkelijk verplaatsen naar quarantine. Zonder deze flag = dry-run.')
    ap.add_argument('--yes', action='store_true', help='Sla "yes" prompt over (voor automation).')
    args = ap.parse_args()

    candidates, owned, errors = find_candidates(OUTPUT_DIR)

    print(f'\nOmni DJ — cleanup_legacy_jobs.py')
    print(f'OUTPUT_DIR: {OUTPUT_DIR}')
    print()
    for e in errors:
        print(f'  ERROR: {e}')
    if errors and not OUTPUT_DIR.is_dir():
        sys.exit(2)

    total_size = sum(s for _, _, s in candidates)
    print(f'  Owned jobs (user_id present): {owned}')
    print(f'  Cleanup-kandidaten:           {len(candidates)}')
    print(f'  Totale grootte kandidaten:    {_human(total_size)}')
    print()

    if not candidates:
        print('Niets te doen — geen owner-less jobs gevonden.')
        return 0

    print('Kandidaten:')
    for name, reason, size in candidates:
        print(f'  {name}  ·  {_human(size):>10}  ·  {reason}')
    print()

    if not args.apply:
        print('[dry-run] Geen wijzigingen gemaakt.')
        print('Run met --apply om naar quarantine te verplaatsen.')
        return 0

    if not args.yes:
        ans = input('Typ "yes" om door te gaan: ').strip().lower()
        if ans != 'yes':
            print('Afgebroken.')
            return 0

    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    quarantine = OUTPUT_DIR / f'.quarantine-{ts}'
    quarantine.mkdir(parents=True, exist_ok=False)

    report_lines = [
        f'Omni DJ cleanup report — {datetime.now().isoformat()}',
        f'OUTPUT_DIR: {OUTPUT_DIR}',
        f'Quarantine: {quarantine}',
        f'Kandidaten: {len(candidates)}',
        f'Totale grootte: {_human(total_size)}',
        '',
        'Verplaatst:',
    ]

    moved = 0
    failed = []
    for name, reason, size in candidates:
        src = OUTPUT_DIR / name
        dst = quarantine / name
        try:
            shutil.move(str(src), str(dst))
            moved += 1
            report_lines.append(f'  {name}  ·  {_human(size)}  ·  {reason}')
            print(f'  moved: {name}')
        except Exception as e:
            failed.append((name, repr(e)))
            report_lines.append(f'  FAILED: {name}  —  {e!r}')
            print(f'  FAILED: {name} — {e!r}')

    if failed:
        report_lines.append('')
        report_lines.append('Failures:')
        for n, e in failed:
            report_lines.append(f'  {n}  —  {e}')

    (quarantine / 'REPORT.txt').write_text('\n'.join(report_lines), encoding='utf-8')

    print()
    print(f'Klaar. {moved} folders verplaatst naar:')
    print(f'  {quarantine}')
    print()
    print('Controleer of je niets mist. Daarna kun je quarantine wissen met:')
    print(f'  rm -rf "{quarantine}"')
    return 0


if __name__ == '__main__':
    sys.exit(main())
