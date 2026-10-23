"""Esquema, validaciones y exportación independientes de la interfaz."""
import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, ConfigDict


class Invoice(BaseModel):
    model_config = ConfigDict(extra='forbid')
    proveedor: str | None
    rut_proveedor: str | None
    folio: str | None
    fecha_emision: str | None
    moneda: str | None
    neto: str | None
    iva: str | None
    total: str | None


LABELS = {
    'proveedor': 'Proveedor', 'rut_proveedor': 'RUT del proveedor',
    'folio': 'Folio', 'fecha_emision': 'Fecha de emisión (AAAA-MM-DD)',
    'moneda': 'Moneda', 'neto': 'Neto', 'iva': 'IVA', 'total': 'Total',
}


def valid_rut(value):
    raw = value.replace('.', '').replace('-', '').replace(' ', '').upper()
    if not re.fullmatch(r'\d{7,8}[0-9K]', raw):
        return False
    total = sum(int(n) * (2 + i % 6) for i, n in enumerate(reversed(raw[:-1])))
    remainder = 11 - total % 11
    check = '0' if remainder == 11 else 'K' if remainder == 10 else str(remainder)
    return raw[-1] == check


def validate_invoice(invoice):
    """Revisión de facturas simples: no certifica validez tributaria."""
    errors = []
    values = invoice.model_dump()
    for name, value in values.items():
        if value is None or not value.strip():
            errors.append(f'{LABELS[name]}: falta el dato; revisa el documento.')
    if invoice.rut_proveedor and not valid_rut(invoice.rut_proveedor):
        errors.append('RUT: formato o dígito verificador incorrecto.')
    if invoice.fecha_emision:
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', invoice.fecha_emision):
                raise ValueError()
            date.fromisoformat(invoice.fecha_emision)
        except ValueError:
            errors.append('Fecha: utiliza una fecha válida en formato AAAA-MM-DD.')
    amounts = {}
    for name in ('neto', 'iva', 'total'):
        if values[name]:
            try:
                if not re.fullmatch(r'\d+(\.\d+)?', values[name]):
                    raise InvalidOperation()
                amount = Decimal(values[name])
                if not amount.is_finite():
                    raise InvalidOperation()
                amounts[name] = amount
            except InvalidOperation:
                errors.append(f'{LABELS[name]}: usa un importe positivo o cero, sin separador de miles y con punto decimal.')
    if len(amounts) == 3:
        tolerance = Decimal('1') if (invoice.moneda or '').upper() == 'CLP' else Decimal('0.01')
        if abs(amounts['neto'] + amounts['iva'] - amounts['total']) > tolerance:
            errors.append('Montos: neto + IVA no coincide con el total. Puede haber otros cargos o impuestos; este prototipo no los admite.')
    return errors


def csv_bytes(invoice):
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=list(LABELS))
    writer.writeheader()
    # Evita interpretar valores de texto como fórmulas al abrirlos en una planilla.
    row = {k: ("'" + v if v and v.lstrip().startswith(('=', '+', '-', '@')) else v)
           for k, v in invoice.model_dump().items()}
    writer.writerow(row)
    return buffer.getvalue().encode('utf-8-sig')
