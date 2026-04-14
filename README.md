# Table of Contents

- [Table of Contents](#table-of-contents)
- [⚠ Important: Custom Installation Required](#-important-custom-installation-required)
  - [Prerequisites](#prerequisites)
  - [Installation Steps](#installation-steps)
- [Python + Rust Integration](#python--rust-integration)
  - [Development](#development)
- [Archive Validation](#archive-validation)
- [Commands](#commands)
  - [avid-tools](#avid-tools)
    - [avid-tools init](#avid-tools-init)
    - [avid-tools context](#avid-tools-context)
      - [avid-tools context add](#avid-tools-context-add)
      - [avid-tools context update](#avid-tools-context-update)
      - [avid-tools context move](#avid-tools-context-move)
      - [avid-tools context delete](#avid-tools-context-delete)
    - [avid-tools tables](#avid-tools-tables)
      - [avid-tools tables search](#avid-tools-tables-search)
      - [avid-tools tables load](#avid-tools-tables-load)
      - [avid-tools tables fastsearch](#avid-tools-tables-fastsearch)
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

> [!IMPORTANT]
> This project uses a **non-standard installation process** because it combines Python and Rust components.

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
maturin build -r

# 4. Install the CLI tool from the generated wheel
uv tool install ./target/wheels/avid_tools*.whl
```

This process builds a Python wheel using Rust and installs it as a CLI tool.

> [!TIP]
> If you get an import error after following the above steps, then make sure you have _deactivated_ the Python virtual environment before running the `avid-tools` command.

# Python + Rust Integration

`avid-tools` employs Rust-written methods for otherwise time intensive Python methods. This is done using the `maturin` build tool. Upon installation, these Rust-written methods become methods of the submodule `avid_tools.feo2xmlprobe`. This submodule has the following methods defined:
* __validate_tables_xsd__: Validate the typeformats of table XML files against their XSD files.
* __encode_database__: Encode a database in a Bloom filter.
* __search_database__: Search a database encoded in a Bloom filter.
* __contains_database__: Check if string is contained in Bloom filter (database).
* __search_tables_xml__: Perform string search across all tablex XML files.

These methods are also described in the Python interface file `avid_tools/feo2xmlprobe.pyi`. This interface file is added such that intellisense programs can, in Python, perform type checks and add DOCSTRINGS to these Rust-written methods.

> [!NOTE]
> `maturin` requires a specific filestructure for Rust+Python integration: Python modules are placed in the python/ folder and Rust code is placed in the src/ folder. An attempt had been made to preserve Python modules in the _"correct"_ src/ placement, but this yielded several errors.

## Development
When developing this tool, use the maturin command `maturin develop`. This command places a shared library file of the Rust-written module in the `python/avid_tools` folder, such that any imports of `feo2xmlprobe` from within the Python files raises no ImportErrors!

# Archive Validation

avid-tools allows for archive validation through its `avid-tools validate` command. This command validates archives according to [bekendtgørelse 128](https://www.retsinformation.dk/eli/lta/2020/128).

> [!NOTE]
> Although the checks are numerous, they are *incomplete*. Filestructure checks and indices checks are solid, however, file content validation of documents are not.

The validation tool performs the following checks:

* __4.b.3__: Mapperne skal navngives som angivet i figur 4.1.
* __4.b.4a__: Et arkiveringsversionsID består af præfikset AVID, en kode på 2-4 bogstaver (som angiver det modtagende arkiv), samt et arkiveringsversionsløbenummer. Elementerne adskilles med punktum.
* __4.c.1a__: Mappen Indices skal indeholde følgende indeksfiler med oplysninger om arkiveringsversionen og dens indhold:
    – fileIndex.xml
    – archiveIndex.xml
    – contextDocumentationIndex.xml
    – tableIndex.xml
* __4.c.1b__: Hvis arkiveringsversionen indeholder digitale dokumenter, lyd, video eller geodata, skal mappen Indices endvidere indeholde følgende indeksfil:
    – docIndex.xml
* __4.c.1c__: Hvis arkiveringsversionen indeholder data, som er skabt i forbindels 
med forskning med anvendelse af videnskabelig metode og er afleveret efter reglerne i bilag 9,
skal mappen Indices endvidere indeholde følgende indeksfil:
    – researchIndex.xml
* __4.c.1d__: Alle indeksfiler skal overholde deres tilhørende skema, jf. bilag 8.
* __4.c.2a__: fileIndex.xml skal indeholde en komplet liste over samtlige filer,
der findes i arkiveringsversionen. fileIndex.xml er dog undtaget fra denne regel.
* __4.c.2b__: [fileIndex.xml] For hver enkelt fil i arkiveringsversionen angives de oplysninger, som fremgår af figur 4.2.
* __4.c.4a__: contextDocumentationIndex.xml skal indeholde et indeks over de dokumenter,
som findes i arkiveringsversionens kontekstdokumentation.
* __4.c.5a__: tableIndex.xml skal indeholde en angivelse af en relationel databasestruktur på 1. normalform 
eller højere. Samtlige tabeller i arkiveringsversionen skal angives.
* __4.c.5b__: »tableIndex.xml« skal overholde det generelle XML-skema »tableIndex.xsd«, jf. 4. F.
* __4.c.6a__: docIndex.xml skal danne forbindelsen mellem hvert dokument og dets placering.
»docIndex.xml« skal desuden indeholde oplysninger om dokumenternes oprindelige filnavne,
filtype i arkiveringsversionen samt eventuelle overordnede dokumenter.
»docIndex.xml« skal ikke indeholde oplysninger om dokumenterne i kontekstdokumentationen.
* __4.c.6b__: For hvert enkelt dokument i docIndex.xml angives de oplysninger, som fremgår af figur 4.4.
* __4.c.7a__: researchIndex.xml skal indeholde angivelse af hovedtabeller og koder for manglende værdier, jf. figur 4.5:
* __4.d.1__: Mappen Tables skal indeholde én mappe for hver tabel i arkiveringsversionen.
* __4.d.2a__: Mappen for en tabel navngives »table[fortløbende nummer]«.
* __4.d2.b__: Den fortløbende nummerering begynder med 1. Foranstillede nuller må ikke anvendes.
* __4.d.3__: Mappen for hver tabel skal indeholde en fil: table[fortløbende nummer]. xml, jf. dog 4. D. 5
* __4.e.1__: Mappen ContextDocumentation skal indeholde en eller flere dokumentsamlingsmapper med kontekstdokumentation, jf. 6. B.
* __4.e.2__: En dokumentsamlingsmappe med kontekstdokumentation må indeholde op til 10.000 dokumentmapper.
* __4.e.5__: Dokumentsamlingsmapperne navngives »docCollection[fortløbende nummer]«, begyndende med 1. Navnet skal være unikt inden for ContextDocumentation.
* __4.e.6__: Et dokuments fil (eller filer) navngives fortløbende med et nummer, begyndende med 1 samt formatets ekstension, jf. 4.G.8
* __4.f.1__: Mappen Schemas skal være opdelt i undermapperne standard og localShared.
* __4.f.2__: Mappen standard skal indeholde skemaer for arkiveringsversionens indeksfiler,
jf. bilag 8, samt W3C standard XML-skema, jf. http://www.w3.org/2001/XMLSchema.xsd.
* __4.f.3__: For skemaerne fileIndex.xsd, archiveIndex.xsd, contextDocumentationIndex.xsd, tableIndex.xsd,
docIndex.xsd, researchIndex.xsd samt W3Cs standard XML-skema gælder, at der altid skal anvendes de skemaer,
som Rigsarkivet stiller til rådighed. Skemaerne og deres navngivning må ikke ændres i arkiveringsversionen.
* __4.g.1__: Mappen Documents skal indeholde én eller flere dokumentsamlingsmapper, dog maksimalt 10.000.
* __4.g.2__: Dokumentsamlingsmapperne navngives »docCollection[fortløbende nummer]«,
begyndende med 1. Navnet skal være unikt inden for Documents.
* __4.g.3__: En dokumentsamlingsmappe må indeholde op til 10.000 dokumentmapper.
* __4.g.8__: Anvendelse af ekstensions
* __5.a.1a__: I overensstemmelse med den tabelstruktur, der i XML-instansen »tableIndex.xml« er defineret for hver tabel,
skal hver tabel findes i en XML-instans navngivet »table[fortløbende nummer]. xml«.
* __5.a.1b__: Den fortløbende nummerering begynder med 1. Foranstillede nuller må ikke anvendes.
* __5.a.2__: Indholdet af de enkelte felter skal renses for eventuelle foran- og efterstillede blanktegn
* __5.b.1__: De standardiserede datatyper, som skal anvendes for tabelindhold, er angivet i figur 5.1.
    De er et uddrag af datatyper fra standarden SQL:1999 repræsenteret som
    datatyper i W3C XML Schema Language 1.0
* __5.c.1__: Tabelindhold skal overholde de angivne datatyper, jf. 5. B. Det følger heraf, at dataindhold i tabelform fra et it-system,
som skal overføres til en arkiveringsversion og som ikke umiddelbart kan overholde dette krav, skal have sit dataindhold konverteret således
* __5.d.1a__: Data i arkiveringsversionens indeksfiler og tabelindhold skal være indkodet som well-formed UTF-8,
    som angivet i ISO/IEC 10646:2003 Annex D og som beskrevet i The Unicode Standard 5.1, kapitel 3.


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

#### avid-tools tables search

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

#### avid-tools tables load

```
Usage: avid-tools tables load [OPTIONS]

  Load table into DB from CSV file

Options:
  --load-file FILE  [required]
  --db-file FILE    [required]
  --help            Show this message and exit.
```

#### avid-tools tables fastsearch

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
