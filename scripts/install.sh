#!/bin/bash
# Instala o filtro arm64 e o PPD da HP M1132 e cria a fila M1132_arm64.
# Uso: make && sudo ./scripts/install.sh
# A URI USB é detectada sozinha; para forçar uma: sudo URI='usb://...' ./scripts/install.sh
# Não mexe em nenhuma outra fila. Para desfazer: sudo ./scripts/uninstall.sh
set -euo pipefail

QUEUE=M1132_arm64
DESC="HP M1132 (arm64)"
FILTER_DIR=/Library/Printers/hp-m1132-arm64
FILTER=$FILTER_DIR/rastertozjs
PPD_NAME=HP-LaserJet_Professional_M1132_MFP-arm64.ppd
PPD_DEST=/Library/Printers/PPDs/Contents/Resources/$PPD_NAME
URI_PREFIX='usb://Hewlett-Packard/HP%20LaserJet%20Professional%20M1132%20MFP'

ROOT=$(cd "$(dirname "$0")/.." && pwd)

die() { echo "ERRO: $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "rode com sudo"

# Não compila como root (deixaria arquivos do projeto com dono root).
[ -x "$ROOT/rastertozjs" ] || die "rastertozjs não encontrado; rode 'make' antes (sem sudo)"
[ -f "$ROOT/ppd/$PPD_NAME" ] || die "PPD não encontrado; rode 'make' antes (sem sudo)"
[ "$(lipo -archs "$ROOT/rastertozjs")" = arm64 ] || die "rastertozjs não é arm64"

if [ -z "${URI:-}" ]; then
  # Impressora ligada: pergunta ao backend usb. Desligada: copia da fila antiga.
  URI=$(lpinfo --include-schemes usb -v 2>/dev/null | grep -o "$URI_PREFIX[^ ]*" | head -n1 || true)
  [ -n "$URI" ] || URI=$(lpstat -v 2>/dev/null | grep -o "$URI_PREFIX[^ ]*" | head -n1 || true)
  [ -n "$URI" ] || die "URI USB da M1132 não encontrada; ligue a impressora ou passe URI='usb://...'"
fi
echo "URI: $URI"

# Filtro: root:wheel 755, senão o CUPS recusa rodar.
install -d -o root -g wheel -m 755 "$FILTER_DIR"
install -o root -g wheel -m 755 "$ROOT/rastertozjs" "$FILTER"
codesign --force --sign - "$FILTER"
codesign --verify "$FILTER"
echo "Filtro: $FILTER ($(lipo -archs "$FILTER"))"

install -o root -g wheel -m 644 "$ROOT/ppd/$PPD_NAME" "$PPD_DEST"
echo "PPD: $PPD_DEST"

# Agora o filtro existe, então o cupstestppd consegue validar o PPD inteiro.
cupstestppd -q "$PPD_DEST" || die "cupstestppd reprovou o PPD instalado"

lpadmin -p "$QUEUE" -E -v "$URI" -P "$PPD_DEST" -D "$DESC" -o printer-is-shared=false
echo
lpstat -p "$QUEUE"
echo "Instalado. Rollback: sudo $ROOT/scripts/uninstall.sh"
