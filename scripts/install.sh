#!/bin/bash
# Installs the arm64 filter and the HP M1132 PPD and creates the M1132_arm64 queue.
# Usage: make && sudo ./scripts/install.sh
# The USB URI is detected automatically; to force one: sudo URI='usb://...' ./scripts/install.sh
# No other queue is touched. To undo: sudo ./scripts/uninstall.sh
set -euo pipefail

QUEUE=M1132_arm64
DESC="HP M1132 (arm64)"
FILTER_DIR=/Library/Printers/hp-m1132-arm64
FILTER=$FILTER_DIR/rastertozjs
PPD_NAME=HP-LaserJet_Professional_M1132_MFP-arm64.ppd
PPD_DEST=/Library/Printers/PPDs/Contents/Resources/$PPD_NAME
URI_PREFIX='usb://Hewlett-Packard/HP%20LaserJet%20Professional%20M1132%20MFP'

ROOT=$(cd "$(dirname "$0")/.." && pwd)

die() { echo "ERROR: $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run with sudo"

# Does not build as root (that would leave project files owned by root).
[ -x "$ROOT/rastertozjs" ] || die "rastertozjs not found; run 'make' first (without sudo)"
[ -f "$ROOT/ppd/$PPD_NAME" ] || die "PPD not found; run 'make' first (without sudo)"
[ "$(lipo -archs "$ROOT/rastertozjs")" = arm64 ] || die "rastertozjs is not arm64"

if [ -z "${URI:-}" ]; then
  # Printer on: ask the usb backend. Printer off: copy it from the old HP queue.
  URI=$(lpinfo --include-schemes usb -v 2>/dev/null | grep -o "$URI_PREFIX[^ ]*" | head -n1 || true)
  [ -n "$URI" ] || URI=$(lpstat -v 2>/dev/null | grep -o "$URI_PREFIX[^ ]*" | head -n1 || true)
  [ -n "$URI" ] || die "M1132 USB URI not found; turn the printer on or pass URI='usb://...'"
fi
echo "URI: $URI"

# Filter: root:wheel 755, otherwise CUPS refuses to run it.
install -d -o root -g wheel -m 755 "$FILTER_DIR"
install -o root -g wheel -m 755 "$ROOT/rastertozjs" "$FILTER"
codesign --force --sign - "$FILTER"
codesign --verify "$FILTER"
echo "Filter: $FILTER ($(lipo -archs "$FILTER"))"

install -o root -g wheel -m 644 "$ROOT/ppd/$PPD_NAME" "$PPD_DEST"
echo "PPD: $PPD_DEST"

# The filter exists now, so cupstestppd can validate the whole PPD.
cupstestppd -q "$PPD_DEST" || die "cupstestppd rejected the installed PPD"

lpadmin -p "$QUEUE" -E -v "$URI" -P "$PPD_DEST" -D "$DESC" -o printer-is-shared=false
echo
lpstat -p "$QUEUE"
echo "Installed. Rollback: sudo $ROOT/scripts/uninstall.sh"
