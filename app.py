import hashlib
import json
import os
import time
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from core import Invoice, LABELS, validate_invoice, csv_bytes
from extractor import extract_invoice, document_content

load_dotenv()
st.set_page_config(page_title='Invoice AI | Revisión de facturas', layout='wide')
st.title('Invoice AI')
st.write('Extrae datos de una factura, revísalos y descarga una tabla.')
st.caption('Prototipo de portafolio. Facturas simples con neto, IVA y total; no valida documentos ante el SII.')

with st.sidebar:
    st.header('Cómo probarlo')
    st.write('1. Abre el ejemplo o carga una factura.\n2. Revisa los datos.\n3. Confirma y descarga.')
    demo = st.button('Abrir ejemplo sin API', use_container_width=True)
    st.caption('El ejemplo carga valores ficticios predefinidos. No realiza extracción con IA.')
    model = st.text_input('Modelo de extracción', value=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'))
    st.caption('La extracción real requiere OPENAI_API_KEY en el archivo .env y genera consumo de API.')

upload = st.file_uploader('Factura PDF, PNG o JPG (máximo 10 MB, PDF de hasta 5 páginas)', type=['pdf', 'png', 'jpg', 'jpeg'])
upload_data = upload.getvalue() if upload else None
source = hashlib.sha256(upload_data).hexdigest() if upload_data else 'sin-archivo'

def set_result(invoice, source_id, metadata):
    st.session_state['invoice'] = invoice.model_dump()
    st.session_state['result_source'] = source_id
    st.session_state['metadata'] = metadata
    st.session_state['revision'] = st.session_state.get('revision', 0) + 1

if demo:
    sample = json.loads((Path(__file__).parent / 'examples' / 'factura_demo.json').read_text(encoding='utf-8'))
    set_result(Invoice(**sample), 'demo', {'modo': 'Ejemplo ficticio, sin llamada a IA'})

consent = st.checkbox('Autorizo enviar este documento a OpenAI para extraer sus datos.', disabled=not bool(upload))
if st.button('Extraer con IA', disabled=not bool(upload) or not consent, type='primary'):
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        st.error('Falta configurar OPENAI_API_KEY en .env. Puedes probar el ejemplo sin API.')
    elif not model.strip():
        st.error('Indica un modelo compatible.')
    else:
        # Invalida un resultado anterior antes de comenzar un intento nuevo.
        st.session_state.pop('invoice', None)
        try:
            with st.spinner('Procesando documento…'):
                start = time.perf_counter()
                result, metadata = extract_invoice(upload_data, upload.name, key, model.strip())
                metadata['segundos'] = round(time.perf_counter() - start, 2)
                set_result(result, source, metadata)
        except ValueError as exc:
            st.error(str(exc))
        except Exception:
            st.error('No se pudo procesar el documento. Comprueba el archivo, la conexión, el acceso al modelo y el saldo de API. No se ha generado un resultado nuevo.')

if 'invoice' in st.session_state:
    result_source = st.session_state['result_source']
    if result_source != 'demo' and result_source != source:
        st.info('El archivo cambió. Extrae sus datos para comenzar una nueva revisión.')
    else:
        left, right = st.columns([1, 1])
        with left:
            st.subheader('Documento de referencia')
            if result_source == 'demo':
                st.text((Path(__file__).parent / 'examples' / 'factura_demo.txt').read_text(encoding='utf-8'))
            elif upload.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                st.image(upload_data, caption='Documento cargado')
            else:
                try:
                    from pypdf import PdfReader
                    import io
                    document_content(upload_data, upload.name)
                    text = '\n'.join(page.extract_text() or '' for page in PdfReader(io.BytesIO(upload_data)).pages)
                    st.text_area('Texto del PDF (no reproduce el diseño)', text or 'PDF escaneado: revisa el original en tu visor de PDF.', height=370, disabled=True)
                except Exception:
                    st.info('Abre el documento original en tu visor para revisarlo.')
            st.json(st.session_state['metadata'])
        with right:
            st.subheader('Revisión de campos')
            st.caption('Importes sin separadores de miles. Ejemplo: 100000 o 100000.50.')
            revision = st.session_state['revision']
            edited = {name: st.text_input(label, value=st.session_state['invoice'].get(name) or '', key=f'{revision}_{name}').strip() or None
                      for name, label in LABELS.items()}
            invoice = Invoice(**edited)
            errors = validate_invoice(invoice)
            for error in errors:
                st.warning(error)
            if not errors:
                st.success('Las comprobaciones de formato y montos no detectaron problemas. Revisa igualmente contra el original.')
            # Vincula la confirmación a los valores: cambiar un campo exige volver a confirmar.
            digest = hashlib.sha256(json.dumps(edited, sort_keys=True).encode()).hexdigest()
            approved = st.checkbox('Revisé estos datos contra el documento.', key=f'approve_{revision}_{digest}')
            st.download_button('Descargar CSV revisado', data=csv_bytes(invoice), file_name='factura_revisada.csv', mime='text/csv', disabled=bool(errors) or not approved)
st.caption('Los archivos se procesan en memoria; esta aplicación no crea una base de datos ni guarda documentos en disco. En modo IA se envían al proveedor de API. No publiques facturas privadas ni claves en GitHub.')
