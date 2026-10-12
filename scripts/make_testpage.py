#!/usr/bin/env python3
"""Gera PDFs de teste (pagina-regua) sem dependencias externas.

Cada pagina tem:
  - reguas nas 4 bordas, com traco a cada 1 mm (5 mm e 10 mm mais longos),
    medidas a partir da borda do papel: o primeiro traco visivel diz quanto
    a impressora cortou;
  - retangulos a 2, 4 e 6 mm da borda (4 mm = 11.34 pt = margem esperada);
  - escala de cinza (10%..100%) para conferir densidade/halftone;
  - linhas finas (0.1 a 1 pt) para conferir resolucao.

Uso: python3 scripts/make_testpage.py [saida_dir]
Gera regua-a4.pdf (2 paginas) e regua-letter.pdf (1 pagina).
"""
import os
import sys

MM = 72 / 25.4
SIZES = {"A4": (595.28, 841.89), "Letter": (612.0, 792.0)}


def ruler(w, h):
    ops = ["0 G 0.3 w"]
    for edge in ("bottom", "top", "left", "right"):
        length = w if edge in ("bottom", "top") else h
        n = int(length / MM)
        for i in range(1, n):
            p = i * MM
            t = (7 if i % 10 == 0 else 4 if i % 5 == 0 else 2) * MM
            if edge == "bottom":
                ops.append(f"{p:.2f} 0 m {p:.2f} {t:.2f} l S")
            elif edge == "top":
                ops.append(f"{p:.2f} {h:.2f} m {p:.2f} {h - t:.2f} l S")
            elif edge == "left":
                ops.append(f"0 {p:.2f} m {t:.2f} {p:.2f} l S")
            else:
                ops.append(f"{w:.2f} {p:.2f} m {w - t:.2f} {p:.2f} l S")
    # numeros a cada 10 mm na borda de baixo e na esquerda
    for i in range(10, int(w / MM), 10):
        ops.append(f"BT /F1 5 Tf {i * MM - 3:.2f} {8 * MM:.2f} Td ({i}) Tj ET")
    for i in range(10, int(h / MM), 10):
        ops.append(f"BT /F1 5 Tf {8 * MM:.2f} {i * MM - 1.5:.2f} Td ({i}) Tj ET")
    return ops


def insets(w, h):
    ops = []
    for mm, dash in ((2, "[1 1] 0 d"), (4, "[] 0 d"), (6, "[3 2] 0 d")):
        d = mm * MM
        ops.append(f"0.5 w {dash} {d:.2f} {d:.2f} {w - 2 * d:.2f} {h - 2 * d:.2f} re S")
    ops.append("[] 0 d")
    return ops


def body(w, h, label, page, pages):
    cx = 25 * MM
    y = h - 30 * MM
    lines = [
        (16, f"hp-m1132-arm64: pagina-regua {label} ({page}/{pages})"),
        (10, "Tracos a cada 1 mm a partir da borda do papel (longos a 5 e 10 mm)."),
        (10, "Retangulos: pontilhado 2 mm, continuo 4 mm (margem esperada), tracejado 6 mm."),
        (10, f"Papel: {w:.2f} x {h:.2f} pt. A 600 dpi: {round(w / 72 * 600)} x {round(h / 72 * 600)} px."),
    ]
    ops = []
    for size, text in lines:
        ops.append(f"BT /F1 {size} Tf {cx:.2f} {y:.2f} Td ({text}) Tj ET")
        y -= size + 8
    # escala de cinza
    y -= 45
    ops.append(f"BT /F1 9 Tf {cx:.2f} {y + 32:.2f} Td (Cinza 10% a 100%:) Tj ET")
    for i in range(10):
        g = 1 - (i + 1) / 10
        x = cx + i * 15 * MM
        ops.append(f"{g:.2f} g {x:.2f} {y:.2f} {14 * MM:.2f} {8 * MM:.2f} re f")
        ops.append(f"0 g BT /F1 7 Tf {x:.2f} {y - 9:.2f} Td ({(i + 1) * 10}%) Tj ET")
    # linhas finas
    y -= 40
    ops.append(f"BT /F1 9 Tf {cx:.2f} {y:.2f} Td (Linhas de 0.1 a 1.0 pt:) Tj ET")
    for i in range(10):
        lw = (i + 1) / 10
        x = cx + i * 15 * MM
        ops.append(f"0 G {lw:.1f} w {x:.2f} {y - 10:.2f} m {x:.2f} {y - 70:.2f} l S")
    ops.append(f"BT /F1 40 Tf {cx:.2f} {h / 2 - 60:.2f} Td (Pagina {page}) Tj ET")
    return ops


def build(path, label, pages):
    w, h = SIZES[label]
    objs = {1: "<< /Type /Catalog /Pages 2 0 R >>",
            3: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"}
    kids = []
    for p in range(1, pages + 1):
        page_id, content_id = 2 + 2 * p, 3 + 2 * p
        stream = "\n".join(ruler(w, h) + insets(w, h) + body(w, h, label, p, pages)).encode()
        objs[page_id] = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {w} {h}] "
                         f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>")
        objs[content_id] = stream
        kids.append(f"{page_id} 0 R")
    objs[2] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {pages} >>"

    out = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for n in sorted(objs):
        offsets[n] = len(out)
        o = objs[n]
        if isinstance(o, bytes):
            out += f"{n} 0 obj\n<< /Length {len(o)} >>\nstream\n".encode() + o + b"\nendstream\nendobj\n"
        else:
            out += f"{n} 0 obj\n{o}\nendobj\n".encode()
    xref = len(out)
    size = max(objs) + 1
    out += f"xref\n0 {size}\n0000000000 65535 f \n".encode()
    for n in range(1, size):
        out += f"{offsets[n]:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    with open(path, "wb") as f:
        f.write(out)
    print(path)


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "test"
    os.makedirs(outdir, exist_ok=True)
    build(os.path.join(outdir, "regua-a4.pdf"), "A4", 2)
    build(os.path.join(outdir, "regua-letter.pdf"), "Letter", 1)
