---
title: finalize
---

```shell
Usage: avid-tools finalize [OPTIONS]

  Opdater md5 hashes og generer nye Indices/fileIndex.xml og
  Indices/docIndex.xml filer.

  archiveIndex.xml, contextDocumentationIndex.xml, tableIndex.xml bliver
  valideret.

  Som default, kun md5 hashes af index filer og kontekstdokumentation bliver
  opdateret. Men det kan ændres med --update-hashes option:

  * all: opdater hashes af alle filer
  * index: opdater hashes af indices
  * context: opdater hashes af kontekstdokumentation filerne
  * tables: opdater hashes af tabellerne
  * documents: opdater hashes af dokumenterne
  * none: ingen hash bliver opdateret

Options:
  --update-hashes [all|index|context|tables|documents|none]
                                  Vælg hvilke hashes skal opdateres.
                                  [default: index, context]
  -h, --help                      Vis denne besked og afslut.
```