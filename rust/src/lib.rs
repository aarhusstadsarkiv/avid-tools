use std::{fs::File, io::BufReader, path::Path};

// use libxml::schemas::SchemaParserContext;
use pyo3::{exceptions::PyValueError, prelude::*};
use quick_xml::{Reader, events::Event, name::QName};

#[derive(Clone, Debug)]
pub struct Table {
    pub name: String,
    pub folder: String,
    pub columns: Vec<String>,
}

fn read_text<R: std::io::BufRead>(
    reader: &mut Reader<R>,
    end: QName,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut buf = Vec::new();
    let mut text = String::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Text(e) => text.push_str(&e.unescape()?),
            Event::End(e) if e.name() == end => break,
            _ => {}
        }
        buf.clear();
    }

    Ok(text)
}

fn read_column<R: std::io::BufRead>(
    reader: &mut Reader<R>,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut buf = Vec::new();
    let mut column_name = String::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Start(ref e) if e.name() == QName(b"name") => {
                column_name = read_text(reader, e.name())?;
            }
            Event::End(e) if e.name() == QName(b"column") => break,
            _ => {}
        }
        buf.clear();
    }

    Ok(column_name)
}

fn read_columns<R: std::io::BufRead>(
    reader: &mut Reader<R>,
) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let mut columns = Vec::new();
    let mut buf = Vec::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Start(ref e) if e.name() == QName(b"column") => {
                columns.push(read_column(reader)?);
            }
            Event::End(e) if e.name() == QName(b"columns") => break,
            _ => {}
        }
        buf.clear();
    }

    Ok(columns)
}

pub fn read_tables(table_path: &Path) -> Result<Vec<Table>, Box<dyn std::error::Error>> {
    let file = File::open(table_path)?;
    let file = BufReader::new(file);

    let mut reader = Reader::from_reader(file);
    reader.config_mut().trim_text(true);

    let mut tables = Vec::new();
    let mut table = Table {
        name: String::new(),
        folder: String::new(),
        columns: Vec::new(),
    };

    let mut buf = Vec::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Start(ref e) => match e.name() {
                QName(b"table") => {
                    table = Table {
                        name: String::new(),
                        folder: String::new(),
                        columns: Vec::new(),
                    };
                }
                QName(b"name") => {
                    if table.name.is_empty() {
                        table.name = read_text(&mut reader, e.name())?;
                    }
                }
                QName(b"columns") => {
                    let columns = read_columns(&mut reader)?;
                    table.columns = columns;
                }
                QName(b"folder") => {
                    table.folder = read_text(&mut reader, e.name())?;
                }
                _ => {}
            },
            Event::End(ref e) => {
                if e.name() == QName(b"table") {
                    tables.push(table.clone());
                }
            }
            Event::Eof => break,
            _ => {}
        }
        buf.clear();
    }

    Ok(tables)
}

pub fn contains_whitespaces(xml_path: &Path) -> Result<bool, Box<dyn std::error::Error>> {
    if !xml_path.exists() {
        return Err("The xml path does not exist".into());
    }

    let file = File::open(xml_path)?;
    let reader = BufReader::new(file);

    let mut reader = Reader::from_reader(reader);

    let mut buf = Vec::new();
    let mut found_any_whitespaces = false;

    loop {
        buf.clear();
        match reader.read_event_into(&mut buf)? {
            Event::Eof => break,
            Event::Text(ref e) => {
                let text = e.unescape()?;
                if !text.trim().is_empty() && text.trim().len() != text.len() {
                    println!("Text is not trimmed: '{}'", text);
                    found_any_whitespaces = true;
                }
            }
            _ => {}
        }
    }

    Ok(found_any_whitespaces)
}

// #[pyfunction]
// fn validate_xsd(table_path: &str) -> PyResult<Vec<String>> {
//     let table_path = Path::new(table_path);
//
//     // Build "<same file name>.xsd" next to the XML file.
//     let xsd_path = table_path.with_extension("xsd");
//
//     let xsd_str = xsd_path
//         .to_str()
//         .ok_or_else(|| PyValueError::new_err("XSD path is not valid UTF-8"))?;
//
//     let xml_str = table_path
//         .to_str()
//         .ok_or_else(|| PyValueError::new_err("XML path is not valid UTF-8"))?;
//
//     let mut parser = SchemaParserContext::from_file(xsd_str);
//
//     let mut validator = match SchemaValidationContext::from_parser(&mut parser) {
//         Ok(v) => v,
//         Err(errors) => {
//             let msgs: Vec<String> = errors.into_iter().map(|e| e.message).collect();
//             return Err(PyValueError::new_err(format!(
//                 "Failed to parse XSD:\n{}",
//                 msgs.join("\n")
//             )));
//         }
//     };
//
//     match validator.validate_file(xml_str) {
//         Ok(()) => Ok(Vec::new()),
//         Err(errors) => {
//             let msgs: Vec<String> = errors.into_iter().map(|e| e.message).collect();
//             Err(PyValueError::new_err(format!(
//                 "XML is not valid:\n{}",
//                 msgs.join("\n")
//             )))
//         }
//     }
// }

#[pyfunction]
fn validate(table_path: String) -> Vec<String> {
    let table_path = Path::new(&table_path);

    let mut invalid_tables: Vec<String> = Vec::new();

    let folder_path = table_path
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("Tables");

    let tables = read_tables(&table_path).unwrap();

    // Create csv file for each table
    for table in tables {
        println!(
            "Vaildating table: {}, table id: {}",
            table.name, table.folder
        );
        let table_xml_path = folder_path.join(format!("{}/{}.xml", table.folder, table.folder));

        match contains_whitespaces(&table_xml_path) {
            Ok(contains) => {
                if contains {
                    println!("Table has whitespaces, {}", table.name);
                    invalid_tables.push(table.name.clone());
                }
            }
            Err(err) => {
                println!("Error occurred! {:#?}", err);
            }
        }
    }

    invalid_tables
}

#[pymodule]
fn whitespacevalidate(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(validate, m)?)?;
    // m.add_function(wrap_pyfunction!(validate_xsd, m)?)?;
    Ok(())
}
