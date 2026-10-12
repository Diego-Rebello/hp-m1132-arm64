# Protocolo e parâmetros da HP LaserJet Professional M1132 MFP

Levantamento da Fase 2 (12/10/2026). Tudo foi feito sem a impressora, com `grep` em fontes primárias.

## 1. Protocolo: **ZjStream (ZJS)**, não XQX

A hipótese da Fase 0 ("M1132 é XQX, como a P1102/M1212nf") estava errada: a própria P1102 é ZJS.

| # | Fonte | O que mostra |
|---|---|---|
| 1 | **Driver Mac da própria HP** já instalado: `/Library/Printers/hp/laserjet/M1130_1210series/HPM1210_1130Raster.bundle/Contents/MacOS/rastertozjs` (PPD `hp1130.ppd.gz`, que lista a M1132 no `*1284DeviceID`) | `strings` mostra `JZJZ`, `@PJL ENTER LANGUAGE=%s` e `[ZJS::Stream]`; **nenhum** `XQX`. Para comparar, o filtro da P1005 (`hplaserjetzjs.bundle/.../rasterToHPZJS`), que é XQX, contém `,XQX` e `ENTER LANGUAGE=ACL`. **Esta é a prova decisiva.** |
| 2 | HPLIP 3.12.11, `prnt/drv/hpcups.drv.in` (espelho `Distrotech/hplip` @ `f0011f2`) | A M1132 (`ModelName "HP LaserJet Professional m1132 MFP"`, linha 15967) está no grupo `hpPrinterLanguage "ljzjstream"`, **o mesmo da P1102/P1102w/P1106/P1107/P1109**. O encapsulador `LJZjStream.cpp` escreve `@PJL ENTER LANGUAGE=ZJS` + `JZJZ`. O XQX (`ljzxstream`, que escreve `,XQX`) fica só com M1005, P1005–P1008, P1505 e P2014. |
| 3 | HPLIP 3.12.11, `data/models/models.dat` | `[hp_laserjet_professional_m1132_mfp]`: `tech-class=LJZjsMono`, `fw-download=False`, `plugin=1`, `plugin-reason=65`. A P1102 e a M1212nf têm a mesma `tech-class`, então esse campo sozinho não separa ZJS de XQX. **Não precisa de firmware.** |
| 4 | foo2zjs (espelho `koenkooi/foo2zjs` @ `e04290d`): `foo2xqx.1in`, `README.in` | A M1132 **não aparece** em nenhuma família. A P1102 está no foo2zjs; a M1212nf aparece como XQX. O PPD da P1102 no printer-all usa `foo2zjs-wrapper -z2` e `CMD:ZJS,PJL,ACL,HTTP`. |

Contradição anotada: o foo2zjs diz que a M1212nf é XQX, mas o driver Mac da HP para a série M1130/**M1210** é ZJS. Talvez o firmware aceite os dois; para nós não importa, seguimos o driver da própria HP.

**Decisão:** trocar a base para `rastertozjs.c` (printer-all @ `b6601e3`) com **Model 2 = `MODEL_HP_PRO`**, que equivale a `foo2zjs -z2` (P1102/P1566/P1606dn). Validação offline com `zjsdecode` (foo2zjs).

## 2. Parâmetros para o PPD (Fase 3)

Fontes: **HP** = `hp1130.ppd.gz` (driver Mac da HP para a série M1130), **hpcups** = grupo da P1102/M1132 no `hpcups.drv`, **foomatic** = `PPD/HP-LaserJet_Pro_P1102.ppd` do printer-all, **filtro** = `src/rastertozjs.c`.

### Resolução
- **Só 600×600 dpi.** O hpcups tem Normal e Draft, ambos `HWResolution[600 600]`. Na HP, "FastRes 600" e "FastRes 1200" também mandam `HWResolution[600 600]` (o 1200 é só um realce interno).
- O 1200×600 previsto no plano **foi descartado**.
- O filtro exige raster de 1 bpp: `cupsColorSpace 3` (= `CUPS_CSPACE_K`: bit 1 = preto, conferido em `cups/raster.h`), `cupsBitsPerColor 1`. No hpcups: `<</cupsColorSpace 3/cupsBitsPerColor 1/cupsRowCount 1/cupsRowStep 2>>`.

### Papel e margens (`ImageableArea`, em pt)
O filtro só reconhece estes nomes (`map_paper_code`); qualquer outro vira Letter no fluxo:
`Letter, Legal, Executive, A4, A5, A6, B5, Env10, EnvDL, EnvC5, EnvB5, EnvMonarch, Postcard`.

| Papel | Tamanho (pt) | HP | foomatic | hpcups (esq/inf/dir/sup) |
|---|---|---|---|---|
| A4 | 595.28 × 841.89 | 12 12 583 830 | 11.34 11.34 583.66 830.66 | 18 / 15.5 / 18 / 15.5 |
| Letter | 612 × 792 | 12 12 600 780 | 11.34 … 600.66 780.66 | 12 em todas |
| Legal | 612 × 1008 | 12 12 600 996 | 11.34 … 600.66 996.66 | 12 |
| Executive | 522 × 756 | 12 12 510 744 | 11.34 … 510.66 744.66 | 12 |
| A5 | 420 × 595 | 12 12 408 583 | 11.34 … 408.66 583.66 | 12 |
| A6 | 298 × 420 | — | 11.34 … 285.66 408.66 | 12 |
| B5 (JIS) | 516 × 729 | — | 11.34 … 486.66 696.66 ⚠️ | 18 / 15.5 |
| Env10 | 297 × 684 | 12 12 285 672 | 11.34 … 285.66 672.66 | 12 |
| EnvDL | 312 × 624 | 12 12 300 612 | 11.34 … 299.66 611.66 | 18 / 15.5 |
| EnvC5 | 459 × 649 | — | 11.34 … 447.66 637.66 | 12 |
| EnvMonarch | 279 × 540 | — | 11.34 … 267.66 528.66 | 18 / 15.5 |

- **Proposta:** usar as margens da **HP: 12 pt (4,23 mm) em todos os lados**. Elas são do driver oficial e ficam entre o foomatic (4 mm) e o hpcups (até 6,35 mm). A página-régua da Fase 5 confirma.
- ⚠️ O B5 do foomatic (498 × 708) é ISO B5, não JIS; confirmar o tamanho na Fase 3.
- Mínimo/máximo do papel personalizado (hpcups): 3×5 in a 17×36 in (o máximo real da M1132 é Legal). Papel personalizado fica para depois; o filtro o mapearia para Letter.

### Tipo de papel (`MediaType`)
O filtro lê o **nome** em `header.MediaType` (não `cupsMediaType`). Nomes aceitos com Model ≥ 1:
`Plain`, `Transparency`, `Glossy`, `Envelope`, `Letterhead`, `ThickStock`, `Cardstock`, `Labels`, `Rough`, `Heavy`, `Light`, `Vellum`, `Color`, `Preprinted`, `Prepunched`, `Recycled`. Qualquer outro nome vira papel comum.
- Os códigos do filtro batem com os da HP (`Light` 258, `Labels` 265, `Envelope` 267, `Letterhead` 513 …). A exceção é `Heavy`: o filtro manda 261, e a HP manda 262 ("Heavy 111–130 g").
- **Proposta:** `Plain` (padrão), `Light`, `Heavy`, `ThickStock`, `Transparency`, `Labels`, `Envelope`, `Letterhead`, `Recycled`, `Rough`.

### Densidade, economia e qualidade
- `Density`: o filtro faz `atoi()`, então as escolhas precisam se chamar **`1`…`5`** (padrão `3`). Os nomes `Density1`… do foomatic dariam 0 e seriam ignorados. A HP também usa 1–5, com padrão 3.
- `EconoMode`: só liga com o valor **`on`**.
- `Quality=draft` também liga a economia de toner. Não precisa de opção própria.

### Bandeja (`InputSlot`)
- A M1132 tem uma bandeja só. A HP oferece apenas `Manual` → `MediaPosition 4`, que o filtro mapeia para `DMBIN_MANUAL`. O hpcups usa `Auto`=7 e `Manual`=2.
- **Proposta:** seguir a HP (`MediaPosition 4`) ou nem expor a opção (o padrão do filtro é `DMBIN_AUTO`). A Fase 5 decide se faz diferença.

### Cópias
- O filtro manda `ZJI_DMCOPIES = header.NumCopies` (as cópias são feitas na impressora). A HP usa `*cupsManualCopies: False`; o foomatic usa `True`.
- **Proposta:** `*cupsManualCopies: False`, como a HP. Testar na Fase 6.

### ⚠️ Modelo: ajuste necessário no filtro
- O filtro usa **Model 1 (HP1020)** por padrão e só muda isso pela opção de job `Model=0..3`. O CUPS não põe os padrões do PPD em `argv[5]`, então um `*DefaultModel: 2` no PPD **não chegaria** ao filtro.
- **Proposta para a Fase 3:** um patch mínimo em `src/rastertozjs.c` para o padrão ser `MODEL_HP_PRO` (por exemplo, `-DDEFAULT_MODEL=2` no Makefile com `#ifndef` no código), registrado no `NOTICE.md`.

## 3. Página de teste

`python3 scripts/make_testpage.py test` gera:
- `test/regua-a4.pdf` (2 páginas) e `test/regua-letter.pdf` (1 página);
- réguas em mm a partir da borda nos 4 lados, retângulos a 2/4/6 mm, escala de cinza de 10% a 100% e linhas de 0,1 a 1 pt.

A4 a 600 dpi = **4961 × 7016 px** brutos.
