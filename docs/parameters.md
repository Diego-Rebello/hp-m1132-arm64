# HP LaserJet Professional M1132 MFP: protocol and parameters

Gathered in Phase 2 (2026-10-12). All of it was done without the printer, by running `grep` over primary sources.

## 1. Protocol: **ZjStream (ZJS)**, not XQX

The Phase 0 assumption ("the M1132 is XQX, like the P1102/M1212nf") was wrong: the P1102 itself is ZJS.

| # | Source | What it shows |
|---|---|---|
| 1 | **HP's own Mac driver**, already installed: `/Library/Printers/hp/laserjet/M1130_1210series/HPM1210_1130Raster.bundle/Contents/MacOS/rastertozjs` (PPD `hp1130.ppd.gz`, which lists the M1132 in `*1284DeviceID`) | `strings` shows `JZJZ`, `@PJL ENTER LANGUAGE=%s` and `[ZJS::Stream]`, and **no** `XQX`. For comparison, the P1005 filter (`hplaserjetzjs.bundle/.../rasterToHPZJS`), which is XQX, contains `,XQX` and `ENTER LANGUAGE=ACL`. **This is the decisive evidence.** |
| 2 | HPLIP 3.12.11, `prnt/drv/hpcups.drv.in` (mirror `Distrotech/hplip` @ `f0011f2`) | The M1132 (`ModelName "HP LaserJet Professional m1132 MFP"`, line 15967) is in the `hpPrinterLanguage "ljzjstream"` group, **the same one as the P1102/P1102w/P1106/P1107/P1109**. The `LJZjStream.cpp` encapsulator writes `@PJL ENTER LANGUAGE=ZJS` + `JZJZ`. XQX (`ljzxstream`, which writes `,XQX`) is used only for the M1005, P1005–P1008, P1505 and P2014. |
| 3 | HPLIP 3.12.11, `data/models/models.dat` | `[hp_laserjet_professional_m1132_mfp]`: `tech-class=LJZjsMono`, `fw-download=False`, `plugin=1`, `plugin-reason=65`. The P1102 and the M1212nf have the same `tech-class`, so this field alone does not tell ZJS from XQX. **No firmware download is needed.** |
| 4 | foo2zjs (mirror `koenkooi/foo2zjs` @ `e04290d`): `foo2xqx.1in`, `README.in` | The M1132 **does not appear** in any family. The P1102 is in foo2zjs; the M1212nf is listed as XQX. The P1102 PPD in printer-all uses `foo2zjs-wrapper -z2` and `CMD:ZJS,PJL,ACL,HTTP`. |

Noted contradiction: foo2zjs says the M1212nf is XQX, but HP's Mac driver for the M1130/**M1210** series is ZJS. The firmware may accept both. It makes no difference here, because this project follows HP's own driver.

> **Corrected in Phase 5:** the protocol is indeed ZJS, but the M1132 **rejects the Model 2 (P1102) structure**. Model 4 was added, copied from the stream HP's filter produces. See §5.

**Decision:** switch the base to `rastertozjs.c` (printer-all @ `b6601e3`) with **Model 2 = `MODEL_HP_PRO`**, the equivalent of `foo2zjs -z2` (P1102/P1566/P1606dn). Offline validation uses `zjsdecode` (foo2zjs).

## 2. PPD parameters (Phase 3)

Sources: **HP** = `hp1130.ppd.gz` (HP's Mac driver for the M1130 series), **hpcups** = the P1102/M1132 group in `hpcups.drv`, **foomatic** = printer-all's `PPD/HP-LaserJet_Pro_P1102.ppd`, **filter** = `src/rastertozjs.c`.

### Resolution
- **600×600 dpi only.** hpcups has Normal and Draft, both `HWResolution[600 600]`. In the HP PPD, "FastRes 600" and "FastRes 1200" also send `HWResolution[600 600]` (1200 is only internal enhancement).
- The 1200×600 mode in the plan **was dropped**.
- The filter requires 1-bit raster: `cupsColorSpace 3` (= `CUPS_CSPACE_K`: bit 1 = black, checked in `cups/raster.h`), `cupsBitsPerColor 1`. In hpcups: `<</cupsColorSpace 3/cupsBitsPerColor 1/cupsRowCount 1/cupsRowStep 2>>`.

### Paper and margins (`ImageableArea`, in pt)
The filter recognizes only these names (`map_paper_code`); any other name becomes Letter in the stream:
`Letter, Legal, Executive, A4, A5, A6, B5, Env10, EnvDL, EnvC5, EnvB5, EnvMonarch, Postcard`.

| Paper | Size (pt) | HP | foomatic | hpcups (left/bottom/right/top) |
|---|---|---|---|---|
| A4 | 595.28 × 841.89 | 12 12 583 830 | 11.34 11.34 583.66 830.66 | 18 / 15.5 / 18 / 15.5 |
| Letter | 612 × 792 | 12 12 600 780 | 11.34 … 600.66 780.66 | 12 on all sides |
| Legal | 612 × 1008 | 12 12 600 996 | 11.34 … 600.66 996.66 | 12 |
| Executive | 522 × 756 | 12 12 510 744 | 11.34 … 510.66 744.66 | 12 |
| A5 | 420 × 595 | 12 12 408 583 | 11.34 … 408.66 583.66 | 12 |
| A6 | 298 × 420 | — | 11.34 … 285.66 408.66 | 12 |
| B5 (JIS) | 516 × 729 | — | 11.34 … 486.66 696.66 ⚠️ | 18 / 15.5 |
| Env10 | 297 × 684 | 12 12 285 672 | 11.34 … 285.66 672.66 | 12 |
| EnvDL | 312 × 624 | 12 12 300 612 | 11.34 … 299.66 611.66 | 18 / 15.5 |
| EnvC5 | 459 × 649 | — | 11.34 … 447.66 637.66 | 12 |
| EnvMonarch | 279 × 540 | — | 11.34 … 267.66 528.66 | 18 / 15.5 |

- **Proposal:** use **HP's margins: 12 pt (4.23 mm) on every side**. They come from the official driver and sit between foomatic (4 mm) and hpcups (up to 6.35 mm). The Phase 5 ruler page confirmed them.
- ⚠️ The foomatic B5 (498 × 708) is ISO B5, not JIS. To be checked in Phase 3.
- Custom paper size limits (hpcups): 3×5 in to 17×36 in (the M1132's real maximum is Legal). Custom sizes are left for later; the filter would map them to Letter.

### Paper type (`MediaType`)
The filter reads the **name** in `header.MediaType` (not `cupsMediaType`). Names accepted with Model ≥ 1:
`Plain`, `Transparency`, `Glossy`, `Envelope`, `Letterhead`, `ThickStock`, `Cardstock`, `Labels`, `Rough`, `Heavy`, `Light`, `Vellum`, `Color`, `Preprinted`, `Prepunched`, `Recycled`. Any other name becomes plain paper.
- The filter's codes match HP's (`Light` 258, `Labels` 265, `Envelope` 267, `Letterhead` 513 …). The exception is `Heavy`: the filter sends 261, HP sends 262 ("Heavy 111–130 g").
- ✅ **Fixed in the Phase 3 review:** the PPD sends HP's code in `cupsMediaType` (`Heavy` 262, `ExtraHeavy` 283, `MidWeight` 282 …) and the filter uses that number directly. The names are only a fallback, with `Heavy` also fixed to 262.
- **Proposal:** `Plain` (default), `Light`, `Heavy`, `ThickStock`, `Transparency`, `Labels`, `Envelope`, `Letterhead`, `Recycled`, `Rough`. **Final:** those plus `MidWeight`, with `ThickStock` renamed to `ExtraHeavy`. The list lives in `scripts/make_ppd.py`.

### Density, toner saving and quality
- `Density`: the filter calls `atoi()`, so the choices must be named **`1`…`5`** (default `3`). Foomatic's `Density1`… names would give 0 and be ignored. HP also uses 1–5 with default 3.
- `EconoMode`: Boolean with `True`/`False` choices (standard PPD spec, as in HP's PPD). The filter accepts `True`/`On`/`Yes`/`1`, case-insensitive.
- `Quality=draft` also turns on toner saving, so it needs no option of its own.

### Tray (`InputSlot`)
- The M1132 has a single tray. HP only offers `Manual` → `MediaPosition 4`, which the filter maps to `DMBIN_MANUAL`. hpcups uses `Auto`=7 and `Manual`=2.
- **Proposal:** follow HP (`MediaPosition 4`) or not expose the option at all (the filter defaults to `DMBIN_AUTO`). Phase 5 decides whether it matters.

### Copies
- The filter sends `ZJI_DMCOPIES = header.NumCopies` (the printer makes the copies). HP uses `*cupsManualCopies: False`; foomatic uses `True`.
- ✅ **Phase 3 review:** the printer can only make **uncollated** copies (1,1,2,2). The PPD gained a `Collate` option (default `True`); with it, the filter keeps the pages in memory and repeats the document, with `DMCOPIES=1`. The copy count comes from `header.NumCopies` or, if that is 1, from `argv[4]` (never multiplied).
- ✅ **Phase 6:** confirmed on the real queue: `Collate` on gives 1,2,1,2 and off gives 1,1,2,2.

### ⚠️ Model: the filter needed a change
- By default the filter uses **Model 1 (HP1020)**, and it only changes that through a `Model=0..3` job option. CUPS does not put PPD defaults in `argv[5]`, so a `*DefaultModel: 2` in the PPD **would never reach** the filter.
- ✅ **Done in Phase 3:** a minimal patch in `src/rastertozjs.c` so that the default is `MODEL_HP_PRO` (for example `-DDEFAULT_MODEL=2` in the Makefile with `#ifndef` in the code), recorded in `NOTICE.md`.
- ✅ **Phase 3 review:** the filter now opens the queue's PPD (`$PPD`) and reads `*cupsModelNumber` and the `Density`, `EconoMode` and `Collate` defaults (`ppdMarkDefaults` + `cupsMarkOptions`), so `lpadmin -o Density=5` now takes effect. `-DDEFAULT_MODEL` was removed from the Makefile; the default without a PPD is `MODEL_HP_PRO` in the code, with `#error` outside 0–3.

## 3. Test page

`python3 scripts/make_testpage.py test` writes:
- `test/ruler-a4.pdf` (2 pages) and `test/ruler-letter.pdf` (1 page);
- mm rulers measured from the edge on all 4 sides, rectangles at 2/4/6 mm, a gray scale from 10% to 100%, and lines from 0.1 to 1 pt.

A4 at 600 dpi is 4961 × 7016 px for the whole page. What goes to the printer is smaller (see §4).

## 4. Offline pipeline results (Phase 3)

### The macOS raster covers only the printable area, and that is correct
- macOS's `cgpdftoraster` rasterizes only the `ImageableArea`. With 12 pt margins, A4 becomes **4761 × 6816 px** (= (595.28 − 24) × 600/72 by (841.89 − 24) × 600/72), not 4961 × 7016. Header: `cupsImagingBBox 12 12 583.28 829.89`, `Margins 12 12`.
- On Linux (Ghostscript) the raster would be the whole page. But **hpcups sends the printer only the printable area**: `LJZjStream.cpp` (HPLIP 3.12.11) writes `ZJI_VIDEO_X/Y` and `ZJI_RASTER_X/Y` from `printable_width`/`printable_height`. So the stream built on macOS has the same shape as HP's driver. Since the margins are symmetric, the printer should center the image. The Phase 5 ruler page confirmed it.
- To check: `./zjsdecode -d out/pg < out/test.zjs` writes one `.pbm` per page (JBIG width rounded up to 128: 4864). The decoded A4 page came out upright, black on white, with the gray scale halftoned and the clipping between the 4 and 6 mm rectangles, as expected.

| Paper | `VIDEO_X × VIDEO_Y` | `DMPAPER` |
|---|---|---|
| A4 | 4761 × 6816 | 9 |
| Letter | 4900 × 6400 | 1 |
| Legal | 4900 × 8200 | 5 |
| Executive | 4150 × 6100 | 7 |
| A5 | 3296 × 4761 | 11 |
| A6 | 2280 × 3296 | 70 |
| B5 (JIS) | 4099 × 5871 | 13 |
| Postcard | 2162 × 3296 | 43 |
| Env10 | 2275 × 5500 | 20 |
| EnvDL | 2398 × 4997 | 27 |
| EnvC5 | 3627 × 5209 | 28 |
| EnvB5 | 3958 × 5705 | 34 |
| EnvMonarch | 2125 × 4300 | 37 |

### Options
- `Density=5 EconoMode=on MediaType=Heavy` with 2 copies → `@PJL SET DENSITY=5`, `@PJL SET ECONOMODE=ON`, `ZJI_ECONOMODE 1`, `ZJI_DMMEDIATYPE 261`, `ZJI_DMCOPIES 2` on every page. `MediaType` and the copy count arrive through the raster header; `Density` and `EconoMode` arrive through `argv[5]`. *(before the review; now `Heavy` → 262)*
- With copies made by the printer (`cupsManualCopies: False`) and `ZJI_DMCOLLATE 0`, a 2-page document with 2 copies should come out **1,1,2,2** (uncollated). *(superseded: see Copies above; with `Collate=True` the output is 1,2,1,2)*

### PPD
- `cupstestppd`: the only errors are "missing cupsFilter/cupsFilter2 file", because the filter is only installed in Phase 4. With `-I filters` it gives PASS with 1 warning: `EnvB5` should be named `EnvISOB5`. **Kept**, because the filter only recognizes `EnvB5`.
- `*cupsFilter2` uses the vendor type `application/vnd.hp-zjs` as its destination, as in the CUPS documentation example. `application/vnd.cups-printer`, which was in the plan, does not exist on macOS. `*cupsFilter` is kept only for compatibility.
- B5 is **JIS** (182 × 257 mm), which is the filter's `DMPAPER_B5` = 13 and HP's `B5JIS`.

### Limitation of macOS `cupsfilter`
- `cupsfilter -m printer/foo` **ignores the PPD's filters** and produces PostScript (`cgpdftops → pstops`), even with HP's own `hp1130.ppd`. So the offline test stops at the raster, and the filter is run by hand with the options in `argv[5]`, as `cupsd` would do. The full chain can only be tested for real with an actual queue (Phases 4/5).

### How to repeat
```sh
PPD=ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd
cupsfilter -p $PPD -m application/vnd.cups-raster [-o PageSize=Letter -o MediaType=Heavy -o copies=2] test/ruler-a4.pdf > out/test.ras
./rastertozjs 1 u t 1 "Density=5 EconoMode=on" out/test.ras > out/test.zjs
./zjsdecode < out/test.zjs | grep -E "PJL SET|VIDEO|DMPAPER|DMMEDIA|DMCOPIES"
```

Note: `zjsdecode` cannot read the Model 4 stream (see §5). For Model 4, use `python3 -I tools/zjsdump.py out/test.zjs`, or pass `Model=2` in `argv[5]` to get a stream `zjsdecode` can decode.

## 5. Real test (Phase 5): the M1132 does not accept the P1102 stream

### Symptom
With Model 2, the arm64 filter ran without errors (the `badarch` problem was solved), but the `usb` backend failed: `USB class driver WritePipe returned e00002ed` (*not responding*), `Sent 0 bytes`, and the queue stopped. Turning the printer off and on did not help.

### How the cause was found
1. **USB works:** a 42-byte raw job (`@PJL INFO STATUS`) was accepted, and the printer answered with its status.
2. **HP reference:** HP's Intel filter (`HPM1210_1130Raster.bundle/.../rastertozjs`) runs in Terminal under Rosetta with `PPD=out/hp1130.ppd DEVICE_URI=usb://…?serial=FAKE` (without `DEVICE_URI` it segfaults in `initReadThread`). It writes the whole job and then waits for status on the back channel (killed after 60 s). Sent raw, that stream **was accepted by the printer**.
3. **Bisection with `tools/zjsmix.py`** (builds variants) and `tools/zjsdump.py` (lists chunks and items):
   - our ZJS with HP's PJL → **rejected** (the PJL is not the cause);
   - our JBIG inside HP's structure → **accepted and printed perfectly**.

### Differences (Model 2 → Model 4)
| | Model 2 (P1102) | Model 4 (M1132 = HP's filter) |
|---|---|---|
| PJL | `LF`, `@PJL JOB`, `SET ECONOMODE`, `SET RET`, `USTATUS TIMED = 30`, `JOBATTR` + `\0`, UEL before `JZJZ` | `CRLF`, `USTATUS JOB/PAGE/DEVICE=ON`, `INFO STATUS`, `JOB NAME=<title>`, `SET DENSITY = n`, `SET JAMRECOVERY = OFF`, **`ENTER LANGUAGE=ZJS`** |
| START_DOC | `DMCOLLATE`, `DMDUPLEX` | `DMCOLLATE` only (reserved `0x0c`) |
| START_PAGE | items out of order, `RET=1`, `ECONOMODE` only when on | 13 items in ID order: `DMPAPER, DMCOPIES, DMDEFAULTSOURCE, DMMEDIATYPE, NBIE, RESOLUTION_X/Y, RASTER_X/Y, VIDEO_BPP, VIDEO_X/Y, ECONOMODE` |
| Plane | `START_PLANE(4)` … `END_PLANE` | no plane |
| JBIG | same (`MX=16`); HP uses `MX=0`, but ours printed correctly | — |

We did not test which single difference stalls the printer (every accepted test uses a sheet of paper). Model 4 follows HP in everything except the JBIG parameters.

### Notes
- foo2zjs's `zjsdecode` cannot read the Model 4 stream (it expects `JZJZ` right after the UEL). Use `python3 -I tools/zjsdump.py file.zjs`.
- HP's filter does flow control over the back channel (it waits for each page's status). Ours does not: USB applies back-pressure on its own, and a 2-page job printed without trouble.
- The page printed from HP's stream came out with a black background and stretched, because the raster had been made for our PPD (different polarity and options). That does not matter: it only served to prove the structure is accepted.
