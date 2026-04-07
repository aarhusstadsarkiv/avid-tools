use std::{
    fs::File,
    io::{BufReader, BufWriter},
};

use pyo3::{FromPyObject, exceptions::{PyTypeError, PyValueError}};
use regex::Regex;
use rusqlite::{Connection, ToSql, types::ValueRef};
use serde::{Deserialize, Serialize};

use pyo3::prelude::*;

pub(crate) struct RegexVec(pub Vec<Regex>);

impl<'a, 'py> FromPyObject<'a, 'py> for RegexVec {
    type Error = PyErr;

    fn extract(obj: pyo3::Borrowed<'a, 'py, pyo3::PyAny>) -> Result<Self, Self::Error> {
        let patterns: Vec<String> = obj.extract().map_err(|_| PyTypeError::new_err("expected a list of strings".to_string()))?;

        let regexes = patterns.into_iter().map(|pattern| {
            Regex::new(&pattern).map_err(|err| {
                PyValueError::new_err(format!("invalid regex {pattern:?}: {err}"))
            })
        }).collect::<Result<Vec<_>, PyErr>>()?;

        Ok(RegexVec(regexes))
    }
}

impl Into<Vec<Regex>> for RegexVec {
    fn into(self) -> Vec<Regex> {
        self.0
    }
}

#[derive(Debug, Clone)]
pub(crate) struct IgnoreMatcher {
    pub ignore_tables: Vec<String>,
    pub ignore_columns: Vec<String>,
    pub ignore_table_regexes: Vec<Regex>,
    pub ignore_column_regexes: Vec<Regex>,
}

impl IgnoreMatcher {
    fn should_ignore_table(&self, table: &str) -> bool {
        let normalized = simplify_string(table);

        self.ignore_tables.iter().any(|t| t == &normalized)
            || self
                .ignore_table_regexes
                .iter()
                .any(|re| re.is_match(table) || re.is_match(&normalized))
    }

    fn should_ignore_column(&self, column: &str) -> bool {
        let normalized = simplify_string(column);

        self.ignore_columns.iter().any(|c| c == &normalized)
            || self
                .ignore_column_regexes
                .iter()
                .any(|re| re.is_match(column) || re.is_match(&normalized))
    }

    fn should_ignore(&self, table: &str, column: &str) -> bool {
        self.should_ignore_table(table) || self.should_ignore_column(column)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ColumnMeta {
    table: String,
    column: String,
    id: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct ColumnBloom {
    meta: ColumnMeta,
    bit_count: u64,
    hash_count: u32,
    bits: Vec<u64>,
    inserted_count: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct OnDiskIndex {
    columns: Vec<ColumnBloom>,
}

fn simplify_string(text: &str) -> String {
    text.trim().to_lowercase()
}

fn quote_ident(ident: &str) -> String {
    format!("\"{}\"", ident.replace('"', "\"\""))
}

fn get_table_names(conn: &Connection) -> rusqlite::Result<Vec<String>> {
    let mut stmt = conn.prepare(
        "SELECT name
         FROM sqlite_master
         WHERE type = 'table'
           AND name NOT LIKE 'sqlite_%'
         ORDER BY name",
    )?;

    let rows = stmt.query_map([], |row| row.get::<_, String>(0))?;
    rows.collect()
}

fn get_column_names(conn: &Connection, table_name: &str) -> rusqlite::Result<Vec<String>> {
    let sql = format!("PRAGMA table_info({})", quote_ident(table_name));
    let mut stmt = conn.prepare(&sql)?;
    let rows = stmt.query_map([], |row| row.get::<_, String>(1))?;
    rows.collect()
}

fn construct_column_metas(
    conn: &Connection,
    ignore: &IgnoreMatcher,
) -> rusqlite::Result<Vec<ColumnMeta>> {
    let tables = get_table_names(conn)?;
    let mut metas = Vec::new();
    let mut next_id: u16 = 0;

    for table in tables {
        if ignore.should_ignore_table(&table) {
            println!("Skipping table {table}");
            continue;
        }

        let columns = get_column_names(conn, &table)?;
        for column in columns {
            if ignore.should_ignore(&table, &column) {
                println!("Skipping {}.{}", table, column);
                continue;
            }

            metas.push(ColumnMeta {
                table: table.clone(),
                column,
                id: next_id,
            });

            next_id = next_id
                .checked_add(1)
                .expect("Too many columns for u16 ids");
        }
    }

    Ok(metas)
}

fn stream_query_rows<F>(
    conn: &Connection,
    query: String,
    args: Vec<String>,
    mut on_value: F,
) -> rusqlite::Result<()>
where
    F: FnMut(Vec<String>),
{
    let mut stmt = conn.prepare(&query)?;
    let column_count = stmt.column_count();
    let params: Vec<&dyn ToSql> = args.iter().map(|s| s as &dyn ToSql).collect();
    let mut rows = stmt.query(&params[..])?;

    while let Some(row) = rows.next()? {
        let mut values = Vec::with_capacity(column_count);

        for i in 0..column_count {
            match row.get_ref(i)? {
                ValueRef::Text(bytes) => {
                    if let Ok(text) = std::str::from_utf8(bytes) {
                        values.push(text.to_string());
                    }
                }
                ValueRef::Null | ValueRef::Integer(_) | ValueRef::Real(_) | ValueRef::Blob(_) => {}
            }
        }

        on_value(values);
    }

    Ok(())
}

fn stream_text_values<F>(
    conn: &Connection,
    table_name: &str,
    column_name: &str,
    mut on_value: F,
) -> rusqlite::Result<()>
where
    F: FnMut(&str),
{
    let sql = format!(
        "SELECT {} FROM {}",
        quote_ident(column_name),
        quote_ident(table_name)
    );

    let mut stmt = conn.prepare(&sql)?;
    let mut rows = stmt.query([])?;

    while let Some(row) = rows.next()? {
        match row.get_ref(0)? {
            ValueRef::Text(bytes) => {
                if let Ok(text) = std::str::from_utf8(bytes) {
                    let normalized = simplify_string(text);
                    if !normalized.is_empty() {
                        on_value(&normalized);
                    }
                }
            }
            ValueRef::Null | ValueRef::Integer(_) | ValueRef::Real(_) | ValueRef::Blob(_) => {}
        }
    }

    Ok(())
}

fn hash128_parts(s: &str) -> (u64, u64) {
    let hash = blake3::hash(s.as_bytes());
    let bytes = hash.as_bytes();

    let h1 = u64::from_le_bytes(bytes[0..8].try_into().unwrap());
    let mut h2 = u64::from_le_bytes(bytes[8..16].try_into().unwrap());

    if h2 == 0 {
        h2 = 0x9e3779b97f4a7c15;
    }

    (h1, h2)
}

fn bloom_params(expected_items: u64, false_positive_rate: f64) -> (u64, u32) {
    let n = expected_items.max(1) as f64;
    let p = false_positive_rate.clamp(1e-9, 0.5);

    let m = (-(n * p.ln()) / (std::f64::consts::LN_2 * std::f64::consts::LN_2)).ceil() as u64;
    let k = ((m as f64 / n) * std::f64::consts::LN_2).ceil() as u32;

    (m.max(64), k.max(1))
}

fn bitvec_words(bit_count: u64) -> usize {
    bit_count.div_ceil(64) as usize
}

fn set_bit(bits: &mut [u64], bit_index: u64) {
    let word = (bit_index / 64) as usize;
    let offset = (bit_index % 64) as u32;
    bits[word] |= 1u64 << offset;
}

fn test_bit(bits: &[u64], bit_index: u64) -> bool {
    let word = (bit_index / 64) as usize;
    let offset = (bit_index % 64) as u32;
    (bits[word] & (1u64 << offset)) != 0
}

fn bloom_positions(h1: u64, h2: u64, bit_count: u64, hash_count: u32) -> impl Iterator<Item = u64> {
    (0..hash_count).map(move |i| h1.wrapping_add((i as u64).wrapping_mul(h2)) % bit_count)
}

fn estimate_unique_text_count(
    conn: &Connection,
    table_name: &str,
    column_name: &str,
) -> rusqlite::Result<u64> {
    let sql = format!(
        "SELECT COUNT(DISTINCT {}) FROM {} WHERE {} IS NOT NULL",
        quote_ident(column_name),
        quote_ident(table_name),
        quote_ident(column_name)
    );

    conn.query_row(&sql, [], |row| row.get::<_, i64>(0))
        .map(|v| v.max(0) as u64)
}

fn build_index(
    conn: &Connection,
    false_positive_rate: f64,
    ignore: &IgnoreMatcher,
) -> rusqlite::Result<OnDiskIndex> {
    let metas = construct_column_metas(conn, ignore)?;
    let total = metas.len();
    let mut columns = Vec::with_capacity(total);

    for (i, meta) in metas.into_iter().enumerate() {
        println!(
            "{}/{}: Encoding {}.{}",
            i + 1,
            total,
            meta.table,
            meta.column
        );

        let expected_items = estimate_unique_text_count(conn, &meta.table, &meta.column)?.max(1);

        let (bit_count, hash_count) = bloom_params(expected_items, false_positive_rate);
        let mut bits = vec![0u64; bitvec_words(bit_count)];

        stream_text_values(conn, &meta.table, &meta.column, |value| {
            let (h1, h2) = hash128_parts(value);

            for pos in bloom_positions(h1, h2, bit_count, hash_count) {
                set_bit(&mut bits, pos);
            }
        })?;

        println!(
            "    -> expected distinct: {}, bits: {}, hashes: {}",
            expected_items, bit_count, hash_count
        );

        columns.push(ColumnBloom {
            meta,
            bit_count,
            hash_count,
            bits,
            inserted_count: expected_items,
        });
    }

    Ok(OnDiskIndex { columns })
}

fn save(index: &OnDiskIndex) -> std::io::Result<()> {
    let file = File::create("data.bin")?;
    let mut writer = BufWriter::new(file);
    bincode::serialize_into(&mut writer, index).map_err(std::io::Error::other)?;
    Ok(())
}

fn load() -> std::io::Result<OnDiskIndex> {
    let file = File::open("data.bin")?;
    let mut reader = BufReader::new(file);
    let index = bincode::deserialize_from(&mut reader).map_err(std::io::Error::other)?;
    Ok(index)
}

fn construct_encoding(conn: &Connection, ignore: &IgnoreMatcher) {
    let false_positive_rate = 0.001;

    match build_index(conn, false_positive_rate, ignore) {
        Ok(index) => {
            println!("Saving index with {} columns", index.columns.len());
            if let Err(e) = save(&index) {
                eprintln!("Failed to save index: {e}");
            }
        }
        Err(e) => eprintln!("Failed to build index: {e}"),
    }
}

pub(crate) fn contains_loaded(search_text: String, ignore: &IgnoreMatcher) {
    let index = match load() {
        Ok(index) => index,
        Err(e) => {
            eprintln!("Failed to load data.bin: {e}");
            return;
        }
    };

    let normalized = simplify_string(&search_text);
    let (h1, h2) = hash128_parts(&normalized);

    let mut found_any = false;

    for column in &index.columns {
        if ignore.should_ignore(&column.meta.table, &column.meta.column) {
            continue;
        }

        let maybe_present = bloom_positions(h1, h2, column.bit_count, column.hash_count)
            .all(|pos| test_bit(&column.bits, pos));

        if maybe_present {
            println!(
                "Maybe found in {}.{}",
                column.meta.table, column.meta.column
            );
            found_any = true;
        }
    }

    if !found_any {
        println!("No match found!");
    }
}

pub(crate) fn search_loaded(search_text: String, db_path: String, ignore: &IgnoreMatcher) {
    let index = match load() {
        Ok(index) => index,
        Err(e) => {
            eprintln!("Failed to load data.bin: {e}");
            return;
        }
    };

    let normalized = simplify_string(&search_text);
    let (h1, h2) = hash128_parts(&normalized);

    let conn = create_connection(db_path).unwrap();

    let mut found_any = false;
    for column in &index.columns {
        if ignore.should_ignore(&column.meta.table, &column.meta.column) {
            continue;
        }

        let maybe_present = bloom_positions(h1, h2, column.bit_count, column.hash_count)
            .all(|pos| test_bit(&column.bits, pos));

        if maybe_present {
            println!(
                "Maybe found in {}.{}",
                column.meta.table, column.meta.column
            );

            let query = format!(
                "SELECT * FROM {} WHERE LOWER(TRIM({})) = ?1",
                quote_ident(&column.meta.table),
                quote_ident(&column.meta.column)
            );

            let args: Vec<String> = vec![normalized.clone()];
            stream_query_rows(&conn, query, args, |row| {
                println!(" - Found row: {:#?}", row);
            })
            .unwrap();

            found_any = true;
        }
    }

    if !found_any {
        println!("No match found!");
    }
}

fn create_connection(path: String) -> Result<Connection, rusqlite::Error> {
    Connection::open(path)
}

pub(crate) fn create_encoded_database(
    db_path: String,
    ignore: &IgnoreMatcher
) {
    println!("Constructing Bloom-filter encoding...");

    match create_connection(db_path) {
        Ok(conn) => construct_encoding(&conn, ignore),
        Err(e) => eprintln!("Could not connect to database: {e}"),
    }
}
