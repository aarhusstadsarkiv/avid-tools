# avid-tools
cli tool to update, fix and test certain elements of an archival version (AVID). In time, this should be made available to other Danish archives that receive archival versions, as an executable Windows file. It should however also be installable with pipx so as to be able to run on the NAS.

Merges functionality from these repos: `avid-utils`, `convert-qa`, `query-table-xml`, `statutory-qa`, `contextupdater` and `avid` and introduces af few more.

## Global options
- `--root` (path to avid-root, e.g. 'AVID.AARS.61.1'. Defaults to '.' so only use, when pwd is not avid-root)
- `--logfile` (persist log in file instead of writing to stdout)
- `--dry-run` (do a test run, instead of actually adding, moving, replacing, deleting, updating any files)
- `--version` (print version and exit)
- `--help` (print help and exit. Global option, that can be used with subcommands as well)

## context commands
Commands related to contextDocumentation

### `context add [--position INT] FILEPATH`
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

### `context replace DOC-ID FILEPATH`
Replace a contextDocument with a new tif-file. Update fileIndex.xml with new checksum, and potentially a new extension.

```shell
# Replace context-doc number 12 (ContextDocumentation/docCollection1/12/1.tif) with a new tif file
$ avid-tools . context replace 12 C:/Users/azkb075/Downloads/new_ctx_doc.tif
```

### `context remove DOC-ID`
Remove a given contextDocument, and re-assign new ids for all affected documents. Finally update contextDocumentationIndex.xml and fileIndex.xml.

```shell
# Remove context-doc with id 12 (ContextDocumentation/docCollection1/12)
$ avid-tools . context remove 12
```

## table commands
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

## doc commands
Commands related to the docs in the docCollections

### `doc replace DOC-COLLECTION DOC-ID FILEPATH`
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
# Copy 10 most frequent checksums to a csv-file
$ avid-tools doc sample --extension lwp --max 20 C:/Users/azkb075/Downloads/samples/
...
$ ls C:/Users/azkb075/Downloads/samples/
lwp
├── {docId}__regneark1.lwp
├── {docId}__Budget2021-Kopi.lwp
...
```

### info
Fetch "metadata" from the current avid.
- `info {type}` (enum: archive, context, tables, table, view)

### search
Fulltext search in table{id}.xml files
- `search {query-string}` (using LIKE syntax)
- `--table {id}` (only search this table. Repeatable)
- `--column {id}` (only search this column ('c{id}'). Repeatable)

More commands will follow, maybe...

## Examples
```shell
# Add new context-doc as id 12 (ContextDocumentation/docCollection1/12/1.tif)
avid-tools context add C:/Users/azkb075/Downloads/new_ctx_doc.tif --position 12
```
## Questions
- how to add or replace an index-file, or perhaps an schema-file?
