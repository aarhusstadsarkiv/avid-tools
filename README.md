# avid-tools
Simple cli tool to update and fix an avid. In time, this should be made available to all other Danish archives that receive archival versions, as an executable Windows file.

## Commands
- **context**
  - `add {filepath}`
    - `--position`
  - `move {src-id} {dest-id}`
  - `replace {id} {filepath}`
  - `remove {id}`

- **tables**
  - `trim-values` (remove any whitespace at the end of any tag-content)
    - `--table {id}` (only trim this table. Repeatable)
  - `search {term(s)}`
    - `--table {id}` (only search this table. Repeatable)
  - `calculate-rows` (calculate correct # of rows)
    - `--table {id}` (only calculate rows for this table. Repeatable)

- **files**
  - `replace {file-id} {filepath}` (docCollection-id is calculated implicitly)
  - `histogram` (print histogram of original file-extensions)
    - `--output-file {filepath}` (output to file instead of stdout)
