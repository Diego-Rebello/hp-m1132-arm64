#!/usr/bin/env python3
"""Monta variantes de teste de um fluxo ZJS (só a 1ª página).
Uso: zjsmix.py entrada.zjs saida.zjs [--hp-pjl] [--no-plane] [--doc-hp] [--no-ret]"""
import struct, sys

src, dst, *flags = sys.argv[1:]
d = open(src, "rb").read()
p = d.find(b"JZJZ")
pjl, p = d[:p], p + 4
chunks = []
while d[p:p + 4] != b"\x1b%-1":
    size, typ = struct.unpack(">II", d[p:p + 8])
    chunks.append((typ, d[p:p + size]))
    p += size
# só até o primeiro END_PAGE
out = []
for typ, c in chunks:
    out.append((typ, c))
    if typ == 3:
        break
out.append((1, struct.pack(">IIIHH", 16, 1, 0, 0, 0x5a5a)))  # END_DOC

def chunk(typ, items, rsvd):
    body = b"".join(struct.pack(">IHBBI", 12, i, 1, 0, v) for i, v in items)
    return struct.pack(">IIIHH", 16 + len(body), typ, len(items), rsvd, 0x5a5a) + body

def items_of(c):
    n = struct.unpack(">I", c[8:12])[0]
    return [struct.unpack(">IHBBI", c[16 + 12 * k:28 + 12 * k])[1::3] for k in range(n)]

res = []
for typ, c in out:
    if "--no-plane" in flags and typ in (9, 10):
        continue
    if "--doc-hp" in flags and typ == 0:
        c = chunk(0, [(1, 0)], 0x0c)
    if typ == 2 and ("--no-ret" in flags or "--doc-hp" in flags):
        it = [(i, v) for i, v in items_of(c) if not ("--no-ret" in flags and i == 22)]
        if "--doc-hp" in flags:
            it.sort()
        c = chunk(2, it, 12 * len(it))
    res.append(c)

if "--hp-pjl" in flags:
    pjl = (b"\x1b%-12345X@PJL USTATUS JOB=ON\r\n@PJL USTATUS PAGE=ON\r\n"
           b"@PJL USTATUS DEVICE=ON\r\n@PJL INFO STATUS\r\n@PJL JOB NAME=teste\r\n"
           b"@PJL SET DENSITY = 3\r\n@PJL SET JAMRECOVERY = OFF\r\n@PJL ENTER LANGUAGE=ZJS\r\n")
    tail = b"\x1b%-12345X@PJL EOJ\r\n\x1b%-12345X"
else:
    tail = b"\x1b%-12345X@PJL EOJ\n\x1b%-12345X"
open(dst, "wb").write(pjl + b"JZJZ" + b"".join(res) + tail)
