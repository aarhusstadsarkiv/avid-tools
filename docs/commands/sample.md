---
title: sample
---

```shell
Usage: avid-tools sample [OPTIONS] COMMAND [ARGS]...

  Tag en prøve af dokumenter.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  docid  Tag en prøve af dokumenterne baseret på det originale...
  size   Tag en prøve af dokumenterne baseret på det originale...
```

## size
```shell
Usage: avid-tools sample size [OPTIONS] EXTENSIONS...

  Tag en prøve af dokumenterne baseret på det originale filtypenavn og
  størrelsen.

  Der tages en prøve af hver filtype, sorteret efter størrelsen. En halvdel af
  prøven indeholder filer med de laveste størrelser, og den anden del
  indeholder filer med de højeste.

  Prøven begrænses til de originale filtyper i EXTENSION argumenter. For at
  tage en prøve af alle filtyper brug "all" som argument. For at tage en prøve
  af valide filtyper alene brug "all-valid" som argument. For at tage en prøve
  af ikke valide filtyper brug "all-invalid" som argument.

  Som default bruges mappen _metadata/sample_size for at gemme prøven. Det kan
  overrides med --output-dir option.

Options:
  --sample-size INTEGER   Antallet af filer i prøven.  [default: 5; x>=1]
  --min-size INTEGER      Min filstørrelse i prøven.  [x>=1]
  --max-size INTEGER      Max filstørrelse i prøven.  [x>=1]
  --output-dir DIRECTORY  Mappen hvor prøven skal ligge.
  -h, --help              Vis denne besked og afslut.
```

## docid
```shell
Usage: avid-tools sample docid [OPTIONS] EXTENSIONS...

  Tag en prøve af dokumenterne baseret på det originale filtypenavn og
  docId'en.

  Der tages en prøve af hver filtype, sorteret efter docID. En halvdel af
  prøven indeholder filer med de laveste docId'er, og den anden del indeholder
  filer med de højeste.

  Prøven begrænses til de originale filtyper i EXTENSION argumenter. For at
  tage en prøve af alle filtyper brug "all" som argument. For at tage en prøve
  af valide filtyper alene brug "all-valid" som argument. For at tage en prøve
  af ikke valide filtyper brug "all-invalid" som argument.

  Som default bruges mappen _metadata/sample_docid for at gemme prøven. Det
  kan overrides med --output-dir option.

Options:
  --sample-size INTEGER   Antallet af filer i prøven.  [default: 5; x>=1]
  --min-docid INTEGER     Min docId i prøven.  [x>=1]
  --max-docid INTEGER     Max docId i prøven.  [x>=1]
  --output-dir DIRECTORY
  -h, --help              Vis denne besked og afslut.
```