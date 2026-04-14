# Table of Contents

- [Table of Contents](#table-of-contents)
- [⚠ Important: Custom Installation Required](#-important-custom-installation-required)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
- [Commands](#commands)
  - [avid-tools](#avid-tools)
    - [avid-tools init](#avid-tools-init)
    - [avid-tools context](#avid-tools-context)
      - [avid-tools context add](#avid-tools-context-add)
      - [avid-tools context update](#avid-tools-context-update)
      - [avid-tools context move](#avid-tools-context-move)
      - [avid-tools context delete](#avid-tools-context-delete)
    - [avid-tools tables](#avid-tools-tables)
      - [avid-tools tables fastsearch](#avid-tools-tables-search)
      - [avid-tools tables search](#avid-tools-tables-search)
      - [avid-tools tables load](#avid-tools-tables-load)
      - [avid-tools tables trim](#avid-tools-tables-trim)
      - [avid-tools tables update-row-count](#avid-tools-tables-update-row-count)
    - [avid-tools index](#avid-tools-index)
      - [avid-tools index view](#avid-tools-index-view)
      - [avid-tools index update](#avid-tools-index-update)
    - [avid-tools documents](#avid-tools-documents)
      - [avid-tools documents extensions](#avid-tools-documents-extensions)
      - [avid-tools documents checksums](#avid-tools-documents-checksums)
    - [avid-tools sample](#avid-tools-sample)
      - [avid-tools sample size](#avid-tools-sample-size)
      - [avid-tools sample docid](#avid-tools-sample-docid)
    - [avid-tools search](#avid-tools-search)
    - [avid-tools finalize](#avid-tools-finalize)
    - [avid-tools validate](#avid-tools-validate)
      - [avid-tools validate file](#avid-tools-validate-file)
      - [avid-tools validate indices](#avid-tools-validate-indices)
      - [avid-tools validate run](#avid-tools-validate-run)
    - [avid-tools encoding](#avid-tools-encoding)
      - [avid-tools encoding bloom](#avid-tools-encoding-bloom)
        - [avid-tools encoding bloom contains](#avid-tools-encoding-bloom-contains)
        - [avid-tools encoding bloom encode](#avid-tools-encoding-bloom-encode)
        - [avid-tools encoding bloom search](#avid-tools-encoding-bloom-search)
      - [avid-tools encoding rowwise](#avid-tools-encoding-rowwise)
        - [avid-tools encoding rowwise encode](#avid-tools-encoding-rowwise-encode)
        - [avid-tools encoding rowwise search](#avid-tools-encoding-rowwise-search)

# ⚠ Important: Custom Installation Required

This project uses a **non-standard installation process** because it combines Python and Rust components.

## Prerequisites

* Rust (required for building the package)
  Install Rust here: https://rust-lang.org/tools/install
* `uv` package manager installed

## Installation Steps

```bash
# 1. Create a virtual environment
uv sync

# 2. Activate the environment
source .venv/bin/activate  # Use activate.fish or others if needed

# 3. Build the project (requires Rust)
maturin build

# 4. Install the CLI tool from the generated wheel
uv tool install ./target/wheels/avid_tools*.whl
```

This process builds a Python wheel using Rust and installs it as a CLI tool.

# Commands

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

### avid-tools tables search

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

### avid-tools tables load

```
Usage: avid-tools tables load [OPTIONS]

  Load table into DB from CSV file

Options:
  --load-file FILE  [required]
  --db-file FILE    [required]
  --help            Show this message and exit.
```

### avid-tools tables fastsearch

```
Usage: avid-tools tables fastsearch [OPTIONS]

  Perform full-text search in tables XML files

Options:
  --text TEXT  [required]
  --help       Show this message and exit.
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

#### avid-tools sample docid

```
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

### avid-tools validate

```
Usage: avid-tools validate [OPTIONS] COMMAND [ARGS]...

  Validate AVID indices

Options:
  --help  Show this message and exit.

Commands:
  file     Validate XML file against XSD file
  indices  Validate Indices against XSD schemas
  run      Run archive validation tests
```


#### avid-tools validate file

```
Usage: avid-tools validate file [OPTIONS]

  Validate XML file against XSD file

Options:
  --xml-path FILE  [required]
  --xsd-path FILE  [required]
  --help           Show this message and exit.
```

#### avid-tools validate indices

```
Usage: avid-tools validate indices [OPTIONS]

  Validate Indices against XSD schemas

Options:
  --path DIRECTORY
  --help            Show this message and exit.
```

#### avid-tools validate run

```
Usage: avid-tools validate run [OPTIONS]

  Run archive validation tests

Options:
  --check TEXT                    Check specific validation function(s)
  --verbose                       Set logging level to DEBUG
  --category [docs|indices|schemas|contextdocs|tables]
                                  Run all validators of type
  --except TEXT                   Validators to not check
  --rust-optimize
  --help                          Show this message and exit.
```

### avid-tools encoding

```
Usage: avid-tools encoding [OPTIONS] COMMAND [ARGS]...

  Encode database or perform actions on encoded database

Options:
  --help  Show this message and exit.

Commands:
  bloom    Encode and search a database using Bloom filters
  rowwise  This program converts SQLite databases into specially encoded...
```

#### avid-tools encoding bloom

```
Usage: avid-tools encoding bloom [OPTIONS] COMMAND [ARGS]...

  Encode and search a database using Bloom filters

  Bloom filters is a space-efficient probabilistic data structure used to test
  whether an element is a member of a set. It can return false positives, but
  never false negatives.

Options:
  --help  Show this message and exit.

Commands:
  contains  Test if text string may be contained in an SQLite database...
  encode    Encode an SQLite database in bloom filters
  search    Search an SQLite database encoded in bloom filters
```

##### avid-tools encoding bloom contains

```
Usage: avid-tools encoding bloom contains [OPTIONS] TEXT

  Test if text string may be contained in an SQLite database encoded in bloom
  filters

Options:
  --ignore_tables TEXT          Name(s) of tables to ignore
  --ignore_columns TEXT         Name(s) of columns to ignore
  --ignore_table_regexes TEXT   Regex(es) of tables to ignore
  --ignore_column_regexes TEXT  Regex(es) of columns to ignore
  --help                        Show this message and exit.
```

##### avid-tools encoding bloom encode

```
Usage: avid-tools encoding bloom encode [OPTIONS] DB_PATH

  Encode an SQLite database in bloom filters

Options:
  --ignore_tables TEXT          Name(s) of tables to ignore
  --ignore_columns TEXT         Name(s) of columns to ignore
  --ignore_table_regexes TEXT   Regex(es) of tables to ignore
  --ignore_column_regexes TEXT  Regex(es) of columns to ignore
  --help                        Show this message and exit.
```

##### avid-tools encoding bloom search

```
Usage: avid-tools encoding bloom search [OPTIONS] DB_PATH TEXT

  Search an SQLite database encoded in bloom filters

Options:
  --ignore_tables TEXT          Name(s) of tables to ignore
  --ignore_columns TEXT         Name(s) of columns to ignore
  --ignore_table_regexes TEXT   Regex(es) of tables to ignore
  --ignore_column_regexes TEXT  Regex(es) of columns to ignore
  --help                        Show this message and exit.
```

#### avid-tools encoding rowwise

```
Usage: avid-tools encoding rowwise [OPTIONS] COMMAND [ARGS]...

  This program converts SQLite databases into specially encoded files for
  faster search of relationships between tables.

  The first step is to encode the database using the 'encode' command.

  Once the encoded file is ready, the 'search' commands can look for specific
  values.

Options:
  --help  Show this message and exit.

Commands:
  encode  Encode a database.
  search  Search an encoded database.
```


##### avid-tools encoding rowwise encode

```
Usage: avid-tools encoding rowwise encode [OPTIONS] FILE [OUTPUT]

Options:
  --hash NAME     The hash algorithm to use.  [default: md5]
  --sample ROWS   Encode a random sample of ROWS rows for each table.  [x>=1]
  --ignore-types  Do not encode type information.
  --help          Show this message and exit.
```

##### avid-tools encoding rowwise search

```
Usage: avid-tools encoding rowwise search [OPTIONS] FILE

Options:
  --value <SQL-TYPE JSON-VALUE>...
                                  Search for specific values.
  --cell <TABLE ROW COLUMN>       Search for the value in a cell.
  --column <TABLE COLUMN>         Search for all values in column.
  --max-results INTEGER           Stop after INTEGER results.  [x>=1]
  --include-null                  Do not skip null values.
  --show-all-results              Do not aggregate results.
  --help                          Show this message and exit.
```
