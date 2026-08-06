from unittest.mock import patch

import pandas as pd


def test_get_sample_file_not_found(client):
    """Ensure /get_sample returns 404 with an error message when the CSV is missing."""
    
    with patch("pandas.read_csv", side_effect=FileNotFoundError):
        response = client.get("/get_sample")
        assert response.status_code == 404
        assert response.json["error"] == "Invoice dataset file not found"

def test_get_sample_returns_valid_json(client):
    """
    Ensure /get_sample converts NaN fields to null, 
    not an invalid `NaN` token.
    """
    # Force a row with a missing/NaN field, like category_note or po_number
    with patch("pandas.read_csv") as mock_read_csv:
        mock_read_csv.return_value = pd.DataFrame([{
            "invoice_id": "INV-1",
            "vendor_name": "Acme Ltd",
            "amount": 123.45,
            "category": "Software",
            "category_note": float("nan"),
        }])
        response = client.get("/get_sample")
        assert response.status_code == 200
        assert b"NaN" not in response.data
        assert response.json["category_note"] is None