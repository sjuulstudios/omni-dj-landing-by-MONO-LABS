#!/usr/bin/env bash
#
# Initialiseert een lokale git-repository voor het Omni DJ project.
# Geen remote — alles blijft op je Mac. Je kunt later een private GitHub
# of GitLab koppelen als je dat wilt.
#
# Gebruik:
#     cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ"
#     bash init_git.sh
#
# Wat het doet:
#   1. git init in de projectroot
#   2. controleert of .gitignore aanwezig is (zo niet, stopt het)
#   3. controleert dat je .env NIET wordt getrackt
#   4. eerste commit als baseline-snapshot
#
# Daarna kun je veranderen, committen, en altijd terug naar deze baseline:
#     git log
#     git diff
#     git checkout -- bestandsnaam

set -euo pipefail

cd "$(dirname "$0")"

echo ""
echo "=== Omni DJ — git init ==="
echo ""

if [[ -d .git ]]; then
    echo "Er is al een .git map aanwezig — git is al geïnitialiseerd."
    echo "Niets te doen."
    exit 0
fi

if [[ ! -f .gitignore ]]; then
    echo "FOUT: .gitignore ontbreekt. Stop voordat je secrets per ongeluk committet."
    exit 1
fi

echo "Stap 1/5 — git init..."
git init -q

echo "Stap 2/5 — initiële configuratie..."
# Default branch naam
git symbolic-ref HEAD refs/heads/main

# Lokale identity als die niet globaal is gezet
if ! git config user.email >/dev/null 2>&1; then
    git config user.email "omnidj@monohq-labs.com"
    git config user.name  "Sjuul Smits"
fi

echo "Stap 3/5 — controleren dat .env NIET getrackt wordt..."
ENV_FILES=$(find . -name ".env" -not -path "*/venv/*" -not -path "*/.git/*" 2>/dev/null || true)
if [[ -n "$ENV_FILES" ]]; then
    for f in $ENV_FILES; do
        if git check-ignore -q "$f"; then
            echo "  $f — genegeerd door .gitignore ✓"
        else
            echo "  FOUT: $f wordt NIET genegeerd."
            echo "  Stop. Voeg een matchende regel toe aan .gitignore."
            exit 1
        fi
    done
fi

echo "Stap 4/5 — bestanden toevoegen (kan even duren bij eerste keer)..."
git add .

echo "Stap 5/5 — baseline commit..."
git commit -q -m "Baseline: Omni DJ project — pre-installer release prep

Bevat:
  - dj-clip-cutter/ : Flask backend + frontend (Flask, librosa, FFmpeg)
  - landing/        : omnidj.com landingspagina
  - PyInstaller     : OmniDJ.spec + launcher.py + build_macos.sh
  - Juridisch       : privacy.html + terms.html (sub-processors, CCPA, force majeure, etc.)
  - Documentatie    : INSTALLER-RUNBOOK.md + bestaande HANDOVER.md
"

COUNT=$(git ls-files | wc -l | tr -d ' ')
echo ""
echo "=== Klaar ==="
echo "Repository : $(pwd)/.git"
echo "Branch     : main"
echo "Commit     : $(git rev-parse --short HEAD)"
echo "Files      : $COUNT in baseline"
echo ""
echo "Volgende keer dat je iets verandert:"
echo "    git status              # zie wat veranderd is"
echo "    git diff                # zie de daadwerkelijke wijzigingen"
echo "    git add ."
echo "    git commit -m \"Wat je gedaan hebt\""
echo ""
echo "Pas later eventueel een remote toevoegen:"
echo "    git remote add origin git@github.com:sjuulstudios/clip-live.git"
echo "    git push -u origin main"
