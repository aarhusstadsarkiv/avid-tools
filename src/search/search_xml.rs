use crate::search::read_index;
use crate::search::read_xml;

use std::path::Path;

use read_index::read_tables;
use read_xml::search_xml;

pub(crate) fn search_tables(table_path: &Path, search_value: String) -> Result<(), Box<dyn std::error::Error>> {
    let folder_path = table_path.parent().unwrap().parent().unwrap().join("Tables");

    let tables = read_tables(&table_path)?;

    for table in tables {
        println!("Searching table: {}, table id: {}", table.name, table.folder);
        let table_xml_path = folder_path.join(format!("{}/{}.xml", table.folder, table.folder));
        search_xml(&table_xml_path, search_value.clone())?;
    }

    Ok(())
}
