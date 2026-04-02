use std::{collections::HashMap, fmt, fs::File, io::{self, BufReader}, path::Path};

use glob::glob;
use quick_xml::{Reader, events::Event};

type Schema = HashMap<Vec<u8>, FieldType>;
type Result<T> = std::result::Result<T, Error>;

enum FieldType {
    String,
    Integer,
    Decimal,
    Float,
    Double,
    Boolean,
    HexBinary,
    Date,
    Time,
    DateTime,
    Duration,
}

#[derive(Debug)]
pub enum Error {
    Io(io::Error),
    Xml(quick_xml::Error),
    UnknownFieldType(Vec<u8>),
    SchemaEmpty
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Io(e) => write!(f, "I/O error: {e}"),
            Error::Xml(e) => write!(f, "XML error: {e}"),
            Error::UnknownFieldType(v) => {
                write!(f, "Unknown field type: {:?}", String::from_utf8_lossy(v))
            }
            Error::SchemaEmpty => {
                write!(f, "No validation types given")
            }
        }
    }
}

impl std::error::Error for Error { }

impl From<io::Error> for Error {
    fn from(value: io::Error) -> Self {
        Error::Io(value)
    }
}

impl From<quick_xml::Error> for Error {
    fn from(value: quick_xml::Error) -> Self {
        Error::Xml(value)
    }
}

impl FieldType {
    fn from_value(attrib: &[u8]) -> Result<FieldType> {
        let ty = match attrib {
            b"xs:string" => Self::String,
            b"xs:integer" => Self::Integer,
            b"xs:decimal" => Self::Decimal,
            b"xs:float" => Self::Float,
            b"xs:double" => Self::Double,
            b"xs:boolean" => Self::Boolean,
            b"xs:hexBinary" => Self::HexBinary,
            b"xs:date" => Self::Date,
            b"xs:time" => Self::Time,
            b"xs:dateTime" => Self::DateTime,
            b"xs:duration" => Self::Duration,
            _ => return Err(Error::UnknownFieldType(attrib.to_vec())),
        };

        Ok(ty)
    }
}


fn is_integer(s: &[u8]) -> bool {
    if s.is_empty() {
        return false;
    }

    let (first, rest) = s.split_first().unwrap();

    if *first == b'-' {
        !rest.is_empty() && rest.iter().all(u8::is_ascii_digit)
    } else {
        s.iter().all(u8::is_ascii_digit)
    }
}

fn is_float_like(s: &[u8]) -> bool {
    if s.is_empty() {
        return false;
    }

    if s == b"NaN" || s == b"INF" || s == b"+INF" || s == b"-INF" {
        return true;
    }

    let mut i = 0;

    if matches!(s[i], b'+' | b'-') {
        i += 1;
        if i == s.len() {
            return false;
        }
    }

    let mut seen_digit = false;
    let mut seen_dot = false;
    let mut seen_exp = false;

    while i < s.len() {
        match s[i] {
            b'0'..=b'9' => {
                seen_digit = true;
                i += 1;
            }
            b'.' if !seen_dot && !seen_exp => {
                seen_dot = true;
                i += 1;
            }
            b'e' | b'E' if !seen_exp && seen_digit => {
                seen_exp = true;
                i += 1;

                if i < s.len() && matches!(s[i], b'+' | b'-') {
                    i += 1;
                }

                let exp_start = i;
                while i < s.len() && s[i].is_ascii_digit() {
                    i += 1;
                }

                return i > exp_start && i == s.len();
            }
            _ => return false,
        }
    }

    seen_digit
}

fn is_hex_binary(s: &[u8]) -> bool {
    return s.iter().all(u8::is_ascii_hexdigit) && s.len().is_multiple_of(2);
}

fn is_xsd_date(s: &[u8]) -> bool {
    // Match YYYY-MM-DD
    s.len() == 10
        && s[0..4].iter().all(u8::is_ascii_digit)
        && s[4] == b'-'
        && s[5..7].iter().all(u8::is_ascii_digit)
        && s[7] == b'-'
        && s[8..10].iter().all(u8::is_ascii_digit)
}

fn is_xsd_time(s: &[u8]) -> bool {
    // Match HH:MM:SS
    // or match HH:MM:SS.sss
    match s.len() {
        8 => {
            s[0..2].iter().all(u8::is_ascii_digit)
                && s[2] == b':'
                && s[3..5].iter().all(u8::is_ascii_digit)
                && s[5] == b':'
                && s[6..8].iter().all(u8::is_ascii_digit)
        }
        12 => {
            s[0..2].iter().all(u8::is_ascii_digit)
                && s[2] == b':'
                && s[3..5].iter().all(u8::is_ascii_digit)
                && s[5] == b':'
                && s[6..8].iter().all(u8::is_ascii_digit)
                && s[8] == b'.'
                && s[9..12].iter().all(u8::is_ascii_digit)
        }
        _ => false,
    }
}

fn is_xsd_datetime(s: &[u8]) -> bool {
    // Match YYYY-MM-DDTHH:MM:SS
    // or match YYYY-MM-DDTHH:MM:SS.sss
    match s.len() {
        19 => is_xsd_date(&s[0..10]) && s[10] == b'T' && is_xsd_time(&s[11..19]),
        23 => is_xsd_date(&s[0..10]) && s[10] == b'T' && is_xsd_time(&s[11..23]),
        _ => false,
    }
}

fn is_xsd_duration(s: &[u8]) -> bool {
    let mut i = 0;

    if s.get(i) != Some(&b'P') {
        return false;
    }
    i += 1;

    i = match read_digits(s, i) {
        Some(next) if s.get(next) == Some(&b'Y') => next + 1,
        _ => return false,
    };

    i = match read_digits(s, i) {
        Some(next) if s.get(next) == Some(&b'M') => next + 1,
        _ => return false,
    };

    i = match read_digits(s, i) {
        Some(next) if s.get(next) == Some(&b'D') => next + 1,
        _ => return false,
    };

    if s.get(i) != Some(&b'T') {
        return false;
    }
    i += 1;

    i = match read_digits(s, i) {
        Some(next) if s.get(next) == Some(&b'H') => next + 1,
        _ => return false,
    };

    i = match read_digits(s, i) {
        Some(next) if s.get(next) == Some(&b'M') => next + 1,
        _ => return false,
    };

    i = match read_digits(s, i) {
        Some(next) if s.get(next) == Some(&b'S') => next + 1,
        _ => return false,
    };

    i == s.len()
}

fn read_digits(s: &[u8], mut i: usize) -> Option<usize> {
    let start = i;

    while i < s.len() && s[i].is_ascii_digit() {
        i += 1;
    }

    if i > start { Some(i) } else { None }
}

impl FieldType {
    fn valid_value(&self, value: &[u8]) -> bool {
        // Check for whitespace in front and at the end of the value
        if let (Some(first), Some(last)) = (value.first(), value.last()) {
            if u8::is_ascii_whitespace(first) || u8::is_ascii_whitespace(last) {
                return false;
            }
        }

        // Perform field type format checks
        match self {
            FieldType::String => true, // Per default always a string
            FieldType::Integer => is_integer(value),
            FieldType::Decimal => is_float_like(value),
            FieldType::Float => is_float_like(value),
            FieldType::Double => is_float_like(value),
            FieldType::Boolean => matches!(value, b"true" | b"false" | b"1" | b"0"),
            FieldType::HexBinary => is_hex_binary(value),
            FieldType::Date => is_xsd_date(value),
            FieldType::Time => is_xsd_time(value),
            FieldType::DateTime => is_xsd_datetime(value),
            FieldType::Duration => is_xsd_duration(value),
        }
    }
}

fn get_element<'a>(types: &'a Schema, name: &[u8]) -> Option<&'a FieldType> {
    types.get(name)
}

// Read an XSD file and parse the types to a hash map
fn read_xsd(filepath: &Path) -> Result<Schema> {
    let mut ret = Schema::new();

    let f = File::open(filepath)?;
    let bufreader = BufReader::new(f);
    let mut reader = Reader::from_reader(bufreader);

    let mut buf = Vec::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) | Ok(Event::Empty(e)) => {
                let name_attr = e
                    .attributes()
                    .flatten()
                    .find(|tag| tag.key.as_ref() == b"name" && tag.value.first() == Some(&b'c'));
                let type_attr = e
                    .attributes()
                    .flatten()
                    .find(|tag| tag.key.as_ref() == b"type");

                if let (Some(attr_name), Some(type_attr)) = (name_attr, type_attr) {
                    let cid = attr_name.value.as_ref().to_vec();
                    let tagtype = type_attr.value.as_ref();

                    ret.insert(cid, FieldType::from_value(tagtype)?);
                }
            }
            Ok(Event::Eof) => break,
            _ => (),
        }

        buf.clear();
    }

    Ok(ret)
}

// Check if the XSD formats are well formed and no whitespaces present in front or
// in the end of text
fn typecheck_xml(filepath: &Path, xsdpath: &Path) -> Result<()> {
    let f = File::open(filepath)?;
    let bufreader = BufReader::new(f);
    let mut reader = Reader::from_reader(bufreader);

    let xsdtypes = read_xsd(&xsdpath)?;

    if xsdtypes.is_empty() {
        return Err(Error::SchemaEmpty);
    }

    let mut buf = Vec::new();
    let mut inner_buf = Vec::new();
    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Start(e)) => {
                let name = e.name();
                if let Some(xsdtype) = get_element(&xsdtypes, &name.as_ref()) {
                    if let Ok(Event::Text(text)) = reader.read_event_into(&mut inner_buf) {
                        if !xsdtype.valid_value(&text.as_ref()) {
                            println!(
                                "'{}' is invalid for the given type!",
                                text.decode().unwrap()
                            );
                        }
                    }
                }
            }
            Ok(Event::Eof) => break,
            _ => (),
        }

        buf.clear();
        inner_buf.clear();
    }

    Ok(())
}

// Read all tables and validate type format
pub(crate) fn all_tables() -> Result<Vec<String>> {
    let mut errors: Vec<String> = Vec::new();

    for entry in glob("Tables/**/table*.xml").expect("Found no table XML files") {
        match entry {
            Ok(path) => {
                let xsd_path = path.parent().unwrap().join(format!(
                    "{}.xsd",
                    path.file_stem().unwrap().to_str().unwrap()
                ));

                println!("Validate {}", path.file_stem().unwrap().to_str().unwrap());

                match typecheck_xml(&path, &xsd_path) {
                    Ok(()) => {}
                    Err(e) => errors.push(format!("Could not validate {:?}, {:?}", path, e).to_string()),
                }
            }
            Err(e) => errors.push(format!("{:?}", e)),
        }
    }

    Ok(errors)
}

#[test]
fn test_is_date() {
    assert!(is_xsd_date("2017-12-24".as_bytes()));
    assert_eq!(is_xsd_date("s2017-12-24".as_bytes()), false);
    assert_eq!(is_xsd_date("2017-12-242323".as_bytes()), false);
}

#[test]
fn test_is_time() {
    assert!(is_xsd_time("12:23:12".as_bytes()));
    assert!(is_xsd_time("12:23:12.123".as_bytes()));

    assert_eq!(is_xsd_time("244:12:23".as_bytes()), false);
    assert_eq!(is_xsd_time("24:12:23.12312".as_bytes()), false);
    assert_eq!(is_xsd_time("ad".as_bytes()), false);
}

#[test]
fn test_is_datetime() {
    assert!(is_xsd_datetime("2017-12-24T23:23:23".as_bytes()));
    assert!(is_xsd_datetime("2017-12-24T23:23:23.123".as_bytes()));

    assert_eq!(is_xsd_datetime("222017-12-24T23:23:23".as_bytes()), false);
    assert_eq!(is_xsd_datetime("2017-12-24T23:23:2322".as_bytes()), false);
}

#[test]
fn test_is_duration() {
    assert!(is_xsd_duration("P3Y7M21DT3H2M45S".as_bytes()));
    assert_eq!(
        is_xsd_duration("P33333333Y7M21DT3H2M45S55".as_bytes()),
        false
    );
    assert_eq!(is_xsd_duration("P3Y7M21DT3H2M45S23232".as_bytes()), false);
}

#[test]
fn test_is_integer() {
    assert!(is_integer("12312312381241".as_bytes()));
    assert_eq!(is_integer("12312312381241.23".as_bytes()), false);
    assert_eq!(is_integer("++12312312381241".as_bytes()), false);
}

#[test]
fn test_decimal_numbers() {
    assert!(is_float_like("12312312.23231".as_bytes()));

    assert!(is_float_like("12312312".as_bytes()));

    assert_eq!(is_float_like(".12312312.23231".as_bytes()), false);
    assert_eq!(is_float_like("12312312.23231e".as_bytes()), false);
    assert_eq!(is_float_like("12312312.23231e-".as_bytes()), false);
}

#[test]
fn test_hexadecimal() {
    assert!(is_hex_binary("CC31E216BC2912DEB1E5CB196923B12E".as_bytes()));
    assert_eq!(
        is_hex_binary("CC31E216BC2912DEB1E5CB196923B12Easdawfna".as_bytes()),
        false
    );
}
