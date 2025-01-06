---
title: tables
---

```shell
Usage: avid-tools tables [OPTIONS] COMMAND [ARGS]...

  Arbejd med tabellerne.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  trim              Trim tabelværdier.
  update-row-count  Opdater antallet af rækker.
```

## trim
```shell
Usage: avid-tools tables trim [OPTIONS]

  Trim tabelværdier og sæt NULL værdier.

  Tomme kollonner med nillable=true i tabelskema sættes til NULL med
  xsi:nil="true".

  Som default trimmes alle tabeller. Det kan overrides med --table.

Options:
  -t, --table ID  Vælg tabeller.  [x>=1]
  -h, --help      Vis denne besked og afslut.
```

## update-row-count
```shell
Usage: avid-tools tables update-row-count [OPTIONS]

  Opdater antallet af rækker i tableIndex.

  Som default opdateres alle tabeller. Det kan overrides med --table.

Options:
  -t, --table ID  Vælg tabeller.  [x>=1]
  -h, --help      Vis denne besked og afslut.
```