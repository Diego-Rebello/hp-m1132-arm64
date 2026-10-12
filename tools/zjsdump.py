#!/usr/bin/env python3
"""Lists the chunks and items of a ZJS stream (big-endian). Usage: zjsdump.py file.zjs"""
import struct, sys

T = {0: "START_DOC", 1: "END_DOC", 2: "START_PAGE", 3: "END_PAGE", 4: "JBIG_BIH",
     5: "JBIG_BID", 6: "END_JBIG", 7: "SIGNATURE", 8: "RAW_IMAGE", 9: "START_PLANE",
     10: "END_PLANE", 11: "2600N_PAUSE", 12: "2600N"}
I = {0: "PAGECOUNT", 1: "DMCOLLATE", 2: "DMDUPLEX", 3: "DMPAPER", 4: "DMCOPIES",
     5: "DMDEFAULTSOURCE", 6: "DMMEDIATYPE", 7: "NBIE", 8: "RESOLUTION_X", 9: "RESOLUTION_Y",
     10: "OFFSET_X", 11: "OFFSET_Y", 12: "RASTER_X", 13: "RASTER_Y", 14: "COLLATE",
     15: "QUANTITY", 16: "VIDEO_BPP", 17: "VIDEO_X", 18: "VIDEO_Y", 19: "INTERLACE",
     20: "PLANE", 21: "PALETTE", 22: "RET", 23: "ECONOMODE", 99: "PAD"}

data = open(sys.argv[1], "rb").read()
p = data.find(b"JZJZ")
if p < 0:
    sys.exit(f"{sys.argv[1]}: no JZJZ header (not a ZJS stream?)")
print(f"PJL ({p} bytes): {data[:p]!r}")
p += 4
while p + 16 <= len(data):
    if data[p:p + 9] == b"\x1b%-12345X":
        print(f"UEL @{p}; rest: {data[p:p + 120]!r}")
        break
    size, typ, items, res, sig = struct.unpack(">IIIHH", data[p:p + 16])
    name = T.get(typ, hex(typ))
    extra = "" if sig == 0x5a5a else f" sig={sig:#x}!"
    if typ in (5,):
        print(f"@{p} {name} size={size}")
    else:
        print(f"@{p} {name} size={size} items={items} reserved={res:#x}{extra}")
        q = p + 16
        for _ in range(items):
            isz, iid, ityp, prm, val = struct.unpack(">IHBBI", data[q:q + 12])
            print(f"    {I.get(iid, hex(iid))}={val} (type={ityp} size={isz})")
            q += isz
        if typ == 4:
            print(f"    BIH: {data[q:p + size].hex()}")
    if size < 16:
        print("invalid size; stopping"); break
    p += size
else:
    print(f"end of file @{p} (total {len(data)})")
