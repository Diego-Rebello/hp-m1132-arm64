# HP LaserJet M1132 MFP no macOS 27 (Apple Silicon): plano

Objetivo: voltar a imprimir na HP LaserJet Professional M1132 MFP (USB) com um filtro CUPS **nativo arm64**, sem Rosetta, sem Ghostscript e sem os drivers Intel da HP.

---

## Como usar este plano (limites de 5 h e semanal)

- **Uma fase por sessão.** Cada fase foi pensada para caber com folga em uma janela de 5 h e terminar com um ponto de parada seguro (nada fica "pela metade").
- **Começar cada sessão assim:** `/clear` e depois:
  > `continua o PLAN.md do ~/hp-m1132-arm64, fase N`
- **No fim de cada fase:** marcar os checkboxes, preencher o "Registro" lá embaixo e fazer `git commit`. É isso que permite retomar sem reexplicar tudo.
- **Economizar uso:**
  - Não colar nem pedir para ler arquivos grandes inteiros (PPDs têm 30 KB+; logs do CUPS são enormes). Usar `grep`/`tail` com filtro.
  - Fases marcadas como 🟢 **leve** podem ser feitas no fim de uma janela ou com o limite semanal apertado. Fases 🟡 **média** precisam de uma janela mais folgada.
  - Se o limite acabar no meio de uma fase, parar no último passo concluído, anotar no Registro e commitar.
- **Sugestão de calendário:** Semana 1 → Fases 1–3 (tudo sem `sudo`, sem mexer no sistema). Semana 2 → Fases 4–5 (instalação e teste real). Semana 3+ → Fases 6–7 (acabamento e publicação), sem pressa.

---

## Contexto já levantado (Fase 0, concluída em 12/10/2026)

- Mac: Apple Silicon (`arm64`), macOS 27.0.1 (26A434).
- Fila atual: `HP_LaserJet_Professional_M1132_MFP`
  URI: `usb://Hewlett-Packard/HP%20LaserJet%20Professional%20M1132%20MFP?serial=…`
- **Causa da falha:** os filtros da HP (`usbink`, `rastertozjs` em `/Library/Printers/hp/laserjet/M11_M12_M13series/hpRaster.bundle`) são só `x86_64 i386`. O CUPS do macOS 27 recusa iniciá-los: log com `com.apple.badarch-error` e `Broken pipe`, 0 bytes enviados. O Rosetta está ativo e o filtro roda no terminal, então o bloqueio é do CUPS.
- Nenhum driver HP instalado tem versão arm64 (`M1130_1210series`, `hplaserjetzjs`, `p1100…`, `cp1020…`: todos Intel).
- A fila atual usa o PPD **errado** ("HP LaserJet Pro M12"), não o da série M1130/M1210. É irrelevante para a solução, mas explica comportamentos estranhos antigos.
- Base escolhida: [faradayfury/printer-all](https://github.com/faradayfury/printer-all) (GPL-2.0), filtro ~~`rastertoxqx.c`~~ → **`rastertozjs.c`** desde a Fase 2 (reescrita do foo2zjs, também GPL-2.0). As notas abaixo valem para os dois filtros (mesmo autor, mesma estrutura).
  - ✅ `rastertoxqx` compila nativo arm64 sem avisos (`clang … -lcups -lcupsimage`).
  - ✅ Código simples: lê raster CUPS da entrada, escreve XQX na saída, sem rede e sem `exec`. Opções lidas: `Density`, `EconoMode`, `PageSize`, `MediaType`. Exige raster **1 bit por pixel**.
  - ❌ **Todos os PPDs do repo chamam `foomatic-rip`** (não existe no macOS). Nenhum usa os filtros do próprio repo, então **precisamos escrever nosso PPD.**
  - ❌ O `install.sh` copia para `/usr/libexec/cups/filter/` (protegido pelo SIP). **Não usar.** Instalar em `/Library/Printers/…` com caminho absoluto no `*cupsFilter`, como a HP faz.
  - ⚠️ M1132 não está na lista dele; só a P1007 foi testada em hardware. ~~Pelo foo2xqx, a M1132 é XQX~~ → **Corrigido na Fase 2: a M1132 é ZjStream (ZJS)**, a mesma família da P1102. A base passou a ser `rastertozjs.c`, Model 2. Não precisa de firmware. Detalhes em `docs/parametros.md`.
- Ferramentas disponíveis sem `sudo`: `clang`, `make`, `git`, `gh` (logado como `Diego-Rebello`), `cupsfilter`, `cupstestppd`.
- Cópia do printer-all usada na análise: pasta temporária do Claude (some ao reiniciar). A Fase 1 clona de novo para dentro do projeto.

---

## Fase 1: Montar o projeto local 🟢 leve (~30 min)

Meta: repositório local enxuto, compilando, com licença correta. **Nada é instalado no sistema.**

- [x] Clonar `printer-all` em `vendor/printer-all-src/` (ignorado no git) e anotar o hash do commit usado (`b6601e3`).
- [x] Copiar só o necessário para `src/`: `rastertoxqx.c`, `foo2zjs/jbig.c`, `jbig.h`, `jbig_ar.c`, `jbig_ar.h`, `xqx.h`, `xqxdecode.c`.
- [x] `LICENSE` (GPL-2.0) + `NOTICE.md` com créditos: foo2zjs (Rick Richardson) e printer-all (faradayfury), com o commit de origem.
- [x] `Makefile` com os alvos `rastertoxqx`, `xqxdecode`, `clean` e `check` (`lipo -archs` precisa dar `arm64`).
- [x] `.gitignore` (binários, `vendor/`, `out/`).
- [x] `make && make check` sem avisos. (Com `-Wextra` aparecem 5 avisos inofensivos; mantido `-Wall`, igual ao upstream.)
- [x] Commit: `Fase 1: estrutura e filtro XQX compilando`.

**Pronto quando:** `make check` imprime `arm64` e o repo tem só fontes + docs.

---

## Fase 2: Confirmar o protocolo e validar o filtro offline 🟡 média (~1–1,5 h)

Meta: ter certeza (sem a impressora) do protocolo da M1132 (XQX ou ZJS) e de que o filtro gera um fluxo coerente.

- [x] Confirmar a família da M1132 em fontes primárias, sem ler arquivos inteiros:
  - lista de modelos do `foo2xqx` (man page / `foo2xqx.c` do foo2zjs): a M1132 não aparece;
  - entrada da M1132 no `models.dat` do HPLIP: `LJZjsMono`, que não decide. O que decidiu foi o `hpcups.drv` (`ljzjstream`) e o **próprio filtro Mac da HP** (`JZJZ`, sem XQX).
  - Fontes anotadas em `docs/parametros.md` §1.
- [x] A M1132 é **ZjStream (ZJS)**: base trocada para `rastertozjs.c` (Model 2 = `-z2`, como a P1102) e Fase 1 refeita (`rastertozjs` + `zjsdecode`, arm64, sem avisos).
- [x] Parâmetros extraídos (HP `hp1130.ppd`, hpcups, foomatic P1102, código do filtro) → `docs/parametros.md` §2.
- [x] PDF de teste: `scripts/make_testpage.py` → `test/regua-a4.pdf` (2 páginas) e `test/regua-letter.pdf`.
- [x] Commit: `Fase 2: M1132 é ZJS; base trocada para rastertozjs`.

**Pronto quando:** protocolo confirmado e parâmetros anotados em `docs/parametros.md`.

---

## Fase 3: Escrever o PPD e testar o pipeline sem sudo 🟡 média (~1–1,5 h)

Meta: PPD próprio validado e o pipeline completo (PDF → raster → ZJS) funcionando **em arquivo**. Os valores estão em `docs/parametros.md` §2; os resultados, em §4.

- [x] **Patch mínimo no filtro:** `DEFAULT_MODEL` com `#ifndef` em `src/rastertozjs.c` e `-DDEFAULT_MODEL=2` no `Makefile`. Registrado no `NOTICE.md`.
- [x] `ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd` com:
  - `*cupsFilter2: "application/vnd.cups-raster application/vnd.hp-zjs 0 /Library/Printers/hp-m1132-arm64/rastertozjs"` (+ `*cupsFilter` equivalente). ~~`application/vnd.cups-printer`~~ não existe no macOS; usado um tipo do fabricante, como manda a documentação da CUPS;
  - `*cupsModelNumber: 2`, `*1284DeviceID: "MFG:Hewlett-Packard;MDL:HP LaserJet Professional M1132 MFP;CMD:ZJS,PJL,ACL;"`;
  - `ColorModel` fixo em Gray (`cupsColorSpace 3`, `cupsBitsPerColor 1`, `cupsColorOrder 0`);
  - `Resolution` só 600x600;
  - 13 tamanhos (A4 padrão, Letter, Legal, Executive, A5, A6, B5 JIS, Postcard, Env10, EnvDL, EnvC5, EnvB5, EnvMonarch), margens de 12 pt;
  - `MediaType` (10 tipos, `Plain` padrão), `Density` `1`–`5` (padrão 3), `EconoMode` Boolean `off`/`on`, `*cupsManualCopies: False`.
- [x] `cupstestppd`: só falha por "falta o arquivo cupsFilter" (filtro instalado na Fase 4). Com `-I filters` dá PASS + 1 aviso (`EnvB5` ≠ `EnvISOB5`, mantido porque é o nome que o filtro reconhece).
- [x] Pipeline em arquivo: `cupsfilter … -m application/vnd.cups-raster` → `./rastertozjs` → `./zjsdecode` com START_DOC / START_PAGE / JBIG / END_PAGE / END_DOC coerentes; `zjsdecode -d` recupera a imagem certa.
  - ⚠️ `cupsfilter -m printer/foo` do macOS ignora os filtros do PPD (até o da HP) e gera PostScript. A cadeia completa só pode ser testada com a fila real.
- [x] A4 com 2 páginas, Letter, os 13 tamanhos (`DMPAPER` certo em todos) e `Density=5 EconoMode=on MediaType=Heavy` com 2 cópias.
- [x] Commit: `Fase 3: PPD + pipeline validado offline`.

**Pronto quando:** `zjsdecode` decodifica as páginas sem erro e as dimensões batem com A4 a 600 dpi. ✅ São **4761×6816 px** (só a área imprimível, como o hpcups manda), e não os 4961×7016 da página inteira que se esperava. Ver `docs/parametros.md` §4.

---

## Fase 4: Instalar e criar uma fila nova 🟢 leve (~30 min) ⚠️ precisa de `sudo`

Meta: instalar sem tocar na fila antiga, com rollback em um comando.

O Claude não digita senha. Os comandos com `sudo` são passados prontos para rodar **no Terminal.app**, começando com `cd ~/hp-m1132-arm64 && sudo …` (o `! sudo` só funciona no prompt do Claude Code, não no zsh).

- [x] `scripts/install.sh` (revisado antes de rodar). Uso: `make && sudo ./scripts/install.sh`
  - confere que `rastertozjs` já está compilado e é arm64 (não compila como root);
  - `/Library/Printers/hp-m1132-arm64/rastertozjs`, dono `root:wheel`, `755` (o CUPS recusa filtros graváveis por outros usuários);
  - `codesign --force --sign -` no binário + `codesign --verify`;
  - PPD em `/Library/Printers/PPDs/Contents/Resources/` (`root:wheel 644`), validado com `cupstestppd` já com o filtro no lugar;
  - URI detectada pelo `lpinfo --include-schemes usb` ou, se a impressora estiver desligada, copiada da fila antiga. `URI=…` força outra. O serial não fica no script.
- [x] `scripts/uninstall.sh` (rollback: cancela os jobs e remove a fila nova, o filtro e o PPD).
- [x] **Fila nova** `M1132_arm64` criada pelo próprio `install.sh` (`lpadmin -p M1132_arm64 -E -v <URI> -P <ppd> -D "HP M1132 (arm64)" -o printer-is-shared=false`). O aviso "Drivers de impressoras não são mais usados" do `lpadmin -P` é esperado e não impede nada.
- [x] A fila antiga **não foi removida** (continua ociosa).
- [x] Commit: `Fase 4: scripts de instalação`.

**Pronto quando:** `lpstat -p M1132_arm64` mostra a fila ativa e `lipo -archs` no filtro instalado dá `arm64`. ✅ Fila ociosa e ativa, filtro `arm64` com assinatura ad hoc, `device-uri` igual à fila antiga.

---

## Fase 5: Teste real na impressora 🟡 média (~1 h, depende do resultado)

Meta: página impressa corretamente.

- [x] Impressora ligada, USB conectado, papel A4.
- [x] `lp -d M1132_arm64 teste.pdf`
- [x] Ver só as linhas relevantes do log: `grep "Job <n>" /var/log/cups/error_log | grep -iE "error|rastertozjs|badarch|sent|PAGE" | tail -30`.
- [x] Árvore de problemas (a falha real foi outra: o USB travava com o fluxo do Model 2; ver Registro e `docs/parametros.md` §5):
  | Sintoma | Provável causa | Ação |
  |---|---|---|
  | `badarch` de novo | binário errado instalado | `lipo -archs` no instalado; reinstalar |
  | "insecure filter" / permissão | dono/modo do filtro | `chown root:wheel`, `chmod 755` |
  | Sandbox nega execução | caminho fora do permitido | testar `/Library/Printers/<pasta>/…` como a HP; registrar a mensagem exata |
  | Impressora não reage / luz pisca | protocolo errado | voltar à Fase 2 e testar o caminho inverso (`rastertoxqx`, que está no histórico do git), ou o Model 1 do `rastertozjs` |
  | Imprime lixo / página em branco | parâmetros de página/resolução | comparar com `zjsdecode` e ajustar o PPD |
  | Margem cortada / deslocada | `ImageableArea`, ou a impressora não centraliza a imagem (o macOS manda só a área imprimível) | medir com a página-régua; ajustar as margens do PPD |
- [x] Testar um documento real: **Word** perfeito em A4. ~~Preview e Safari~~ → passaram para a Fase 6, junto com a conferência do diálogo.
- [x] Registrar o resultado (inclusive falhas) no Registro e commitar.

**Pronto quando:** página de teste e um documento real saem corretos. ✅ Página-régua (1 e 2 páginas) e documento do Word perfeitos, com o **Model 4**.

---

## Fase 6: Acabamento e uso diário 🟢 leve (~30–45 min)

- [x] Tornar `M1132_arm64` a padrão (`lpoptions -d M1132_arm64`). Já era a padrão do sistema e do usuário. Também foi desligado o "Usar última impressora" (`defaults write org.cups.PrintingPrefs UseLastPrinter -bool false`), porque o macOS guardava a fila antiga como padrão em outras redes. Para desfazer: `defaults delete org.cups.PrintingPrefs UseLastPrinter`.
- [x] Conferir as opções no diálogo de impressão do macOS (densidade, economia, tipo de papel, cópias) e **a escolha do tamanho do papel** (o Diego sentiu falta disso no Word; lá o tamanho vem de Layout → Tamanho / Arquivo → Configurar Página, e no Preview/Safari aparece em "Tamanho do Papel").
- [x] Imprimir um PDF pelo **Preview** e uma página pelo **Safari** (sobraram da Fase 5).
- [x] Testar várias cópias e várias páginas na fila real: com `Collate` ligado deve sair 1,2,1,2; desligado, 1,1,2,2 (offline já conferido na revisão da Fase 3). ✅ Jobs 604 (ligado) e 605 (desligado) saíram na ordem certa.
- [ ] ⏳ **Depois de ~1 semana de uso sem problemas (a partir de 19/10/2026):** remover a fila antiga (o macOS ainda manda jobs "Supplies Levels" para ela, que rodam o `usbink` da HP) (`lpadmin -x HP_LaserJet_Professional_M1132_MFP`). Remover os drivers Intel da HP é opcional e fica para outra decisão.
- [x] Commit: `Fase 6: uso diário`.

---

## Fase 7: Publicar no GitHub 🟢 leve (~30 min)

- [ ] Decidir: **público ou privado** (ainda em aberto).
- [ ] README em PT e EN: problema (macOS 27 + filtros Intel), instalação, rollback, status testado (M1132 MFP, macOS 27.0.1, data) e créditos/GPL.
- [ ] `gh repo create Diego-Rebello/hp-m1132-arm64 --private|--public --source . --push`
- [ ] Opcional: abrir uma issue ou PR no `faradayfury/printer-all` com o relatório de teste da M1132 e o problema dos PPDs foomatic + SIP.

---

## Fora do escopo (anotar e não fazer agora)

- **Scanner da M1132** (é multifuncional): o scanner usa outro caminho (ICA/eSCL); provavelmente também é Intel. Investigar depois, como projeto separado.
- Suporte a outros modelos.

## Planos B (se a Fase 5 falhar de vez)

1. ~~Trocar para `rastertoxqx.c` (mesmo repo) ou outro Model do `rastertozjs` se for problema de protocolo.~~ Resolvido na Fase 5 com o Model 4.
2. Portar o filtro `hpcups` do HPLIP (bem mais pesado: várias sessões).
3. Servidor de impressão em Raspberry Pi/Linux com `foo2zjs -z2`/HPLIP, compartilhado por IPP (o Mac imprime via AirPrint).

---

## Registro

| Data | Fase | Resultado / decisões | Commit |
|---|---|---|---|
| 2026-10-12 | 0 | Diagnóstico concluído (ver Contexto). `rastertoxqx` compila em arm64. Projeto criado em `~/hp-m1132-arm64`. | — |
| 2026-10-12 | 1 | Estrutura criada; `rastertoxqx` e `xqxdecode` compilam arm64 sem avisos (`-Wall`). Fontes copiadas sem modificação de printer-all@b6601e3. | (este) |
| 2026-10-12 | 2 | **M1132 é ZjStream, não XQX.** Prova decisiva: o filtro Mac da própria HP para a série M1130/M1210 só contém `JZJZ`/`ENTER LANGUAGE` do ZJS. O hpcups (HPLIP 3.12.11) põe a M1132 no grupo `ljzjstream` da P1102; o `models.dat` (`LJZjsMono`, sem firmware) não decide; o foo2zjs não lista a M1132. Base trocada para `rastertozjs.c` Model 2 (`-z2`); `zjsdecode` vem do foo2zjs (espelho koenkooi@e04290d). Parâmetros em `docs/parametros.md`: só 600×600, margens de 12 pt (HP), `Density` numérico 1–5, Model padrão do filtro = 1 → **patch na Fase 3**. Página-régua: `scripts/make_testpage.py`. | (este) |
| 2026-10-12 | 3 | PPD próprio (13 tamanhos, margens de 12 pt, `MediaType`, `Density` 1–5, `EconoMode`) e patch `DEFAULT_MODEL=2`. Pipeline offline OK: `DMPAPER` certo nos 13 tamanhos e opções conferidas no fluxo; a página decodificada pelo `zjsdecode -d` saiu correta. **Achados:** (1) no macOS o raster cobre só a área imprimível (A4 = 4761×6816), a mesma forma que o hpcups manda; (2) `cupsfilter -m printer/foo` ignora os filtros do PPD, então a cadeia completa só é testada na fila real; (3) `cupsFilter2` passou a usar `application/vnd.hp-zjs`; (4) 2 cópias × 2 páginas devem sair sem agrupar (1,1,2,2): conferir na Fase 6. | (este) |
| 2026-10-12 | 3 (revisão) | Correções do `/code-review`: códigos de papel da HP via `cupsMediaType` (`Heavy` 262, `ExtraHeavy` 283); `EconoMode` `True`/`False`; filtro lê o PPD da fila (Model, padrões de `Density`/`EconoMode`/`Collate`); cópias por `argv[4]` e agrupamento feito pelo filtro (opção `Collate`); `DEFAULT_MODEL` no código com `#error`; PPD gerado por `scripts/make_ppd.py` (`make ppd`). Tudo conferido offline com `zjsdecode`. | (este) |
| 2026-10-12 | 4 | `install.sh`/`uninstall.sh` criados; instalação feita pelo Diego no Terminal.app (`cd ~/hp-m1132-arm64 && sudo ./scripts/install.sh`; o `! sudo` dentro do zsh não serve). Fila `M1132_arm64` ativa, com a mesma URI USB, sem compartilhamento; filtro `root:wheel 755`, arm64, ad hoc; PPD da fila confere (`cupsFilter2` → filtro instalado). Fila antiga intacta. Nada foi impresso ainda: isso é a Fase 5. | (este) |
| 2026-10-12 | 5 | **Imprimindo.** Com o Model 2, o filtro arm64 rodou sem erro (o `badarch` foi resolvido), mas o USB travou: `WritePipe e00002ed` (*not responding*), 0 bytes enviados, mesmo depois de desligar e ligar a impressora. Um PJL raw foi aceito, então o USB funciona. O filtro Intel da HP rodou no Terminal pelo Rosetta (com `DEVICE_URI` falso) e o fluxo dele foi aceito pela impressora. A bisseção (`tools/zjsmix.py`, `tools/zjsdump.py`) mostrou que o problema é a **estrutura ZJS da P1102**, não o PJL: nosso JBIG dentro da estrutura da HP imprimiu perfeito. Criado o **Model 4 (`MODEL_HP_M1132`)**, agora o padrão e com `cupsModelNumber: 4` no PPD: PJL em CRLF com `ENTER LANGUAGE=ZJS`, `START_DOC` só com `DMCOLLATE`, itens em ordem de ID, sem `RET` e sem plano. O Model 2 continua idêntico byte a byte. Reinstalado pelo Diego (`sudo ./scripts/install.sh`). Página-régua de 1 e 2 páginas e documento do Word **perfeitos** em A4. Pendências para a Fase 6: Preview/Safari e a escolha do papel no diálogo. Debug log do CUPS ligado durante o teste e desligado no fim. Detalhes em `docs/parametros.md` §5. | (este) |
| 2026-10-12 | 6 | Uso diário OK. `M1132_arm64` já era a padrão; foi desligado o `UseLastPrinter` do macOS, que guardava a fila antiga como padrão em outras redes. 2 cópias da régua de 2 páginas: `Collate` ligado deu 1,2,1,2 e desligado deu 1,1,2,2. O Diego conferiu o diálogo (tamanho do papel, Intercalar, Recursos da Impressora: Media Type, Density, EconoMode) e imprimiu pelo **Preview** e pelo **Safari**: tudo certo. **Pendente:** remover a fila antiga depois de ~1 semana sem problemas (a partir de 19/10/2026). | (este) |
