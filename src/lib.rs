use pyo3::{exceptions::PyRuntimeError, prelude::*};

mod encode;
mod typeformat;

fn construct_ignore_matcher(
    ignore_tables: Option<Vec<String>>,
    ignore_columns: Option<Vec<String>>,
    ignore_table_regexes: Option<encode::RegexVec>,
    ignore_column_regexes: Option<encode::RegexVec>,
) -> encode::IgnoreMatcher {
    encode::IgnoreMatcher {
        ignore_tables: ignore_tables.unwrap_or(Vec::new()),
        ignore_columns: ignore_columns.unwrap_or(Vec::new()),
        ignore_table_regexes: ignore_table_regexes
            .unwrap_or(encode::RegexVec(Vec::new()))
            .into(),
        ignore_column_regexes: ignore_column_regexes
            .unwrap_or(encode::RegexVec(Vec::new()))
            .into(),
    }
}

#[pyfunction]
fn validate_tables_xsd() -> PyResult<Vec<String>> {
    typeformat::all_tables().map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

#[pyfunction]
fn encode_database(
    db_path: String,
    // Args for IgnoreMatcher - Those columns or tables to ignore
    ignore_tables: Option<Vec<String>>,
    ignore_columns: Option<Vec<String>>,
    ignore_table_regexes: Option<encode::RegexVec>,
    ignore_column_regexes: Option<encode::RegexVec>,
) {
    let ignore = construct_ignore_matcher(
        ignore_tables,
        ignore_columns,
        ignore_table_regexes,
        ignore_column_regexes,
    );
    encode::create_encoded_database(db_path, &ignore);
}

#[pyfunction]
fn search_database(
    db_path: String,
    search_text: String,

    // Args for IgnoreMatcher - Those columns or tables to ignore
    ignore_tables: Option<Vec<String>>,
    ignore_columns: Option<Vec<String>>,
    ignore_table_regexes: Option<encode::RegexVec>,
    ignore_column_regexes: Option<encode::RegexVec>,
) {
    let ignore = construct_ignore_matcher(
        ignore_tables,
        ignore_columns,
        ignore_table_regexes,
        ignore_column_regexes,
    );

    encode::search_loaded(search_text, db_path, &ignore);
}

#[pyfunction]
fn contains_database(
    search_text: String,

    // Args for IgnoreMatcher - Those columns or tables to ignore
    ignore_tables: Option<Vec<String>>,
    ignore_columns: Option<Vec<String>>,
    ignore_table_regexes: Option<encode::RegexVec>,
    ignore_column_regexes: Option<encode::RegexVec>,
) {
    let ignore = construct_ignore_matcher(
        ignore_tables,
        ignore_columns,
        ignore_table_regexes,
        ignore_column_regexes,
    );

    encode::contains_loaded(search_text, &ignore);
}

#[pymodule]
fn whitespacevalidate(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_tables_xsd, m)?)?;
    m.add_function(wrap_pyfunction!(encode_database, m)?)?;
    m.add_function(wrap_pyfunction!(search_database, m)?)?;
    m.add_function(wrap_pyfunction!(contains_database, m)?)?;
    Ok(())
}
