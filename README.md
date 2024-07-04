# avid-tools
Simple cli tool to update and fix an avid. In time, this should be made available to all other Danish archives that receive archival versions, as an executable Windows file. It should however also be installable with pipx so as to be able to run on the NAS.

Merges functionality from these repos: `avid-utils`, `convert-qa`, `query-table-xml`, `statutory-qa`, `contextupdater` and `avid` and introduces af few more.

## Global options
- `--root` (path to avid-root. Defaults to '.' so only use, when pwd is not avid-root)
- `--logfile` (persist log in file instead of writing to stdout)
- `--version` (print version and exit)
- `--help` (print help and exit. Global option, that can be used with subcommands as well)

## context commands
Commands related to contextDocumentation

### `context add [--position INT] FILEPATH`
The {filepath} must point to a valid tif-file. The position determines where the contextDocument is to be placed. It defaults to last id-folder + 1.

```shell
# Add new context-doc as id 12 (ContextDocumentation/docCollection1/12/1.tif)
$ avid-tools . context add C:/Users/azkb075/Downloads/new_ctx_doc.tif --position 12
```

### `context move SRC-DOC-ID DEST-DOC-ID`
Move a contextDocument to a new position, and re-assign new ids for all affected documents. Finally update fileIndex.xml.

```shell
# Add new context-doc as id 12 (ContextDocumentation/docCollection1/12/1.tif)
$ avid-tools . context add C:/Users/azkb075/Downloads/new_ctx_doc.tif --position 12
```

### `context replace DOC-ID FILEPATH`
Replace a contextDocument with a new tif-file. Update fileIndex.xml with new checksum, and potentially a new extension.

```shell
# Replace context-doc number 12 (ContextDocumentation/docCollection1/12/1.tif) with tif at filepath
$ avid-tools . context replace 12 C:/Users/azkb075/Downloads/new_ctx_doc.tif
```

### `context remove DOC-ID`
Remove a given contextDocument, and re-assign new ids for all affected documents. Finally update fileIndex.xml.

```shell
# Remove context-doc with id 12 (ContextDocumentation/docCollection1/12)
$ avid-tools . context remove 12
```

## table commands
Commands related to the *table{id}.xml* files of the avid.

### `table trim-values [--table ID]`
Trim any whitespace at the beginning or end of any text-content in the *table{id}.xml* files. Use --table to restrict the trim to certain table(s). Update fileIndex.xml.

```shell
# Trim whitespace from tables 4 and 5
$ avid-tools . table trim-values --table 4 --table 5
```

### `table update-row-count [--table ID]`
Calculate and insert correct row-count number for each table in tableIndex.xml. Use --table to restrict the re-calculation to certain table(s). Update fileIndex.xml

```shell
# Update row-count for table 4
$ avid-tools . table update-row-count --table 4
```

### docs
Commands related to the docs in the docCollections
- `docs replace {docCollection-id} {doc-id} {filepath}` (requires a file in a valid archival format)
- `docs extensions` (print histogram of original file-extensions)
  - `--head {int}` (maximum # of extension to print, sorted by count descending)
  - `--reverse` (sort output by count ascending)
  - `--output-dir {filepath}` (output to file instead of stdout)
- `docs checksums` (print checksums+count for each checksum with count > 1)
  - `--head {int}` (maximum # of checksums to print, sorted by count descending)
  - `--reverse` (sort output by count ascending)
  - `--output-dir {filepath}` (output to file instead of stdout)
- `docs sample {output-dir}` (copy samples of each fileextension to output-dir)
  - `--type` (selection-principle. Enum: random, largest, smallest, oldest, newest, extreme)
  - `--max-size {int}` (defaults to 5)
  - `--min-size {int}` (defaults to 1)

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
