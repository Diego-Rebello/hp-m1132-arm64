#!/bin/bash
# Desfaz o install.sh: remove a fila M1132_arm64, o filtro e o PPD.
# Uso: sudo ./scripts/uninstall.sh
# A fila antiga da HP não é tocada.
set -euo pipefail

QUEUE=M1132_arm64
FILTER_DIR=/Library/Printers/hp-m1132-arm64
PPD_DEST=/Library/Printers/PPDs/Contents/Resources/HP-LaserJet_Professional_M1132_MFP-arm64.ppd

[ "$(id -u)" -eq 0 ] || { echo "ERRO: rode com sudo" >&2; exit 1; }

if lpstat -p "$QUEUE" >/dev/null 2>&1; then
  cancel -a "$QUEUE" 2>/dev/null || true
  lpadmin -x "$QUEUE"
  echo "Fila $QUEUE removida"
fi

rm -rf "$FILTER_DIR"
rm -f "$PPD_DEST"
echo "Filtro e PPD removidos"
