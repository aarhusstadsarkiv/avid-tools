use pyo3::{exceptions::PyRuntimeError, prelude::*};

mod typeformat;

#[pyfunction]
fn validate_tables_xsd() -> PyResult<Vec<String>> {
    typeformat::all_tables().map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

#[pymodule]
fn whitespacevalidate(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate_tables_xsd, m)?)?;
    Ok(())
}
