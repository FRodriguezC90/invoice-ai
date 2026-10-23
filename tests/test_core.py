import unittest
from core import Invoice, validate_invoice, valid_rut, csv_bytes

def sample(**changes):
    values = dict(proveedor='Ejemplo', rut_proveedor='76.123.456-0', folio='001', fecha_emision='2026-10-23', moneda='CLP', neto='100000', iva='19000', total='119000')
    return Invoice(**(values | changes))

class ValidationTests(unittest.TestCase):
    def test_valid_document(self):
        self.assertEqual(validate_invoice(sample()), [])

    def test_wrong_total(self):
        self.assertTrue(any('no coincide' in e for e in validate_invoice(sample(total='120000'))))

    def test_rut_checksum(self):
        self.assertTrue(valid_rut('76.123.456-0'))
        self.assertFalse(valid_rut('76.123.456-1'))

    def test_missing_field(self):
        self.assertTrue(any('falta' in e for e in validate_invoice(sample(folio=None))))

    def test_impossible_date(self):
        self.assertTrue(any('Fecha:' in e for e in validate_invoice(sample(fecha_emision='2026-02-30'))))

    def test_ambiguous_amount(self):
        self.assertTrue(any('Neto:' in e for e in validate_invoice(sample(neto='100.000,00'))))

    def test_formula_escape_and_leading_zero(self):
        output = csv_bytes(sample(proveedor='=SUM(A1:A2)')).decode('utf-8-sig')
        self.assertIn("'=SUM", output)
        self.assertIn('001', output)

if __name__ == '__main__':
    unittest.main()
