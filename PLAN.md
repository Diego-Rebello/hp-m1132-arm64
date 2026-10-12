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
- Base escolhida: [faradayfury/printer-all](https://github.com/faradayfury/printer-all) (GPL-2.0), filtro `rastertoxqx.c` (reescrita do foo2xqx do foo2zjs, também GPL-2.0).
  - ✅ `rastertoxqx` compila nativo arm64 sem avisos (`clang … -lcups -lcupsimage`).
  - ✅ Código simples: lê raster CUPS da entrada, escreve XQX na saída, sem rede e sem `exec`. Opções lidas: `Density`, `EconoMode`, `PageSize`, `MediaType`. Exige raster **1 bit por pixel**.
  - ❌ **Todos os PPDs do repo chamam `foomatic-rip`** (não existe no macOS). Nenhum usa os filtros do próprio repo, então **precisamos escrever nosso PPD.**
  - ❌ O `install.sh` copia para `/usr/libexec/cups/filter/` (protegido pelo SIP). **Não usar.** Instalar em `/Library/Printers/…` com caminho absoluto no `*cupsFilter`, como a HP faz.
  - ⚠️ M1132 não está na lista dele; só a P1007 foi testada em hardware. Pelo foo2xqx, a M1132 é **XQX**, a mesma família da P1102/M1212nf. Isso é confirmado na Fase 2. Não precisa de firmware.
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

Meta: ter certeza (sem a impressora) de que a M1132 é XQX e de que o filtro gera um fluxo coerente.

- [ ] Confirmar a família da M1132 em fontes primárias, sem ler arquivos inteiros:
  - lista de modelos do `foo2xqx` (man page / `foo2xqx.c` do foo2zjs);
  - entrada da M1132 no `models.dat` do HPLIP (campo de linguagem: esperar algo como `zjstream`/XQX).
  - Anotar no Registro qual fonte confirmou o quê.
- [ ] Se a M1132 for **ZjStream (ZJS)**, e não XQX, trocar a base para `rastertozjs.c` e refazer a Fase 1 para esse filtro (uns 15 min). Registrar a decisão.
- [ ] Extrair do PPD foomatic da P1102/M1212nf **só os parâmetros** de que precisamos (`grep`): resoluções suportadas, tamanhos de papel e margens (`ImageableArea`), nomes dos MediaType e valores de densidade.
- [ ] Gerar um PDF de teste simples (texto + linhas de régua nas bordas para checar margens).

**Pronto quando:** protocolo confirmado e parâmetros anotados em `docs/parametros.md`.

---

## Fase 3: Escrever o PPD e testar o pipeline sem sudo 🟡 média (~1–1,5 h)

Meta: PPD próprio validado e o pipeline completo (PDF → raster → XQX) funcionando **em arquivo**.

- [ ] `ppd/HP-LaserJet_Professional_M1132_MFP-arm64.ppd` com:
  - `*cupsFilter2: "application/vnd.cups-raster application/vnd.cups-printer 0 /Library/Printers/hp-m1132-arm64/rastertoxqx"` (+ `*cupsFilter` equivalente por compatibilidade);
  - `*cupsModelNumber`, `*1284DeviceID` com `MFG:Hewlett-Packard;MDL:HP LaserJet Professional M1132 MFP;` (assim o macOS sugere o driver);
  - `ColorModel` fixo em Gray com `cupsBitsPerColor 1` e `cupsColorSpace 3`/`cupsColorOrder 0` (1 bpp, que é o que o filtro exige);
  - `Resolution` 600 dpi (default) e, se a Fase 2 confirmar, 1200x600;
  - `PageSize`/`ImageableArea` para A4 (default), Letter, Legal, A5, B5, Executive e envelopes, com os nomes que `map_paper_code` reconhece;
  - `MediaType` (Plain, Heavy, Transparency, Envelope, Labels, Letterhead), `Density` 1–5 e `EconoMode`.
- [ ] `cupstestppd` sem erros (avisos documentados).
- [ ] Pipeline em arquivo, sem sudo:
  `cupsfilter -p ppd/…ppd -m application/vnd.cups-raster teste.pdf > out/teste.ras`
  → `./rastertoxqx 1 u t 1 "" out/teste.ras > out/teste.xqx`
  → `./xqxdecode < out/teste.xqx | head -40` mostra START_DOC / START_PAGE / JBIG / END_PAGE / END_DOC coerentes, com o tamanho de página certo.
- [ ] Testar também A4 com 2 páginas e uma página com `Density=5`.
- [ ] Commit: `Fase 3: PPD + pipeline validado offline`.

**Pronto quando:** `xqxdecode` decodifica as páginas sem erro e as dimensões batem com A4 a 600 dpi (≈4960×7016 px brutos).

---

## Fase 4: Instalar e criar uma fila nova 🟢 leve (~30 min) ⚠️ precisa de `sudo`

Meta: instalar sem tocar na fila antiga, com rollback em um comando.

O Claude não digita senha. Os comandos com `sudo` serão passados prontos para você rodar com `! sudo …`.

- [ ] `scripts/install.sh` (revisado antes de rodar):
  - `/Library/Printers/hp-m1132-arm64/rastertoxqx`, dono `root:wheel`, `755` (o CUPS recusa filtros graváveis por outros usuários);
  - `codesign --force --sign -` no binário;
  - PPD em `/Library/Printers/PPDs/Contents/Resources/`.
- [ ] `scripts/uninstall.sh` (rollback: remove a fila nova, o filtro e o PPD).
- [ ] Criar a **fila nova** `M1132_arm64` com a mesma URI USB:
  `lpadmin -p M1132_arm64 -E -v '<URI acima>' -P <ppd> -D "HP M1132 (arm64)"`
- [ ] A fila antiga **não é removida** nesta fase.
- [ ] Commit: `Fase 4: scripts de instalação`.

**Pronto quando:** `lpstat -p M1132_arm64` mostra a fila ativa e `lipo -archs` no filtro instalado dá `arm64`.

---

## Fase 5: Teste real na impressora 🟡 média (~1 h, depende do resultado)

Meta: página impressa corretamente.

- [ ] Impressora ligada, USB conectado, papel A4.
- [ ] `lp -d M1132_arm64 teste.pdf`
- [ ] Ver só as linhas relevantes do log: `grep "Job <n>" /var/log/cups/error_log | grep -iE "error|rastertoxqx|badarch|sent|PAGE" | tail -30`.
- [ ] Árvore de problemas:
  | Sintoma | Provável causa | Ação |
  |---|---|---|
  | `badarch` de novo | binário errado instalado | `lipo -archs` no instalado; reinstalar |
  | "insecure filter" / permissão | dono/modo do filtro | `chown root:wheel`, `chmod 755` |
  | Sandbox nega execução | caminho fora do permitido | testar `/Library/Printers/<pasta>/…` como a HP; registrar a mensagem exata |
  | Impressora não reage / luz pisca | protocolo errado | voltar à Fase 2 e testar `rastertozjs` |
  | Imprime lixo / página em branco | parâmetros de página/resolução | comparar com `xqxdecode` e ajustar o PPD |
  | Margem cortada / deslocada | `ImageableArea` | ajustar o PPD com a página-régua |
- [ ] Testar um PDF real, um documento do Pages/Word e uma impressão pelo Safari.
- [ ] Registrar o resultado (inclusive falhas) no Registro e commitar.

**Pronto quando:** página de teste e um documento real saem corretos.

---

## Fase 6: Acabamento e uso diário 🟢 leve (~30–45 min)

- [ ] Tornar `M1132_arm64` a padrão (`lpoptions -d M1132_arm64`).
- [ ] Conferir as opções no diálogo de impressão do macOS (densidade, economia, tipo de papel, cópias).
- [ ] Testar várias cópias e várias páginas (o PPD usa `cupsManualCopies`?).
- [ ] **Depois de ~1 semana de uso sem problemas:** remover a fila antiga (`lpadmin -x HP_LaserJet_Professional_M1132_MFP`). Remover os drivers Intel da HP é opcional e fica para outra decisão.
- [ ] Commit: `Fase 6: uso diário`.

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

1. Trocar para `rastertozjs.c` (mesmo repo) se for problema de protocolo.
2. Portar o filtro `hpcups` do HPLIP (bem mais pesado: várias sessões).
3. Servidor de impressão em Raspberry Pi/Linux com `foo2xqx`/HPLIP, compartilhado por IPP (o Mac imprime via AirPrint).

---

## Registro

| Data | Fase | Resultado / decisões | Commit |
|---|---|---|---|
| 2026-10-12 | 0 | Diagnóstico concluído (ver Contexto). `rastertoxqx` compila em arm64. Projeto criado em `~/hp-m1132-arm64`. | — |
| 2026-10-12 | 1 | Estrutura criada; `rastertoxqx` e `xqxdecode` compilam arm64 sem avisos (`-Wall`). Fontes copiadas sem modificação de printer-all@b6601e3. | (este) |
