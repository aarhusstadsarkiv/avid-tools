use std::{fs::File, io::BufReader, path::Path};

use quick_xml::{events::Event, name::QName, Reader};

#[derive(Clone, Debug)]
pub struct Table {
    pub name: String,
    pub folder: String,
    pub columns: Vec<String>
}


fn read_text<R: std::io::BufRead>(reader: &mut Reader<R>, end: QName) -> Result<String, Box<dyn std::error::Error>> {
    let mut buf = Vec::new();
    let mut text = String::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Text(e) => text.push_str(&e.decode()?),
            Event::End(e) if e.name() == end => break,
            _ => {}
        }
        buf.clear();
    }

    Ok(text)
}

fn read_column<R: std::io::BufRead>(reader: &mut Reader<R>) -> Result<String, Box<dyn std::error::Error>> {
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

fn read_columns<R: std::io::BufRead>(reader: &mut Reader<R>) -> Result<Vec<String>, Box<dyn std::error::Error>> {
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
        columns: Vec::new()
    };

    let mut buf = Vec::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Start(ref e) => {
                match e.name() {
                    QName(b"table") => {
                        table = Table {
                            name: String::new(),
                            folder: String::new(),
                            columns: Vec::new()
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
                }
            }
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

