#!/bin/bash
# Undoes install.sh: removes the M1132_arm64 queue, the filter and the PPD.
# Usage: sudo ./scripts/uninstall.sh
# The old HP queue is not touched.
set -euo pipefail

QUEUE=M1132_arm64
FILTER_DIR=/Library/Printers/hp-m1132-arm64
PPD_DEST=/Library/Printers/PPDs/Contents/Resources/HP-LaserJet_Professional_M1132_MFP-arm64.ppd

[ "$(id -u)" -eq 0 ] || { echo "ERROR: run with sudo" >&2; exit 1; }

if lpstat -p "$QUEUE" >/dev/null 2>&1; then
  cancel -a "$QUEUE" 2>/dev/null || true
  lpadmin -x "$QUEUE"
  echo "Queue $QUEUE removed"
fi

rm -rf "$FILTER_DIR"
rm -f "$PPD_DEST"
echo "Filter and PPD removed"
