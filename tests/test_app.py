import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_high_risk_logic(client):

    # Test a fraudulent payload
    suspicious_payload = {
        "invoice_id": "INV-1001",
        "payment_terms": "Net 30",
        "invoice_date": "2025-01-23",
        "submitted_by": "PythonTester",
        "vendor_name": "QuickPay UK", # Known suspicious name in your logic
        "amount": 99999.0,           
        "currency": "GBP",
        "invoice_time": 2,            
        "vendor_rating": 1.0,         # Poor rating
        "is_duplicate": True,
        "bank_account_change": True,
        "po_number": "",              # Missing PO
        "is_govt_official": True,
        "category": "Miscellaneous"
    }

    response = client.post('/predict', json=suspicious_payload)
    data = response.get_json()

    # Assert that the risk is higher than usual.
    conf_value = float(data['confidence'].replace('%', ''))

    assert response.status_code == 200
    assert conf_value > 50
    assert data.get('is_fraud') is True

def test_predict_route_status(client):

    # Test a dummy prediction to see if  the engine handles the test.
    payload = {
        "invoice_id": "INV-TEST-001",
        "vendor_name": "Small Ltd",
        "amount": 250.00,
        "currency": "GBP",
        "invoice_time": 10,
        "vendor_rating": 3.5,
        "payment_terms": "Net 30",
        "invoice_date": "2025-01-23",
        "submitted_by": "PythonTester",
        "is_duplicate": False,
        "bank_account_change": False,
        "po_number": "PO 346",
        "is_govt_official": False,
        "category": "Utilities"
    }

    response = client.post('/predict', json=payload)
    data = response.get_json()

    assert response.status_code == 200
    assert "confidence" in data