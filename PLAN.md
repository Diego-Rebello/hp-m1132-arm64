# HP LaserJet M1132 MFP on macOS 27 (Apple Silicon): plan

Goal: get the HP LaserJet Professional M1132 MFP (USB) printing again with a **native arm64** CUPS filter, without Rosetta, Ghostscript or HP's Intel drivers.

---

## How to use this plan (5-hour and weekly usage limits)

- **One phase per session.** Each phase is sized to fit comfortably in a 5-hour window and ends at a safe stopping point (nothing is left half-done).
- **Start each session with:** `/clear` and then:
  > `continue PLAN.md in ~/hp-m1132-arm64, phase N`
- **At the end of each phase:** tick the checkboxes, fill in the "Log" at the bottom and `git commit`. That is what makes it possible to resume without re-explaining everything.
- **Saving usage:**
  - Do not paste or ask to read large files in full (PPDs are 30 KB+; CUPS logs are huge). Use `grep`/`tail` with filters.
  - Phases marked 🟢 **light** can be done at the end of a window or when the weekly limit is tight. 🟡 **medium** phases need a roomier window.
  - If the limit runs out mid-phase, stop at the last completed step, note it in the Log and commit.
- **Suggested schedule:** Week 1 → Phases 1–3 (no `sudo`, nothing touched on the system). Week 2 → Phases 4–5 (install and real test). Week 3+ → Phases 6–7 (finishing and publishing), no rush.

---

## Context gathered (Phase 0, done 2026-10-12)

- Mac: Apple Silicon (`arm64`), macOS 27.0.1 (26A434).
- Existing queue: `HP_LaserJet_Professional_M1132_MFP`
  URI: `usb://Hewlett-Packard/HP%20LaserJet%20Professional%20M1132%20MFP?serial=…`
- **Cause of the failure:** HP's filters (`usbink`, `rastertozjs` in `/Library/Printers/hp/laserjet/M11_M12_M13series/hpRaster.bundle`) are `x86_64 i386` only. macOS 27's CUPS refuses to start them: the log shows `com.apple.badarch-error` and `Broken pipe`, with 0 bytes sent. Rosetta is active and the filter runs in Terminal, so the block is in CUPS.
- No installed HP driver has an arm64 build (`M1130_1210series`, `hplaserjetzjs`, `p1100…`, `cp1020…`: all Intel).
- The existing queue uses the **wrong** PPD ("HP LaserJet Pro M12"), not the M1130/M1210 series one. It does not matter for the solution, but it explains some odd behavior in the past.
- Chosen base: [faradayfury/printer-all](https://github.com/faradayfury/printer-all) (GPL-2.0), filter ~~`rastertoxqx.c`~~ → **`rastertozjs.c`** since Phase 2 (a rewrite of foo2zjs, also GPL-2.0). The notes below apply to both filters (same author, same structure).
  - ✅ `rastertoxqx` builds natively for arm64 with no warnings (`clang … -lcups -lcupsimage`).
  - ✅ Simple code: reads CUPS raster from its input and writes XQX to its output, with no network access and no `exec`. Options read: `Density`, `EconoMode`, `PageSize`, `MediaType`. Requires **1 bit per pixel** raster.
  - ❌ **Every PPD in the repo calls `foomatic-rip`** (which does not exist on macOS). None of them uses the repo's own filters, so **we need to write our own PPD.**
  - ❌ Its `install.sh` copies to `/usr/libexec/cups/filter/` (protected by SIP). **Do not use it.** Install under `/Library/Printers/…` with an absolute path in `*cupsFilter`, as HP does.
  - ⚠️ The M1132 is not on its list; only the P1007 was tested on hardware. ~~According to foo2xqx, the M1132 is XQX~~ → **Corrected in Phase 2: the M1132 is ZjStream (ZJS)**, the same family as the P1102. The base became `rastertozjs.c`, Model 2. No firmware needed. Details in `docs/parameters.md`.
- Tools available without `sudo`: `clang`, `make`, `git`, `gh` (logged in as `Diego-Rebello`), `cupsfilter`, `cupstestppd`.
- The printer-all copy used for the analysis was in Claude's temporary folder (gone after a reboot). Phase 1 clones it again into the project.

---

## Phase 1: Set up the local project 🟢 light (~30 min)

Goal: a lean local repository that builds and has the correct license. **Nothing is installed on the system.**

- [x] Clone `printer-all` into `vendor/printer-all-src/` (git-ignored) and note the commit hash used (`b6601e3`).
- [x] Copy only what is needed to `src/`: `rastertoxqx.c`, `foo2zjs/jbig.c`, `jbig.h`, `jbig_ar.c`, `jbig_ar.h`, `xqx.h`, `xqxdecode.c`.
- [x] `LICENSE` (GPL-2.0) + `NOTICE.md` crediting foo2zjs (Rick Richardson) and printer-all (faradayfury), with the source commit.
- [x] `Makefile` with the `rastertoxqx`, `xqxdecode`, `clean` and `check` targets (`lipo -archs` must give `arm64`).
- [x] `.gitignore` (binaries, `vendor/`, `out/`).
- [x] `make && make check` with no warnings. (`-Wextra` shows 5 harmless warnings; kept `-Wall`, as upstream does.)
- [x] Commit: `Fase 1: estrutura e filtro XQX compilando`.

**Done when:** `make check` prints `arm64` and the repo has only sources + docs.

---

## Phase 2: Confirm the protocol and validate the filter offline 🟡 medium (~1–1.5 h)

Goal: be sure (without the printer) which protocol the M1132 speaks (XQX or ZJS) and that the filter produces a coherent stream.

- [x] Confirm the M1132's family from primary sources, without reading whole files:
  - `foo2xqx` model list (man page / foo2zjs's `foo2xqx.c`): the M1132 is not there;
  - the M1132 entry in HPLIP's `models.dat`: `LJZjsMono`, which does not decide it. What decided it was `hpcups.drv` (`ljzjstream`) and **HP's own Mac filter** (`JZJZ`, no XQX).
  - Sources listed in `docs/parameters.md` §1.
- [x] The M1132 is **ZjStream (ZJS)**: base switched to `rastertozjs.c` (Model 2 = `-z2`, like the P1102) and Phase 1 redone (`rastertozjs` + `zjsdecode`, arm64, no warnings).
- [x] Parameters extracted (HP `hp1130.ppd`, hpcups, foomatic P1102, filter code) → `docs/parameters.md` §2.
- [x] Test PDF: `scripts/make_testpage.py` → `test/ruler-a4.pdf` (2 pages) and `test/ruler-letter.pdf`.
- [x] Commit: `Fase 2: M1132 é ZJS; base trocada para rastertozjs`.

**Done when:** protocol confirmed and parameters written down in `docs/parameters.md`.

---

## Phase 3: Write the PPD and test the pipeline without sudo 🟡 medium (~1–1.5 h)

Goal: our own validated PPD and the full pipeline (PDF → raster → ZJS) working **to a file**. The values are in `docs/parameters.md` §2; the results in §4.

- [x] **Minimal filter patch:** `DEFAULT_MODEL` with `#ifndef` in `src/rastertozjs.c` and `-DDEFAULT_MODEL=2` in the `Makefile`. Recorded in `NOTICE.md`.
- [x] `ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd` with:
  - `*cupsFilter2: "application/vnd.cups-raster application/vnd.hp-zjs 0 /Library/Printers/hp-m1132-arm64/rastertozjs"` (+ the equivalent `*cupsFilter`). ~~`application/vnd.cups-printer`~~ does not exist on macOS; a vendor type is used instead, as the CUPS documentation says;
  - `*cupsModelNumber: 2`, `*1284DeviceID: "MFG:Hewlett-Packard;MDL:HP LaserJet Professional M1132 MFP;CMD:ZJS,PJL,ACL;"`;
  - `ColorModel` fixed to Gray (`cupsColorSpace 3`, `cupsBitsPerColor 1`, `cupsColorOrder 0`);
  - `Resolution` 600x600 only;
  - 13 sizes (A4 default, Letter, Legal, Executive, A5, A6, B5 JIS, Postcard, Env10, EnvDL, EnvC5, EnvB5, EnvMonarch), 12 pt margins;
  - `MediaType` (10 types, `Plain` default), `Density` `1`–`5` (default 3), `EconoMode` Boolean `off`/`on`, `*cupsManualCopies: False`.
- [x] `cupstestppd`: fails only on "missing cupsFilter file" (the filter is installed in Phase 4). With `-I filters`, PASS + 1 warning (`EnvB5` ≠ `EnvISOB5`, kept because that is the name the filter recognizes).
- [x] Pipeline to a file: `cupsfilter … -m application/vnd.cups-raster` → `./rastertozjs` → `./zjsdecode` with coherent START_DOC / START_PAGE / JBIG / END_PAGE / END_DOC; `zjsdecode -d` recovers the right image.
  - ⚠️ macOS `cupsfilter -m printer/foo` ignores the PPD's filters (even HP's) and produces PostScript. The full chain can only be tested with the real queue.
- [x] A4 with 2 pages, Letter, all 13 sizes (correct `DMPAPER` for each) and `Density=5 EconoMode=on MediaType=Heavy` with 2 copies.
- [x] Commit: `Fase 3: PPD + pipeline validado offline`.

**Done when:** `zjsdecode` decodes the pages without errors and the dimensions match A4 at 600 dpi. ✅ They are **4761×6816 px** (the printable area only, as hpcups sends it), not the 4961×7016 of the whole page that was expected. See `docs/parameters.md` §4.

---

## Phase 4: Install and create a new queue 🟢 light (~30 min) ⚠️ needs `sudo`

Goal: install without touching the old queue, with a one-command rollback.

Claude does not type passwords. `sudo` commands are handed over ready to run **in Terminal.app**, starting with `cd ~/hp-m1132-arm64 && sudo …` (the `! sudo` prefix only works in the Claude Code prompt, not in zsh).

- [x] `scripts/install.sh` (reviewed before running). Usage: `make && sudo ./scripts/install.sh`
  - checks that `rastertozjs` is already built and is arm64 (does not build as root);
  - `/Library/Printers/hp-m1132-arm64/rastertozjs`, owned by `root:wheel`, `755` (CUPS refuses filters writable by other users);
  - `codesign --force --sign -` on the binary + `codesign --verify`;
  - PPD in `/Library/Printers/PPDs/Contents/Resources/` (`root:wheel 644`), validated with `cupstestppd` once the filter is in place;
  - URI detected by `lpinfo --include-schemes usb` or, if the printer is off, copied from the old queue. `URI=…` forces another one. The serial number is not in the script.
- [x] `scripts/uninstall.sh` (rollback: cancels jobs and removes the new queue, the filter and the PPD).
- [x] **New queue** `M1132_arm64` created by `install.sh` itself (`lpadmin -p M1132_arm64 -E -v <URI> -P <ppd> -D "HP M1132 (arm64)" -o printer-is-shared=false`). The "Printer drivers are deprecated" warning from `lpadmin -P` is expected and blocks nothing.
- [x] The old queue **was not removed** (it stays idle).
- [x] Commit: `Fase 4: scripts de instalação`.

**Done when:** `lpstat -p M1132_arm64` shows the queue enabled and `lipo -archs` on the installed filter gives `arm64`. ✅ Queue idle and enabled, filter `arm64` with an ad hoc signature, `device-uri` identical to the old queue's.

---

## Phase 5: Real test on the printer 🟡 medium (~1 h, depends on the result)

Goal: a correctly printed page.

- [x] Printer on, USB connected, A4 paper.
- [x] `lp -d M1132_arm64 test.pdf`
- [x] Look only at the relevant log lines: `grep "Job <n>" /var/log/cups/error_log | grep -iE "error|rastertozjs|badarch|sent|PAGE" | tail -30`.
- [x] Troubleshooting tree (the actual failure was a different one: USB stalled on the Model 2 stream; see the Log and `docs/parameters.md` §5):
  | Symptom | Likely cause | Action |
  |---|---|---|
  | `badarch` again | wrong binary installed | `lipo -archs` on the installed one; reinstall |
  | "insecure filter" / permissions | filter owner/mode | `chown root:wheel`, `chmod 755` |
  | Sandbox denies execution | path outside the allowed ones | try `/Library/Printers/<folder>/…` like HP; record the exact message |
  | Printer does not react / light blinks | wrong protocol | back to Phase 2 and try the other path (`rastertoxqx`, which is in the git history), or `rastertozjs` Model 1 |
  | Prints garbage / blank page | page/resolution parameters | compare with `zjsdecode` and adjust the PPD |
  | Margin clipped / shifted | `ImageableArea`, or the printer does not center the image (macOS sends only the printable area) | measure with the ruler page; adjust the PPD margins |
- [x] Test a real document: **Word**, perfect on A4. ~~Preview and Safari~~ → moved to Phase 6, along with checking the dialog.
- [x] Record the result (including failures) in the Log and commit.

**Done when:** the test page and a real document print correctly. ✅ Ruler page (1 and 2 pages) and a Word document perfect, with **Model 4**.

---

## Phase 6: Finishing touches and daily use 🟢 light (~30–45 min)

- [x] Make `M1132_arm64` the default (`lpoptions -d M1132_arm64`). It already was, for the system and the user. "Use last printer" was also turned off (`defaults write org.cups.PrintingPrefs UseLastPrinter -bool false`), because macOS kept the old queue as the default on other networks. To undo: `defaults delete org.cups.PrintingPrefs UseLastPrinter`.
- [x] Check the options in the macOS print dialog (density, EconoMode, paper type, copies) and **the paper size choice** (Diego missed it in Word; there the size comes from Layout → Size / File → Page Setup, and in Preview/Safari it is under "Paper Size").
- [x] Print a PDF from **Preview** and a page from **Safari** (left over from Phase 5).
- [x] Test multiple copies and multiple pages on the real queue: with `Collate` on it should come out 1,2,1,2; off, 1,1,2,2 (already checked offline in the Phase 3 review). ✅ Jobs 604 (on) and 605 (off) came out in the right order.
- [ ] ⏳ **After ~1 week of trouble-free use (from 2026-10-19):** remove the old queue (macOS still sends "Supplies Levels" jobs to it, which run HP's `usbink`) (`sudo lpadmin -x HP_LaserJet_Professional_M1132_MFP`). Removing HP's Intel drivers is optional and left for a separate decision.
- [x] Commit: `Fase 6: uso diário`.

---

## Phase 7: Publish on GitHub 🟢 light (~30 min)

- [x] Decide: **public or private** → **public**.
- [x] All documentation in English (README, PLAN, NOTICE, `docs/parameters.md`, script comments and messages). Files renamed: `docs/parametros.md` → `docs/parameters.md`, `test/regua-*.pdf` → `test/ruler-*.pdf`.
- [x] README: problem (macOS 27 + Intel filters), install, rollback, tested status (M1132 MFP, macOS 27.0.1, date) and credits/GPL.
- [x] Printer serial number removed before publishing.
- [x] `gh repo create Diego-Rebello/hp-m1132-arm64 --public --source . --push`
- [x] Optional: open an issue or PR on `faradayfury/printer-all` with the M1132 test report and the foomatic-PPD + SIP problem. → [printer-all#4](https://github.com/faradayfury/printer-all/issues/4) (a PR with Model 4 was offered there).

---

## Out of scope (note it, do not do it now)

- **M1132 scanner** (it is a multifunction device): the scanner uses a different path (ICA/eSCL) and is probably Intel-only too. Investigate later, as a separate project.
- Support for other models.

## Plan B (if Phase 5 fails for good)

1. ~~Switch to `rastertoxqx.c` (same repo) or another `rastertozjs` Model if it is a protocol problem.~~ Solved in Phase 5 with Model 4.
2. Port the `hpcups` filter from HPLIP (much heavier: several sessions).
3. Print server on a Raspberry Pi/Linux with `foo2zjs -z2`/HPLIP, shared over IPP (the Mac prints via AirPrint).

---

## Log

| Date | Phase | Result / decisions | Commit |
|---|---|---|---|
| 2026-10-12 | 0 | Diagnosis done (see Context). `rastertoxqx` builds for arm64. Project created in `~/hp-m1132-arm64`. | — |
| 2026-10-12 | 1 | Structure created; `rastertoxqx` and `xqxdecode` build for arm64 with no warnings (`-Wall`). Sources copied unmodified from printer-all@b6601e3. | (this one) |
| 2026-10-12 | 2 | **The M1132 is ZjStream, not XQX.** Decisive evidence: HP's own Mac filter for the M1130/M1210 series contains only ZJS's `JZJZ`/`ENTER LANGUAGE`. hpcups (HPLIP 3.12.11) puts the M1132 in the P1102's `ljzjstream` group; `models.dat` (`LJZjsMono`, no firmware) does not decide it; foo2zjs does not list the M1132. Base switched to `rastertozjs.c` Model 2 (`-z2`); `zjsdecode` comes from foo2zjs (mirror koenkooi@e04290d). Parameters in `docs/parameters.md`: 600×600 only, 12 pt margins (HP), numeric `Density` 1–5, the filter's default Model = 1 → **patch in Phase 3**. Ruler page: `scripts/make_testpage.py`. | (this one) |
| 2026-10-12 | 3 | Own PPD (13 sizes, 12 pt margins, `MediaType`, `Density` 1–5, `EconoMode`) and the `DEFAULT_MODEL=2` patch. Offline pipeline OK: correct `DMPAPER` for all 13 sizes and options checked in the stream; the page decoded by `zjsdecode -d` came out right. **Findings:** (1) on macOS the raster covers only the printable area (A4 = 4761×6816), the same shape hpcups sends; (2) `cupsfilter -m printer/foo` ignores the PPD's filters, so the full chain is only tested on the real queue; (3) `cupsFilter2` now uses `application/vnd.hp-zjs`; (4) 2 copies × 2 pages should come out uncollated (1,1,2,2): to check in Phase 6. | (this one) |
| 2026-10-12 | 3 (review) | Fixes from `/code-review`: HP paper codes via `cupsMediaType` (`Heavy` 262, `ExtraHeavy` 283); `EconoMode` `True`/`False`; the filter reads the queue's PPD (Model, `Density`/`EconoMode`/`Collate` defaults); copies from `argv[4]` and collation done by the filter (`Collate` option); `DEFAULT_MODEL` in the code with `#error`; PPD generated by `scripts/make_ppd.py` (`make ppd`). All checked offline with `zjsdecode`. | (this one) |
| 2026-10-12 | 4 | `install.sh`/`uninstall.sh` written; install run by Diego in Terminal.app (`cd ~/hp-m1132-arm64 && sudo ./scripts/install.sh`; `! sudo` inside zsh does not work). Queue `M1132_arm64` enabled, same USB URI, unshared; filter `root:wheel 755`, arm64, ad hoc; the queue's PPD checks out (`cupsFilter2` → installed filter). Old queue intact. Nothing printed yet: that is Phase 5. | (this one) |
| 2026-10-12 | 5 | **Printing.** With Model 2 the arm64 filter ran without errors (the `badarch` problem was solved), but USB stalled: `WritePipe e00002ed` (*not responding*), 0 bytes sent, even after turning the printer off and on. A raw PJL job was accepted, so USB works. HP's Intel filter ran in Terminal under Rosetta (with a fake `DEVICE_URI`) and the printer accepted its stream. Bisection (`tools/zjsmix.py`, `tools/zjsdump.py`) showed the problem is the **P1102 ZJS structure**, not the PJL: our JBIG inside HP's structure printed perfectly. Added **Model 4 (`MODEL_HP_M1132`)**, now the default and with `cupsModelNumber: 4` in the PPD: PJL with CRLF and `ENTER LANGUAGE=ZJS`, `START_DOC` with `DMCOLLATE` only, items in ID order, no `RET` and no plane. Model 2 is still byte-for-byte identical. Reinstalled by Diego (`sudo ./scripts/install.sh`). Ruler page (1 and 2 pages) and a Word document **perfect** on A4. Left for Phase 6: Preview/Safari and the paper choice in the dialog. CUPS debug log turned on during the test and off at the end. Details in `docs/parameters.md` §5. | (this one) |
| 2026-10-12 | 6 | Daily use OK. `M1132_arm64` was already the default; macOS's `UseLastPrinter` was turned off, since it kept the old queue as the default on other networks. 2 copies of the 2-page ruler: `Collate` on gave 1,2,1,2 and off gave 1,1,2,2. Diego checked the dialog (paper size, Collate, Printer Features: Media Type, Density, EconoMode) and printed from **Preview** and **Safari**: all fine. **Pending:** remove the old queue after ~1 week without problems (from 2026-10-19). | (this one) |
| 2026-10-12 | 7 | Published as a **public** repo: https://github.com/Diego-Rebello/hp-m1132-arm64 (history rewritten before the first push to drop the serial; backup in `refs/original`). Topics added. All documentation translated to English; files with Portuguese names renamed. English README (problem, install, rollback, tested status, credits). Printer serial removed from PLAN.md. | (this one) |
