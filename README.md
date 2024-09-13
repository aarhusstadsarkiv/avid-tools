# avid-tools
cli tool to update, fix and test certain elements of an archival version (AVID). In time, this should be made available to other Danish archives that receive archival versions, as an executable Windows file. It should however also be installable with pipx so as to be able to run on the NAS.

Merges functionality from these repos: `avid-utils`, `convert-unmanaged`, `convert-qa`, `query-table-xml`, `statutory-qa`, `contextupdater` and `avid` and introduces af few more.

## Global argument
- `root` (path to avid-root, e.g. 'C:\AVID.AARS.61.1' or '.'

## Global options
[//]: # (- `--logfile` &#40;persist log in file instead of writing to stdout&#41;)
[//]: # (- `--dry-run` &#40;do a test run, instead of actually adding, moving, replacing, deleting, updating any files&#41;)
- `--version` (print version and exit)
- `--help` (print help and exit. Global option, that can be used with subcommands as well)

## context subcommand
Commands related to contextDocumentation

### `context add [--position INT] FILEPATH METADATA`
The {filepath} must point to a valid tif-file. The position determines where the contextDocument is to be placed. It defaults to last id-folder + 1.

```shell
# Add new context-doc as id 12 (ContextDocumentation/docCollection1/12/1.tif)
$ avid-tools . context add --position 12 C:/Users/azkb075/Downloads/new_ctx_doc.tif
```

### `context move SRC-DOC-ID DEST-DOC-ID`
Move a contextDocument to a new position, and re-assign new ids for all affected documents. Finally update fileIndex.xml.

```shell
# Move contextDocument 12 to position 8. Update contextDocumentationIndex.xml and fileIndex.xml.
$ avid-tools . context move 12 8
```

### `context update DOC-ID [--file FILEPATH] [--metadata METADATA]`
Update a contextDocument with a new tif-file. Update fileIndex.xml with new checksum, and potentially a new extension.

```shell
# Update context-doc number 12 (ContextDocumentation/docCollection1/12/1.tif) with a new tif file
$ avid-tools . context update 12 C:/Users/azkb075/Downloads/new_ctx_doc.tif
```

### `context delete DOC-ID`
Delete a given contextDocument, and re-assign new ids for all affected documents. Finally update contextDocumentationIndex.xml and fileIndex.xml.

```shell
# Delete context-doc with id 12 (ContextDocumentation/docCollection1/12)
$ avid-tools . context delete 12
```

## table subcommand
Commands related to the *table{id}.xml* files of the avid.

### `table trim-values [--table ID]`
Trim any whitespace at the beginning or end of any text-content in the *table{id}.xml* files. Use `--table` to restrict the trim to certain table(s). Update fileIndex.xml.

```shell
# Trim whitespace from tables 4 and 5
$ avid-tools . table trim-values --table 4 --table 5
```

### `table update-row-count [--table ID]`
Calculate and insert correct row-count number for each table in tableIndex.xml. Use `--table` to restrict the re-calculation to certain table(s). Update fileIndex.xml

```shell
# Update row-count for table 4
$ avid-tools . table update-row-count --table 4
```

## doc subcommand
Commands related to the docs in the docCollections

### `doc replace DOC-COLLECTION DOC-ID FILEPATH` (postponed))
Replace a document (one or more files) with a new document (one or more files). FILEPATH points to a folder with the new file(s). If the name of one or more of the files in FILEPATH is not named according to the demands of incremental integers, use its filename as original filename (<oFn>) in docIndex.xml. Update fileIndex.xml with new checksum(s), and possibly new extension(s) and entries. 

```shell
# Replace documentId 31253 in docCollection 4 with a new file.
$ avid-tools . doc replace --docCollection 4 --docId 31253 C:/Users/azkb075/Downloads/new_doc/
```

### `doc extensions [--head INT] [--reverse] [--csv-file FILEPATH]`
Output a list of (extension, count, docId) for all file extensions in the <oFn>-tag in docIndex.xml, sorted by count DESC. Use `--head` to limit the number of rows to output. Use `--reverse` to sort by count ASC. Use `--csv-file` to save output a csv-file.

```shell
# Output top 20 original extensions to a csv-file
$ avid-tools doc extension --head 20 --csv-file C:/Users/azkb075/Downloads/top-20-original-extensions.csv
```

### `doc checksums [--head INT] [--reverse] [--csv-file FILEPATH]`
Output a list of (checksum, count, docId) for all duplicate checksums in the <md5>-tag in fileIndex.xml, sorted by count DESC. Use `--head` to limit the number of rows to output. Use `--reverse` to sort by count ASC. Use `--csv-file` to save output a csv-file.

```shell
# Output the 10 most frequent checksums to a csv-file
$ avid-tools doc checksums --head 10 --csv-file C:/Users/azkb075/Downloads/top-10-checksums.csv
```

### `doc sample [--extension STRING] [--max INT] [--min INT] OUTPUT-DIR`
Copies a number of samples of each original file extension (<oFn>) to an given directory. Use `--extension` to sample only specific file extension(s). Use `--max` and `--min` to control the sample size. Defaults to 5. 

```shell
# Copy up to 20 samples of .lpw-files and .123-files to a sample folder
$ avid-tools doc sample --extension lwp --extension 123 --max 20 C:/Users/azkb075/Downloads/samples/
...
$ ls C:/Users/azkb075/Downloads/samples/
lwp
├── {docId}__regneark1.lwp
├── {docId}__Budget2021-Kopi.lwp
123
├── {docId}__lønudgifter.123
├── {docId}__HannePedersen.123
...
```

## index subcommand
Commands to work with the xml files in the `Indices` directory.

### `index [--type ENUM]`
Display metadata from one or more of the index.xml-files. Use `--type` ('archive', 'context', 'tables', 'table', 'view') to display metadata from specific index-files.

```shell
# Display the information in archiveIndex.xml
$ avid-tools . index --type archive
```

### `index update AVID_DIR [--type INDEX_TYPE] INDEX_FILE`
Update an index file (archiveIndex, contextDocumentationIndex, tableIndex) with the xml file at the FILEPATH. Finally update fileIndex.xml.

```shell
# Update archiveIndex.xml
$ avid-tools . index update C:/Users/azkb075/Downloads/archiveIndex.xml
```

## search subcommand
Fulltext search in table{id}.xml files.

### `search [--table INT] [--column STRING] QUERY`
Search for a given substring in the table{id}.xml files. `QUERY` uses LIKE syntax.

```shell
# Search for strings containing 'Gellerupplanen' in tables 4 and 5
$ avid-tools . search --table 4 --table 5 '%Gellerupplanen%'
```
