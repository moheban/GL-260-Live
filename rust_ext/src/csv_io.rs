//! Native CSV tokenization and worksheet serialization; Python owns commit policy.

use numpy::PyReadonlyArray2;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::collections::BTreeMap;
use std::fs::File;
use std::io::{BufReader, BufWriter, Write};
use zip::write::SimpleFileOptions;

/// Match Python str.strip, including its extra ASCII information separators.
/// Returns an owned trimmed field; no side effects or errors.
fn trimmed(value: &str) -> String {
    value
        .trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
        .to_owned()
}

/// Parse decoded CSV into a metadata/header prefix and normalized data rows.
/// Inputs are text and Python's CSV field-character limit. Returns both row sets;
/// detaches Python execution and raises on invalid CSV/oversized fields so the
/// authoritative Python parser can retry. Header naming remains Python-owned.
#[pyfunction]
pub fn csv_table_core(
    py: Python<'_>,
    text: String,
    field_limit: usize,
) -> PyResult<(Vec<Vec<String>>, Vec<Vec<String>>)> {
    py.detach(move || {
        let mut reader = csv::ReaderBuilder::new()
            .has_headers(false)
            .flexible(true)
            .from_reader(text.as_bytes());
        let mut prefix = Vec::new();
        let mut rows = Vec::new();
        let mut found = false;
        let mut width = None;
        let mut units = false;
        for record in reader.records() {
            let record = record.map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
            if record.iter().any(|s| s.chars().count() > field_limit) {
                return Err(PyRuntimeError::new_err(
                    "CSV field exceeds Python field limit",
                ));
            }
            let mut row: Vec<String> = record.iter().map(trimmed).collect();
            let nonempty = row.iter().any(|s| !s.is_empty());
            if !found {
                found = row.iter().any(|s| s.eq_ignore_ascii_case("data"));
                prefix.push(row);
            } else if width.is_none() {
                if nonempty {
                    width = Some(row.len());
                }
                prefix.push(row);
            } else if !units {
                if nonempty {
                    units = true;
                }
                prefix.push(row);
            } else if nonempty {
                row.resize(width.unwrap(), String::new());
                rows.push(row);
            }
        }
        if width.is_none() {
            return Err(PyRuntimeError::new_err("CSV data header not found"));
        }
        Ok((prefix, rows))
    })
}

/// Escape XML text and reject prohibited XML 1.0 characters before output.
/// Returns escaped text; raises on invalid characters. No side effects.
fn escaped(value: &str) -> Result<String, String> {
    let mut output = String::with_capacity(value.len());
    for ch in value.chars() {
        match ch {
            '&' => output.push_str("&amp;"),
            '<' => output.push_str("&lt;"),
            '>' => output.push_str("&gt;"),
            '\r' => output.push_str("&#13;"),
            c if (c < '\u{20}' && c != '\n' && c != '\t') || c == '\u{fffe}' || c == '\u{ffff}' => {
                return Err("Illegal XML character in cell".into());
            }
            c => output.push(c),
        }
    }
    Ok(output)
}

/// Convert a zero-based column index to its Excel address letters.
/// Returns the label with no side effects; caller enforces Excel column limits.
fn column_label(index: usize) -> String {
    let mut number = index + 1;
    let mut label = Vec::new();
    while number > 0 {
        number -= 1;
        label.push(b'A' + (number % 26) as u8);
        number /= 26;
    }
    label.reverse();
    String::from_utf8(label).unwrap()
}

/// Independently stream-validate the generated worksheet before Python commits it.
/// Inputs are candidate ZIP path, sheet part and expected data row count. Returns
/// None after checking balanced XML, worksheet closure and consecutive row IDs.
/// Reads only the candidate, releases Python execution and raises on corruption.
#[pyfunction]
pub fn validate_csv_worksheet_core(
    py: Python<'_>,
    path: String,
    part: String,
    rows: usize,
) -> PyResult<()> {
    py.detach(move || -> Result<(), String> {
        use quick_xml::events::Event;
        let input = File::open(path).map_err(|e| e.to_string())?;
        let mut archive = zip::ZipArchive::new(input).map_err(|e| e.to_string())?;
        let sheet = archive.by_name(&part).map_err(|e| e.to_string())?;
        let mut reader = quick_xml::Reader::from_reader(BufReader::new(sheet));
        reader.config_mut().check_end_names = true;
        let mut buffer = Vec::new();
        let mut depth = 0usize;
        let mut expected_row = 1usize;
        let mut root_seen = false;
        let mut root_closed = false;
        loop {
            let event = reader
                .read_event_into(&mut buffer)
                .map_err(|e| e.to_string())?;
            let empty = matches!(&event, Event::Empty(_));
            match event {
                Event::Start(ref node) | Event::Empty(ref node) => {
                    if depth == 0 {
                        if root_seen || node.name().as_ref() != b"worksheet" {
                            return Err("Invalid worksheet root".into());
                        }
                        root_seen = true;
                    }
                    if node.name().as_ref() == b"row" {
                        let attribute = node
                            .try_get_attribute("r")
                            .map_err(|e| e.to_string())?
                            .ok_or("Missing worksheet row number")?;
                        let number = std::str::from_utf8(&attribute.value)
                            .map_err(|e| e.to_string())?
                            .parse::<usize>()
                            .map_err(|e| e.to_string())?;
                        if number != expected_row {
                            return Err("Worksheet row sequence is incomplete".into());
                        }
                        expected_row += 1;
                    }
                    if !empty {
                        depth += 1;
                    }
                }
                Event::End(node) => {
                    depth = depth.checked_sub(1).ok_or("Unexpected XML closing tag")?;
                    if depth == 0 && node.name().as_ref() == b"worksheet" {
                        root_closed = true;
                    }
                }
                Event::Eof => break,
                _ => (),
            }
            buffer.clear();
        }
        if !root_seen || !root_closed || depth != 0 || expected_row != rows + 2 {
            return Err("Worksheet XML or row count is incomplete".into());
        }
        Ok(())
    })
    .map_err(PyRuntimeError::new_err)
}

/// Serialize a string cell using openpyxl-compatible formula/error semantics.
/// Writes XML to the provided stream; truncates to Excel's 32767-character limit.
/// I/O and invalid XML errors propagate, leaving only the temporary file affected.
fn text_cell(writer: &mut impl Write, reference: &str, value: &str) -> Result<(), String> {
    let value: String = value.chars().take(32767).collect();
    let xml = escaped(&value)?;
    if value.starts_with('=') && value.len() > 1 {
        write!(
            writer,
            "<c r=\"{reference}\"><f>{}</f><v></v></c>",
            &xml[1..]
        )
    } else if [
        "#NULL!", "#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#NUM!", "#N/A",
    ]
    .contains(&value.as_str())
    {
        write!(writer, "<c r=\"{reference}\" t=\"e\"><v>{xml}</v></c>")
    } else if value.is_empty() {
        write!(writer, "<c r=\"{reference}\" t=\"inlineStr\"></c>")
    } else {
        write!(
            writer,
            "<c r=\"{reference}\" t=\"inlineStr\"><is><t xml:space=\"preserve\">{xml}</t></is></c>"
        )
    }
    .map_err(|e| e.to_string())
}

/// Generate one worksheet and copy unrelated compressed ZIP entries unchanged.
/// Inputs: source/temp paths, worksheet part, small XML patches, headers, numeric
/// matrix and optional text columns, column kinds/slots, date style and row count.
/// Writes only destination (which must differ from source), returning None on
/// success. Copies owned buffers before detaching Python; all errors raise and
/// Python validates the finished package before any destination replacement.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
pub fn write_csv_workbook_core(
    py: Python<'_>,
    source: String,
    destination: String,
    sheet_part: String,
    patches: BTreeMap<String, Vec<u8>>,
    headers: Vec<String>,
    numeric: PyReadonlyArray2<'_, f64>,
    text: Vec<Vec<Option<String>>>,
    kinds: Vec<String>,
    slots: Vec<usize>,
    date_style: usize,
    rows: usize,
) -> PyResult<()> {
    let numbers = numeric.as_array().to_owned();
    if source == destination
        || headers.is_empty()
        || headers.len() > 16384
        || rows >= 1048576
        || kinds.len() != headers.len()
        || slots.len() != headers.len()
        || numbers.ncols() != rows
    {
        return Err(PyRuntimeError::new_err(
            "Invalid worksheet buffers or destination",
        ));
    }
    for (kind, &slot) in kinds.iter().zip(&slots) {
        let valid = match kind.as_str() {
            "text" => text.get(slot).is_some_and(|v| v.len() == rows),
            "date" | "number" | "bool" => slot < numbers.nrows(),
            _ => false,
        };
        if !valid {
            return Err(PyRuntimeError::new_err("Invalid worksheet column"));
        }
    }
    py.detach(move || -> Result<(), String> {
        let input = File::open(&source).map_err(|e| e.to_string())?;
        let mut archive = zip::ZipArchive::new(input).map_err(|e| e.to_string())?;
        let output = File::create(&destination).map_err(|e| e.to_string())?;
        let mut writer = zip::ZipWriter::new(BufWriter::new(output));
        writer.set_raw_comment(archive.comment().to_vec().into_boxed_slice());
        // Raw-copy leaves existing worksheet XML and compressed payloads intact.
        for index in 0..archive.len() {
            let entry = archive.by_index(index).map_err(|e| e.to_string())?;
            if entry.name() != sheet_part && !patches.contains_key(entry.name()) {
                writer.raw_copy_file(entry).map_err(|e| e.to_string())?;
            }
        }
        let options = SimpleFileOptions::default().compression_method(zip::CompressionMethod::Deflated);
        for (name, bytes) in patches {
            writer.start_file(name, options).map_err(|e| e.to_string())?;
            writer.write_all(&bytes).map_err(|e| e.to_string())?;
        }
        writer.start_file(sheet_part, options).map_err(|e| e.to_string())?;
        // Batch small XML fragments before compression to avoid per-token writes.
        let mut sheet_writer = BufWriter::with_capacity(65536, &mut writer);
        let labels: Vec<String> = (0..headers.len()).map(column_label).collect();
        write!(sheet_writer, "<?xml version=\"1.0\" encoding=\"UTF-8\"?><worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetPr><outlinePr summaryBelow=\"1\" summaryRight=\"1\"/><pageSetUpPr/></sheetPr><dimension ref=\"A1:{}{}\"/><sheetViews><sheetView workbookViewId=\"0\"><pane ySplit=\"1\" topLeftCell=\"A2\" activePane=\"bottomLeft\" state=\"frozen\"/><selection pane=\"bottomLeft\" activeCell=\"A1\" sqref=\"A1\"/></sheetView></sheetViews><sheetFormatPr baseColWidth=\"8\" defaultRowHeight=\"15\"/><sheetData><row r=\"1\">", labels.last().unwrap(), rows + 1).map_err(|e| e.to_string())?;
        for (label, header) in labels.iter().zip(&headers) {
            text_cell(&mut sheet_writer, &format!("{label}1"), header)?;
        }
        write!(sheet_writer, "</row>").map_err(|e| e.to_string())?;
        for row in 0..rows {
            let excel_row = row + 2;
            write!(sheet_writer, "<row r=\"{excel_row}\">").map_err(|e| e.to_string())?;
            for column in 0..headers.len() {
                let reference = format!("{}{excel_row}", labels[column]);
                let slot = slots[column];
                if kinds[column] == "text" {
                    if let Some(value) = &text[slot][row] { text_cell(&mut sheet_writer, &reference, value)?; }
                } else {
                    let value = numbers[(slot, row)];
                    if value.is_finite() {
                        if kinds[column] == "date" {
                            write!(sheet_writer, "<c r=\"{reference}\" s=\"{date_style}\" t=\"n\"><v>{value}</v></c>")
                        } else if kinds[column] == "bool" {
                            write!(sheet_writer, "<c r=\"{reference}\" t=\"b\"><v>{}</v></c>", usize::from(value != 0.0))
                        } else {
                            write!(sheet_writer, "<c r=\"{reference}\" t=\"n\"><v>{value}</v></c>")
                        }.map_err(|e| e.to_string())?;
                    }
                }
            }
            write!(sheet_writer, "</row>").map_err(|e| e.to_string())?;
        }
        write!(sheet_writer, "</sheetData><pageMargins left=\"0.75\" right=\"0.75\" top=\"1\" bottom=\"1\" header=\"0.5\" footer=\"0.5\"/></worksheet>").map_err(|e| e.to_string())?;
        sheet_writer.flush().map_err(|e| e.to_string())?;
        drop(sheet_writer);
        let mut output = writer.finish().map_err(|e| e.to_string())?;
        output.flush().map_err(|e| e.to_string())?;
        Ok(())
    }).map_err(PyRuntimeError::new_err)
}
