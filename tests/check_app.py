import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from streamlit.testing.v1 import AppTest

at = AppTest.from_file(str(root / 'app.py'), default_timeout=20).run()
assert not at.exception, at.exception
at.sidebar.button[0].click().run()
assert not at.exception, at.exception
assert len(at.text_input) == 9, len(at.text_input)
assert len(at.warning) == 0, [w.value for w in at.warning]
assert at.get('download_button')[0].proto.disabled
at.checkbox[-1].check().run()
assert not at.get('download_button')[0].proto.disabled
total = next(x for x in at.text_input if x.label == 'Total')
total.set_value('120000').run()
assert any('no coincide' in w.value for w in at.warning)
assert at.get('download_button')[0].proto.disabled
assert not at.checkbox[-1].value
assert not at.exception
print('PASS: initial screen, demo review, approval, download enabled, mismatch blocked, approval reset')

# Comprueba el contrato del SDK con una respuesta simulada, sin red ni clave real.
import httpx
from openai import OpenAI
from core import Invoice
import json
sample = json.loads((root / 'examples/factura_demo.json').read_text(encoding='utf-8'))
seen = []
def handler(request):
    payload = json.loads(request.content)
    seen.append(payload)
    assert payload['store'] is False
    assert payload['text']['format']['strict'] is True
    return httpx.Response(200, json={
        'id':'resp_test', 'object':'response', 'created_at':0, 'model':'gpt-4.1-mini',
        'status':'completed', 'output':[{'id':'msg_test','type':'message','role':'assistant','status':'completed',
        'content':[{'type':'output_text','text':json.dumps(sample),'annotations':[]}]}],
        'usage':{'input_tokens':10,'output_tokens':20,'total_tokens':30},
    })
client = OpenAI(api_key='test-not-a-real-key', http_client=httpx.Client(transport=httpx.MockTransport(handler)))
response = client.responses.parse(model='gpt-4.1-mini', input='test', text_format=Invoice, store=False)
assert response.output_parsed.total == '119000'
print('PASS: SDK structured output contract with mocked transport; no real inference performed')
