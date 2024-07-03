# avid-tools
Simple cli tool to update and fix an avid. In time, this should be made available to all other Danish archives that receive archival versions, as an executable Windows file.

## Commands
- **context**
  - `add {filepath}`
    - `--position` (defaults to last+1)
  - `move {src-doc-id} {dest-doc-id}`
  - `replace {doc-id} {filepath}`
  - `remove {doc-id}`

- **tables**
  - `trim-values` (remove any whitespace at the end of any tag-content)
    - `--table {id}` (only trim this table. Repeatable)
  - `search {term(s)}`
    - `--table {id}` (only search this table. Repeatable)
  - `calculate-rows` (calculate correct # of rows)
    - `--table {id}` (only calculate rows for this table. Repeatable)

- **docs**
  - `replace {doc-id} {filepath}` (docCollection-id is calculated implicitly)
  - `histogram` (print histogram of original file-extensions)
    - `--output-file {filepath}` (output to file instead of stdout)
  - `checksum` (print checksums, count for each checksum with count > 1)
    - `--max {int}` (maximum # of checksums to print)
    - `--output-file {filepath}` (output to file instead of stdout)

More commands will follow...

## Questions
- how to add or replace an index-file, or perhaps an schema-file?
