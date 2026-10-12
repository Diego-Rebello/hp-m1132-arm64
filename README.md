# hp-m1132-arm64

Filtro CUPS **nativo arm64** para a HP LaserJet Professional M1132 MFP no macOS 27 (Apple Silicon), que não roda mais os filtros Intel da HP (`com.apple.badarch-error`).

> 🚧 Em desenvolvimento: ver [`PLAN.md`](PLAN.md). Ainda não foi testado na impressora.

## Compilar

```sh
make check   # compila rastertozjs e zjsdecode e confere que são arm64
```

Créditos e licença: [`NOTICE.md`](NOTICE.md) (GPL v2+).
