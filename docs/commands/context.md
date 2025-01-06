---
title: context
---

```shell
Usage: avid-tools context [OPTIONS] COMMAND [ARGS]...

  Opdater kontekstdokumentation.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  add     Tilføj et kontekstdokument.
  delete  Fjern et kontekstdokument.
  move    Flyt et kontekstdokument.
  update  Opdater et kontekstdokument.
```

## add
```shell
Usage: avid-tools context add [OPTIONS] FILE METADATA

  Tilføj et kontekstdokument til arkiveringsversionen.

  Kontekstdokumentet FILE kan tilføjes til contextDocumentation.

  METADATA-filen skal være et XML-dokument med det samme skema som
  Indices/contextDocumentationIndex.xml, men med et enkelt <document> tag.

  Som standard tiføjes det nye kontekstdokument til slutningen af eksiterende
  kontekstdokumenter. Hvis --position option bruges, dokumentet tilføjes til
  den position, og eksiterende dokumenter bevæges.

  METADATA eksempel
  ----------------

  <?xml version="1.0" encoding="utf-8"?>
  <contextDocumentationIndex xsi:schemaLocation="http://www.sa.dk/xmlns/diark/1.0 ../Schemas/standard/contextDocumentationIndex.xsd"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.sa.dk/xmlns/diark/1.0">
      <document>...</document>
  </contextDocumentationIndex>

Options:
  --position INTEGER  Placering af det nye kontekstdokument.  [x>=1]
  -h, --help          Vis denne besked og afslut.
```

## update

```shell
Usage: avid-tools context update [OPTIONS] DOC_ID

  Opdater kontekstdokument med ID DOC_ID.

  Enten filen eller metadata eller begge kan opdateres ved at bruge --file til
  filen og --metadata til metadata.

  Værdien til --metadata skal være et XML-dokument med det samme skema som
  Indices/contextDocumentationIndex.xml, men med et enkelt <document> tag.

  Metadata eksempel
  ----------------

  <?xml version="1.0" encoding="utf-8"?>
  <contextDocumentationIndex xsi:schemaLocation="http://www.sa.dk/xmlns/diark/1.0 ../Schemas/standard/contextDocumentationIndex.xsd"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.sa.dk/xmlns/diark/1.0">
      <document>...</document>
  </contextDocumentationIndex>

Options:
  --file FILE      Kontekstdokument fil.
  --metadata FILE  Kontekstdokument metadata.
  -h, --help       Vis denne besked og afslut.
```

## move
```shell
Usage: avid-tools context move [OPTIONS] FROM_DOC_ID TO_DOC_ID

  Flyt et kontekstdokument til en ny placering.

  FROM_DOC_ID skal være ID'en af et eksisterende kontekstdokument.

  TO_DOC_ID kan enten være ID'en af et andet eksisterende kontekstdokument,
  eller 0 for at flytte dokumentet til starten af dokumentation, eller -1 for
  at flytte dokumentet til slutningen af dokumentation.

Options:
  -h, --help  Vis denne besked og afslut.
```

## delete
```shell
Usage: avid-tools context delete [OPTIONS] DOC_ID

  Fjern et kontekstdokument med ID DOC_ID fra arkiveringsversionen.

Options:
  -h, --help  Vis denne besked og afslut.
```