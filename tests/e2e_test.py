import httpx
import sys
import re

ANALYZE_URL = 'http://127.0.0.1:8000/api/analyze'
SUBMIT_URL = 'http://127.0.0.1:8000/api/submit'
TEST_IMAGE = 'test_ticket.jpg'

print('Starting E2E test')

try:
    with open(TEST_IMAGE, 'rb') as f:
        files = {'file': ('test_ticket.jpg', f, 'image/jpeg')}
        print('POST', ANALYZE_URL)
        r = httpx.post(ANALYZE_URL, files=files, timeout=60.0)
        print('Status', r.status_code)
        if r.status_code != 200:
            print('Analyze failed:', r.text[:1000])
            sys.exit(2)
        html = r.text

    # extract image_data hidden field
    m = re.search(r'name="image_data"\s+value="([^"]+)"', html)
    if not m:
        print('image_data not found in analyze response')
        print(html[:1000])
        sys.exit(3)
    image_data = m.group(1)
    print('Extracted image_data length:', len(image_data))

    # Scenario 1: normal submission with image
    form = {
        'fournisseur': 'E2E Test Fournisseur',
        'date': '2026-06-10',
        'montant_ttc': '15.50',
        'tva': '2.50',
        'devise': 'EUR',
        'type_document': 'transport',
        'description': 'E2E submission test',
        'image_data': image_data,
    }

    print('POST', SUBMIT_URL, '(normal submission)')
    r2 = httpx.post(SUBMIT_URL, data=form, timeout=60.0)
    print('Submit status', r2.status_code)
    print('Submit response snippet:', r2.text[:1000])
    if r2.status_code != 200:
        print('Submit failed')
        sys.exit(4)

    # Scenario 2: robustness test without image and empty TVA
    form_no_image = {
        'fournisseur': 'E2E Test Fournisseur',
        'date': '2026-06-10',
        'montant_ttc': '15.50',
        'tva': '',
        'devise': 'EUR',
        'type_document': 'transport',
        'description': 'E2E robustness test',
        'image_data': '',
    }

    print('POST', SUBMIT_URL, '(robustness test without image)')
    r3 = httpx.post(SUBMIT_URL, data=form_no_image, timeout=60.0)
    print('Submit status', r3.status_code)
    print('Submit response snippet:', r3.text[:1000])
    if r3.status_code != 200:
        print('Robustness submit failed')
        sys.exit(5)

    print('E2E test completed successfully')
except Exception as e:
    print('E2E test encountered exception:', repr(e))
    sys.exit(1)
