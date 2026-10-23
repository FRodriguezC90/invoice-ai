# Invoice AI

Prototipo de extracción de datos de facturas con Python, Streamlit y un LLM. Proyecto de portafolio para practicar integración de IA con validación y revisión humana.

## Qué incluye

- Entrada PDF, PNG y JPEG (10 MB; PDF de hasta 5 páginas).
- Extracción de proveedor, RUT del emisor, folio, fecha, moneda, neto, IVA y total.
- Salida estructurada mediante Pydantic y OpenAI Responses API.
- Validación local de campos ausentes, fecha, dígito verificador del RUT y suma de importes.
- Formulario de corrección, confirmación y exportación CSV.
- Ejemplo ficticio sin API para recorrer la interfaz. Este modo carga datos predefinidos, no extrae información.
- Registro visible de duración y tokens de cada extracción real.

## Ejecutar en Windows

Requiere Python 3.11 o superior. Abre una terminal dentro de esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abre la dirección local indicada por Streamlit. Pulsa **Abrir ejemplo sin API** para probar la revisión y la descarga, sin clave ni consumo.

Para extracción real, edita `.env` e introduce tu clave en `OPENAI_API_KEY`. El modelo propuesto es `gpt-4.1-mini`; puedes cambiar `OPENAI_MODEL` por uno al que tu cuenta tenga acceso y que admita imágenes, PDF y salidas estructuradas. La API tiene facturación propia: una suscripción de ChatGPT no configura esta aplicación. No introduzcas la clave en el código ni la compartas.

Carga un documento ficticio o anonimizado en PDF, PNG o JPG y autoriza su envío. La extracción real envía el documento completo a OpenAI; no se hace OCR local. `store=False` desactiva el almacenamiento de la respuesta para recuperación posterior, pero no equivale a una garantía de retención cero por parte del proveedor. Consulta sus condiciones antes de usar documentos de terceros.

## Flujo

```text
Documento -> validación del archivo -> modelo multimodal
          -> esquema Pydantic -> reglas locales -> revisión humana -> CSV
```

`core.py` contiene reglas y exportación; `extractor.py`, la integración con el modelo; `app.py`, la interfaz. Los documentos y claves no se guardan en disco por la aplicación. Los resultados viven en la sesión y se pierden al reiniciarla. No hay base de datos, autenticación ni detección de duplicados persistente en esta versión.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/check_app.py
```

Las pruebas verifican reglas y exportación; no demuestran la precisión del modelo. Para medirla, reúne documentos ficticios con formatos distintos, anota sus respuestas correctas y compara cada campo con la extracción **antes** de corregirla. Separa los documentos usados para ajustar el prompt de los usados para evaluación final. Informa número de documentos, aciertos por campo, campos ausentes, tiempo y tokens. No publiques porcentajes sin haber hecho esa evaluación.

## Publicar en tu GitHub

1. Crea un repositorio vacío llamado `invoice-ai` desde tu cuenta de GitHub. No agregues README remoto si vas a subir este proyecto con Git.
2. Abre una terminal en esta carpeta y ejecuta:

```powershell
git init
git add .
git status
git commit -m "Build invoice extraction prototype with human review"
git branch -M main
```

3. Comprueba en `git status` y en los archivos preparados que no haya claves, `.env`, facturas privadas ni datos personales. `.env.example` sí debe publicarse, con la clave vacía.
4. Ejecuta `git remote add origin` seguido de la URL exacta de tu repositorio. Luego:

```powershell
git push -u origin main
```

Si Git solicita identidad, configura tu nombre y correo de commits. Si una clave llega a un commit, revócala; borrarla del archivo no elimina el secreto del historial.

## Alcance y límites

Admite una factura simple por archivo. Notas de crédito, múltiples facturas, descuentos, montos exentos y otros impuestos requieren ampliar el esquema y las reglas. No valida ante el SII ni sustituye revisión contable. Un RUT con dígito correcto no prueba identidad. Campos estructurados no garantizan extracción correcta. No se asigna una confianza inventada al modelo.

La vista PDF muestra texto extraído, no el diseño original; para un escaneo se necesita revisar el archivo con un visor externo. La carga de imágenes tiene vista previa. La exportación bloquea campos faltantes o errores de las reglas del prototipo. El CSV conserva los valores como texto, pero un programa de planillas puede reinterpretar folios al importarlos: selecciona tipo texto para conservar ceros iniciales.

Antes de ofrecerlo como servicio: autenticación, almacenamiento seguro, gestión de datos, límites de consumo, pruebas de carga y evaluación con documentos representativos.

## Documentación técnica

- [Entradas PDF en OpenAI](https://developers.openai.com/api/docs/guides/file-inputs)
- [Salidas estructuradas](https://developers.openai.com/api/docs/guides/structured-outputs)

## Cómo presentarlo

Mientras no tenga usuarios reales, descríbelo como **prototipo personal de portafolio**. Incluye capturas del ejemplo ficticio y resultados de evaluación solo cuando los hayas medido. No representa experiencia comercial ni un modelo entrenado desde cero.
