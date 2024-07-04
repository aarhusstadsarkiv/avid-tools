# avid-tools
Simple cli tool to update and fix an avid. In time, this should be made available to all other Danish archives that receive archival versions, as an executable Windows file. It should however also be installable with pipx so as to be able to run on the NAS.

Merges functionality from these repos: `avid-utils`, `convert-qa`, `query-table-xml`, `statutory-qa`, `contextupdater` and `avid` and introduces af few more.

## Global options
- `--logfile` (persist log in file instead of writing to stdout)
- `--root` (path to avid-root. Defaults to '.' so only use, when pwd is not avid-root)
- `--version` (print version and exit)
- `--help` (print help and exit. Global option, that can be used with subcommands as well)

## Subcommands
### context
Commands related to contextDocumentation
- `context add {filepath}` (requires a valid tif-file)
  - `--position` (defaults to last+1)
- `context move {src-doc-id} {dest-doc-id}`
- `context replace {doc-id} {filepath}` (requires a valid tif-file)
- `context remove {doc-id}`

### tables
Commands related to the xml-tables of the avid
- `tables trim-values` (remove any whitespace at the end of any tag-content)
- `--table {id}` (only trim this table. Repeatable)
- `tables update-row-count` (calculate and insert correct # of rows)
- `--table {id}` (only calculate rows for this table. Repeatable)

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
