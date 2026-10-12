# Créditos e licença

Este projeto é distribuído sob a **GNU GPL v2 ou posterior** (ver `LICENSE`), a mesma licença do código de origem.

| Arquivo | Origem | Autor(es) |
|---|---|---|
| `src/rastertozjs.c` | [faradayfury/printer-all](https://github.com/faradayfury/printer-all) @ `b6601e3` (2026-03-14) | faradayfury: reescrita como filtro CUPS do `foo2zjs` |
| `src/zjs.h` | foo2zjs, via printer-all @ `b6601e3` | Rick Richardson |
| `src/zjsdecode.c` | foo2zjs (`zjsdecode.c,v 1.84`), via o espelho [koenkooi/foo2zjs](https://github.com/koenkooi/foo2zjs) @ `e04290d` | Rick Richardson |
| `src/jbig.c`, `jbig.h`, `jbig_ar.c`, `jbig_ar.h` | JBIG-KIT, via foo2zjs / printer-all @ `b6601e3` | Markus Kuhn |
| `ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd` | este projeto (valores do `hp1130.ppd` da HP, do hpcups e do filtro; ver `docs/parametros.md`) | — |
| `scripts/make_testpage.py`, `scripts/make_ppd.py` | este projeto (o PPD é gerado pelo `make_ppd.py`) | — |
| `tools/zjsdump.py`, `tools/zjsmix.py` | este projeto (inspeção e variantes de fluxos ZJS, Fase 5) | — |

Os arquivos de terceiros foram copiados sem modificação, com uma exceção:

- **`src/rastertozjs.c` (Fase 3, 12/10/2026):** o Model padrão passou a vir da macro `DEFAULT_MODEL`, que o `Makefile` define como `2` (`MODEL_HP_PRO`, equivalente a `foo2zjs -z2`). Sem a macro, o padrão continua `MODEL_HP1020`, como no original. Motivo: o CUPS não passa os padrões do PPD ao filtro em `argv[5]`, então um `*DefaultModel` no PPD não chegaria. São 7 linhas, marcadas com `hp-m1132-arm64` no comentário.
- **`src/rastertozjs.c` (revisão da Fase 3, 12/10/2026):** o filtro lê o PPD da fila (`$PPD`): Model por `*cupsModelNumber` e padrões de `Density`/`EconoMode`/`Collate`. O padrão sem PPD passou a ser `MODEL_HP_PRO` no próprio código (o `-D` saiu do Makefile). `EconoMode` aceita `True`/`On`. O tipo de papel usa `cupsMediaType` quando o PPD o define, e o nome `Heavy` passou de 261 para 262 (código da HP), com `MidWeight` 282 e `ExtraHeavy` 283. Cópias: lê `argv[4]` quando `NumCopies` é 1 e, com `Collate`, repete o documento em vez de pedir cópias à impressora. Trechos marcados com `hp-m1132-arm64`.

- **`src/rastertozjs.c` (Fase 5, 12/10/2026):** novo **Model 4 (`MODEL_HP_M1132`)**, agora o padrão, com o fluxo que o filtro Mac da própria HP manda para a M1132: PJL em CRLF com `ENTER LANGUAGE=ZJS`, `START_DOC` só com `DMCOLLATE`, itens da página em ordem de ID com `ECONOMODE` e sem `RET`/`START_PLANE`. O título do job entra no `@PJL JOB NAME` (só ASCII imprimível, sem aspas, até 63 caracteres). Os Models 0–3 não mudaram: a saída do Model 2 é idêntica byte a byte. Motivo: a M1132 trava o USB com o fluxo do Model 2 (ver `docs/parametros.md` §5).

Outras alterações ficam registradas no histórico do git.

Na Fase 1 a base era `rastertoxqx.c` (XQX). Ela foi trocada na Fase 2, quando se confirmou que a M1132 usa ZjStream (ver `docs/parametros.md`).
