---
title: index
---

```shell
Usage: avid-tools index [OPTIONS] COMMAND [ARGS]...

  Vis og opdater indeks filer i Indices.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  update  Opdater en indeks file.
  view    Vis en eller flere indeks filer.
```

## view
```shell
Usage: avid-tools index view [OPTIONS] {archiveIndex|contextDocumentationIndex
                             |tableIndex}...

  Vis en eller flere indeks filer.

Options:
  -h, --help  Vis denne besked og afslut.
```

## update
```shell
Usage: avid-tools index update [OPTIONS] INDEX_FILE

  Opdater en indeks file.

  Indekstype genkendes automatisk fra navnet af INDEX_FILE, men det kan
  overrides med --type option.

Options:
  --type [archiveIndex|contextDocumentationIndex|tableIndex]
                                  Indeks type.
  -h, --help                      Vis denne besked og afslut.
```