# Commands

* [avid-tools](#avid-tools)
    * [init](#avid-tools-init)
    * [context](#avid-tools-context)
        * [add](#avid-tools-context-add)
        * [update](#avid-tools-context-update)
        * [move](#avid-tools-context-move)
        * [delete](#avid-tools-context-delete)
    * [tables](#avid-tools-tables)
        * [trim](#avid-tools-tables-trim)
        * [update-row-count](#avid-tools-tables-update-row-count)
    * [index](#avid-tools-index)
        * [view](#avid-tools-index-view)
        * [update](#avid-tools-index-update)
    * [documents](#avid-tools-documents)
        * [extensions](#avid-tools-documents-extensions)
        * [checksums](#avid-tools-documents-checksums)
    * [sample](#avid-tools-sample)
        * [size](#avid-tools-sample-size)
        * [docid](#avid-tools-sample-docid)
    * [search](#avid-tools-search)
    * [finalize](#avid-tools-finalize)

## avid-tools

```
Usage: avid-tools [OPTIONS] COMMAND [ARGS]...

  Arbejd med arkiveringsversioner.

Options:
  --version   Vis versionen og afslut.
  -h, --help  Vis denne besked og afslut.

Commands:
  init       Initializer en ny AVID mappe med værktøjets database.
  context    Opdater kontekstdokumentation.
  tables     Arbejd med tabellerne.
  index      Vis og opdater indeks filer i Indices.
  documents  Vis oversigter af dokumenterne i arkiveringsverionen.
  sample     Tag en prøve af dokumenter.
  search     Søg i tabellerne.
  finalize   Opdater md5 hashes og generer nye Indices/fileIndex.xml og...
```

### avid-tools init

```
Usage: avid-tools init [OPTIONS] AVID_DIR

  Initializer en ny AVID mappe med værktøjets database.

  AVID_DIR argument skal være stien til hoved mappen af en arkiversingsversion
  (hvor Indices, Tables, osv. ligger). Hvis programmet kører i hoved mappen,
  kan man brug "." som sti.

Options:
  -h, --help  Vis denne besked og afslut.
```

### avid-tools context

```
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

#### avid-tools context add

```
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

#### avid-tools context update

```
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

#### avid-tools context move

```
Usage: avid-tools context move [OPTIONS] FROM_DOC_ID TO_DOC_ID

  Flyt et kontekstdokument til en ny placering.

  FROM_DOC_ID skal være ID'en af et eksisterende kontekstdokument.

  TO_DOC_ID kan enten være ID'en af et andet eksisterende kontekstdokument,
  eller 0 for at flytte dokumentet til starten af dokumentation, eller -1 for
  at flytte dokumentet til slutningen af dokumentation.

Options:
  -h, --help  Vis denne besked og afslut.
```

#### avid-tools context delete

```
Usage: avid-tools context delete [OPTIONS] DOC_ID

  Fjern et kontekstdokument med ID DOC_ID fra arkiveringsversionen.

Options:
  -h, --help  Vis denne besked og afslut.
```

### avid-tools tables

```
Usage: avid-tools tables [OPTIONS] COMMAND [ARGS]...

  Arbejd med tabellerne.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  trim              Trim tabelværdier.
  update-row-count  Opdater antallet af rækker.
```

#### avid-tools tables trim

```
Usage: avid-tools tables trim [OPTIONS]

  Trim tabelværdier og sæt NULL værdier.

  Tomme kollonner med nillable=true i tabelskema sættes til NULL med
  xsi:nil="true".

  Som default trimmes alle tabeller. Det kan overrides med --table.

Options:
  -t, --table ID  Vælg tabeller.  [x>=1]
  -h, --help      Vis denne besked og afslut.
```

#### avid-tools tables update-row-count

```
Usage: avid-tools tables update-row-count [OPTIONS]

  Opdater antallet af rækker i tableIndex.

  Som default opdateres alle tabeller. Det kan overrides med --table.

Options:
  -t, --table ID  Vælg tabeller.  [x>=1]
  -h, --help      Vis denne besked og afslut.
```

### avid-tools index

```
Usage: avid-tools index [OPTIONS] COMMAND [ARGS]...

  Vis og opdater indeks filer i Indices.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  update  Opdater en indeks file.
  view    Vis en eller flere indeks filer.
```

#### avid-tools index view

```
Usage: avid-tools index view [OPTIONS] {archiveIndex|contextDocumentationIndex
                             |tableIndex}...

  Vis en eller flere indeks filer.

Options:
  -h, --help  Vis denne besked og afslut.
```

#### avid-tools index update

```
Usage: avid-tools index update [OPTIONS] INDEX_FILE

  Opdater en indeks file.

  Indekstype genkendes automatisk fra navnet af INDEX_FILE, men det kan
  overrides med --type option.

Options:
  --type [archiveIndex|contextDocumentationIndex|tableIndex]
                                  Indeks type.
  -h, --help                      Vis denne besked og afslut.
```

### avid-tools documents

```
Usage: avid-tools documents [OPTIONS] COMMAND [ARGS]...

  Vis oversigter af dokumenterne i arkiveringsverionen.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  checksums   Vis antallet af md5 hashes.
  extensions  Vis antallet af filtypenavner.
```

#### avid-tools documents extensions

```
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

#### avid-tools documents checksums

```
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

### avid-tools sample

```
Usage: avid-tools sample [OPTIONS] COMMAND [ARGS]...

  Tag en prøve af dokumenter.

Options:
  -h, --help  Vis denne besked og afslut.

Commands:
  docid  Tag en prøve af dokumenterne baseret på det originale...
  size   Tag en prøve af dokumenterne baseret på det originale...
```

#### avid-tools sample size

```
Usage: avid-tools sample size [OPTIONS] EXTENSIONS...

  Tag en prøve af dokumenterne baseret på det originale filtypenavn og
  størrelsen.

  Der tages en prøve af hver filtype, sorteret efter størrelsen. En halvdel af
  prøven indeholder filer med de laveste størrelser, og den anden del
  indeholder filer med de højeste.

  Prøven begrænses til de originale filtyper i EXTENSION argumenter. For at
  tage en prøve af alle filtyper brug "all" som argument.

  Som default bruges mappen _metadata/sample_size for at gemme prøven. Det kan
  overrides med --output-dir option.

Options:
  --sample-size INTEGER   Antallet af filer i prøven.  [default: 5; x>=1]
  --min-size INTEGER      Min filstørrelse i prøven.  [x>=1]
  --max-size INTEGER      Max filstørrelse i prøven.  [x>=1]
  --output-dir DIRECTORY  Mappen hvor prøven skal ligge.
  -h, --help              Vis denne besked og afslut.
```

#### avid-tools sample docid

```
Usage: avid-tools sample docid [OPTIONS] EXTENSIONS...

  Tag en prøve af dokumenterne baseret på det originale filtypenavn og
  docId'en.

  Der tages en prøve af hver filtype, sorteret efter docID. En halvdel af
  prøven indeholder filer med de laveste docId'er, og den anden del indeholder
  filer med de højeste.

  Prøven begrænses til de originale filtyper i EXTENSION argumenter. For at
  tage en prøve af alle filtyper brug "all" som argument.

  Som default bruges mappen _metadata/sample_docid for at gemme prøven. Det
  kan overrides med --output-dir option.

Options:
  --sample-size INTEGER   Antallet af filer i prøven.  [default: 5; x>=1]
  --min-docid INTEGER     Min docId i prøven.  [x>=1]
  --max-docid INTEGER     Max docId i prøven.  [x>=1]
  --output-dir DIRECTORY
  -h, --help              Vis denne besked og afslut.
```

### avid-tools search

```
Usage: avid-tools search [OPTIONS] PATTERN...

  Søg PATTERN i tabel rækker i Tables.

  PATTERN skal være i SQL LIKE format (% til nul eller flere bogstaver og _
  til nul eller et bogstav). Flere PATTERN kan bruges og matches med "eller"
  logik (dvs. PATTERN et, eller PATTERN to, eller PATTERN tre, osv.).

  Som default søges PATTERN'er i alle tabeller og kolonner. --table kan bruges
  for at begrænse søgning til bestemte tabeller. --column kan bruges for at
  begrænse søgning til bestemte kolloner i bestemte tabeller. Begge --table og
  --column kan bruges.

Options:
  -t, --table ID                  Vælg søgetabeller.  [x>=1]
  -c, --column TABLE_ID COLUMN_ID
                                  Vælg søgekolonner i tabeller.
  --limit INTEGER                 Begræns hvor mange resultater vises.  [x>=1]
  --show-columns / --show-rows    Vis alle kolonner i matchende rækker eller
                                  kun rækkenumre.
  -h, --help                      Vis denne besked og afslut.
```

### avid-tools finalize

```
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

