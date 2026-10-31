"""Real PDF regressions for the choice and parent/widget layouts found on Pi."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, DictionaryObject, FloatObject, NameObject, TextStringObject,
)

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from extract_form_field_info import get_field_info


def fixture(path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    rect = ArrayObject([FloatObject(n) for n in (40, 500, 240, 520)])
    font = writer._add_object(DictionaryObject({
        NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/Type1'),
        NameObject('/BaseFont'): NameObject('/Helvetica'),
    }))
    parent = DictionaryObject({
        NameObject('/FT'): NameObject('/Tx'),
        NameObject('/T'): TextStringObject('phone'),
        NameObject('/DA'): TextStringObject('/Helv 10 Tf 0 g'),
    })
    parent_ref = writer._add_object(parent)
    widget = writer._add_object(DictionaryObject({
        NameObject('/Type'): NameObject('/Annot'),
        NameObject('/Subtype'): NameObject('/Widget'),
        NameObject('/Rect'): rect,
        NameObject('/Parent'): parent_ref,
    }))
    parent[NameObject('/Kids')] = ArrayObject([widget])
    choice = writer._add_object(DictionaryObject({
        NameObject('/Type'): NameObject('/Annot'),
        NameObject('/Subtype'): NameObject('/Widget'),
        NameObject('/FT'): NameObject('/Ch'),
        NameObject('/T'): TextStringObject('option'),
        NameObject('/Rect'): rect,
        NameObject('/DA'): TextStringObject('/Helv 10 Tf 0 g'),
        NameObject('/Opt'): ArrayObject([
            TextStringObject(''), TextStringObject('A'), TextStringObject('Long option'),
            ArrayObject([TextStringObject('export'), TextStringObject('Display label')]),
        ]),
    }))
    page[NameObject('/Annots')] = ArrayObject([widget, choice])
    writer._root_object[NameObject('/AcroForm')] = writer._add_object(DictionaryObject({
        NameObject('/Fields'): ArrayObject([parent_ref, choice]),
        NameObject('/DR'): DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/Helv'): font})}),
        NameObject('/DA'): TextStringObject('/Helv 10 Tf 0 g'),
    }))
    writer.write(path)


class FormFieldsTest(unittest.TestCase):
    def test_discovery_and_fill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.pdf'
            fixture(source)
            fields = {f['field_id']: f for f in get_field_info(PdfReader(source))}
            self.assertEqual(fields['option']['choice_options'], [
                {'value': '', 'text': ''}, {'value': 'A', 'text': 'A'},
                {'value': 'Long option', 'text': 'Long option'},
                {'value': 'export', 'text': 'Display label'},
            ])
            self.assertEqual(fields['phone']['type'], 'text')
            self.assertEqual(fields['phone']['page'], 1)
            self.assertEqual(fields['phone']['rect'], [40, 500, 240, 520])
            values = root / 'values.json'
            values.write_text(json.dumps([
                {'field_id': 'phone', 'page': 1, 'value': '555-0100'},
                {'field_id': 'option', 'page': 1, 'value': 'export'},
            ]))
            result = root / 'filled.pdf'
            subprocess.run([sys.executable, str(SCRIPTS / 'fill_fillable_fields.py'),
                            str(source), str(values), str(result)], check=True)
            filled = PdfReader(result).get_fields()
            self.assertEqual(filled['phone']['/V'], '555-0100')
            self.assertEqual(filled['option']['/V'], 'export')


if __name__ == '__main__':
    unittest.main()
