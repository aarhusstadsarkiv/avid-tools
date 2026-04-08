use std::{fs::File, io::BufReader, path::Path};

use quick_xml::{events::Event, Reader};

pub fn search_xml(xml_path: &Path, substring: String) -> Result<(), Box<dyn std::error::Error>> {
    assert!(xml_path.exists());

    let file = File::open(xml_path)?;
    let reader = BufReader::new(file);

    let mut reader = Reader::from_reader(reader);
    reader.config_mut().trim_text(true);

    let mut row: Vec<String> = Vec::new();
    let mut buf = Vec::new();

    let mut has_match: bool = false;

    loop {
        buf.clear();
        match reader.read_event_into(&mut buf).unwrap() {
            Event::Eof => break,
            Event::End(ref e) => {
                if e.name().as_ref() == b"row" {
                    if has_match {
                        println!("Rows: {:?}", row);
                        has_match = false;
                    }

                    row.clear();
                }
            }
            Event::Text(ref e) => {
                let text = e.decode().unwrap().into_owned();
                row.push(text.clone());
                if text.contains(&substring) || text == substring {
                    has_match = true;
                }
            }
            Event::Empty(ref e) => {
                if e.name().0[0] == b'c' {
                    row.push("".to_string());
                }
            }
            _ => {}
        }
    }

    Ok(())
}
