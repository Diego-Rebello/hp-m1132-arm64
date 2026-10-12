# Créditos e licença

Este projeto é distribuído sob a **GNU GPL v2 ou posterior** (ver `LICENSE`), a mesma licença do código de origem.

| Arquivo | Origem | Autor(es) |
|---|---|---|
| `src/rastertozjs.c` | [faradayfury/printer-all](https://github.com/faradayfury/printer-all) @ `b6601e3` (2026-03-14) | faradayfury: reescrita como filtro CUPS do `foo2zjs` |
| `src/zjs.h` | foo2zjs, via printer-all @ `b6601e3` | Rick Richardson |
| `src/zjsdecode.c` | foo2zjs (`zjsdecode.c,v 1.84`), via o espelho [koenkooi/foo2zjs](https://github.com/koenkooi/foo2zjs) @ `e04290d` | Rick Richardson |
| `src/jbig.c`, `jbig.h`, `jbig_ar.c`, `jbig_ar.h` | JBIG-KIT, via foo2zjs / printer-all @ `b6601e3` | Markus Kuhn |
| `ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd` | este projeto (valores do `hp1130.ppd` da HP, do hpcups e do filtro; ver `docs/parametros.md`) | — |
| `scripts/make_testpage.py` | este projeto | — |

Os arquivos de terceiros foram copiados sem modificação, com uma exceção:

- **`src/rastertozjs.c` (Fase 3, 12/10/2026):** o Model padrão passou a vir da macro `DEFAULT_MODEL`, que o `Makefile` define como `2` (`MODEL_HP_PRO`, equivalente a `foo2zjs -z2`). Sem a macro, o padrão continua `MODEL_HP1020`, como no original. Motivo: o CUPS não passa os padrões do PPD ao filtro em `argv[5]`, então um `*DefaultModel` no PPD não chegaria. São 7 linhas, marcadas com `hp-m1132-arm64` no comentário.

Outras alterações ficam registradas no histórico do git.

Na Fase 1 a base era `rastertoxqx.c` (XQX). Ela foi trocada na Fase 2, quando se confirmou que a M1132 usa ZjStream (ver `docs/parametros.md`).
