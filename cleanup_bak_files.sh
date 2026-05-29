#!/usr/bin/env bash
#
# Opruimscript voor de 138 .bak files in het Omni DJ project.
#
# Maakt eerst een tar.gz-backup, verwijdert dan de originelen.
# Veilig: als de tar.gz mislukt, wordt er niets verwijderd.
#
# Gebruik:
#     cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ"
#     bash cleanup_bak_files.sh
#
# Wat het NIET aanraakt:
#     - venv/        (Python virtuele omgeving)
#     - .superpowers/ (Claude state)
#     - dist/        (de gebouwde .app — die wordt bij volgende build sowieso vervangen)

set -euo pipefail

cd "$(dirname "$0")"

ARCHIVE="_bak-archive-2026-05-17.tar.gz"

echo ""
echo "=== Omni DJ — .bak opruimen ==="
echo ""

echo "Stap 1/4 — .bak files inventariseren..."
COUNT=$(find . -name "*.bak" -not -path "*/venv/*" -not -path "*/.superpowers/*" -not -path "*/dist/*" | wc -l | tr -d ' ')
echo "Gevonden: $COUNT .bak files"
echo ""

if [[ "$COUNT" == "0" ]]; then
    echo "Niets te doen — geen .bak files gevonden."
    exit 0
fi

echo "Stap 2/4 — tar.gz backup maken: $ARCHIVE"
find . -name "*.bak" -not -path "*/venv/*" -not -path "*/.superpowers/*" -not -path "*/dist/*" -print0 | \
    tar -czf "$ARCHIVE" --null --files-from=-
SIZE=$(ls -lh "$ARCHIVE" | awk '{print $5}')
echo "Backup gemaakt: $ARCHIVE ($SIZE)"
echo ""

echo "Stap 3/4 — backup verifiëren..."
TAR_COUNT=$(tar -tzf "$ARCHIVE" | wc -l | tr -d ' ')
if [[ "$TAR_COUNT" != "$COUNT" ]]; then
    echo "FOUT: tar bevat $TAR_COUNT files maar we wilden $COUNT backuppen."
    echo "Verwijder NIETS. Check $ARCHIVE eerst handmatig."
    exit 1
fi
echo "Backup OK ($TAR_COUNT files)."
echo ""

echo "Stap 4/4 — originelen verwijderen..."
find . -name "*.bak" -not -path "*/venv/*" -not -path "*/.superpowers/*" -not -path "*/dist/*" -delete
REMAINING=$(find . -name "*.bak" -not -path "*/venv/*" -not -path "*/.superpowers/*" -not -path "*/dist/*" | wc -l | tr -d ' ')
echo "Verwijderd. Nog $REMAINING .bak files over (in venv/superpowers/dist, die laten we staan)."
echo ""
echo "=== Klaar ==="
echo "Backup     : $(pwd)/$ARCHIVE"
echo "Restore    : tar -xzf $ARCHIVE      # in deze map"
