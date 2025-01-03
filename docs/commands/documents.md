---
title: documents
layout: default
parent: Kommandoer
nav_order: 5
---

```shell
Usage: avid-tools documents [OPTIONS] COMMAND [ARGS]...

  Vis oversigter af dokumenterne i arkiveringsverionen.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  checksums   Vis antallet af md5 hashes.
  extensions  Vis antallet af filtypenavner.
```

```shell
Usage: avid-tools documents extensions [OPTIONS]

  Vis antallet af filtypenavner.

  Der vises fire kolloner:
  * ext: filetypen
  * count: antallet af filer med filetypen
  * unique: antallet af unikke md5 hashes med filetypen
  * firstDocId: først docId med filetypen

  Brug --limit option for at begrænse hvor mange filtyper vises.
  Filetypenavner vises i faldende rækkefølge som default, for at vise dem i
  stigende rækkefølge brug --reverse option.

  Resultaterne kan gemmes til en CSV fil ved at brug --csv-file option.
  --limit og --reverse kan bruges med CSV fil også.

Options:
  --limit INTEGER RANGE  Begræns hvor mange resultater vises.  [x>=1]
  --reverse              Vis i stigende rækkefølge.
  --csv-file FILE        Gem output til en CSV fil.
  -h, --help             Vis denne besked og afslut.
```

```shell
Usage: avid-tools documents checksums [OPTIONS]

  Vis antallet af md5 hashes.

  Der vises fire kolloner:
  * md5: hash
  * count: antallet af filer med hash
  * firstDocId: først docId med hash

  Brug --limit option for at begrænse hvor mange hasher vises. Hasher vises i
  faldende rækkefølge som default, for at vise dem i stigende rækkefølge, brug
  --reverse option.

  Resultaterne kan gemmes til en CSV fil ved at brug --csv-file option.
  --limit og --reverse kan bruges med CSV fil også.

Options:
  --limit INTEGER RANGE  Begræns hvor mange resultater vises.  [x>=1]
  --reverse              Vis i stigende rækkefølge.
  --csv-file FILE        Gem output til en CSV fil.
  -h, --help             Vis denne besked og afslut.
```
