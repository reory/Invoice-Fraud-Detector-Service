import logging
import threading
from datetime import datetime, timezone

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pydantic import ValidationError

from core.explainer import explain_prediction
from core.schemas import InvoiceModel

app = Flask(__name__)
CORS(app)

# Load model and encoders once at startup
MODEL = joblib.load("models/fraud_model.pkl")
VENDOR_LE = joblib.load("models/vendor_encoder.pkl")
CAT_LE = joblib.load("models/category_encoder.pkl")
CURR_LE = joblib.load("models/currency_encoder.pkl")

logger = logging.getLogger(__name__)

# Global in-memory log with thread-safety lock
SESSION_AUDIT_LOG = []
AUDIT_LOG_LOCK = threading.Lock()


@app.route("/")
def index():
    """Serve the frontend dashboard (templates/index.html)."""

    return render_template("index.html")


@app.route("/get_sample", methods=["GET"])
def get_sample():
    """Return one random invoice from the dataset as JSON, converting NaN to null."""
    
    try:
        df = pd.read_csv("data/raw/fake_invoices.csv")
        random_row = df.sample(n=1).to_dict(orient="records")[0]

        if "amount" in random_row:
            random_row["amount"] = float(random_row["amount"])

        random_row = {
            k: (None if isinstance(v, float) and pd.isna(v) else v)
            for k, v in random_row.items()
        }

        return jsonify(random_row)

    except FileNotFoundError:
        logger.error("Dataset file 'data/raw/fake_invoices.csv' was not found.")
        return jsonify({"error": "Invoice dataset file not found"}), 404

    except (KeyError, ValueError) as e:
        logger.error("Malformed row or missing required column in dataset: %s", e)
        return jsonify({"error": "Dataset missing required fields"}), 500


@app.route("/predict", methods=["POST"])
def predict():
    """
    Validate an invoice payload, 
    run it through the fraud model, and return the verdict.
    """

    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        invoice = InvoiceModel(**data)

        # Parse datetime safely
        try:
            dt = pd.to_datetime(invoice.invoice_date)
        except Exception as dt_err:
            raise ValueError(
                f"Invalid date format for invoice_date: {invoice.invoice_date}") from dt_err

        # Transform categorical data with Safety Catches
        try:
            vendor_enc = int(VENDOR_LE.transform([invoice.vendor_name])[0])
        except ValueError:
            vendor_enc = -1

        try:
            cat_enc = int(CAT_LE.transform([invoice.category])[0])
        except ValueError:
            cat_enc = -1

        try:
            curr_enc = int(CURR_LE.transform([invoice.currency])[0])
        except ValueError:
            curr_enc = -1

        final_features = [
            float(invoice.amount),
            int(invoice.invoice_time),
            float(invoice.vendor_rating),
            vendor_enc,
            cat_enc,
            1 if str(invoice.is_duplicate).lower() in ["true", "1", "yes"] else 0,
            int(dt.dayofweek),
            int(dt.month),
            1 if str(invoice.bank_account_change).lower() in ["true", "1", "yes"] else 0,
            1 if invoice.po_number else 0,
            1 if str(invoice.is_govt_official).lower() in ["true", "1", "yes"] else 0,
            curr_enc,
        ]

        cols = [
            "amount",
            "invoice_time",
            "vendor_rating",
            "vendor_encoded",
            "category_encoded",
            "is_duplicate",
            "day_of_week",
            "month",
            "bank_account_change",
            "has_po",
            "is_govt_official",
            "currency_encoded",
        ]

        input_df = pd.DataFrame([final_features], columns=cols)

        # Predict Probabilities
        prob_array = MODEL.predict_proba(input_df)[0]
        fraud_probability = float(prob_array[1])

        # Determine Verdict
        is_fraud_detected = fraud_probability > 0.5
        reasons = explain_prediction(input_df) if is_fraud_detected else []
        verdict = "⚠️ FRAUD" if is_fraud_detected else "✅ CLEAR"
        confidence_str = f"{fraud_probability:.2%}"

        # AUDIT LOG ENTRY CREATION
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "invoice_id": invoice.invoice_id,
            "vendor_name": invoice.vendor_name,
            "amount": f"£{float(invoice.amount):,.2f}",
            "confidence": confidence_str,
            "verdict": verdict,
            "reasons": reasons if reasons else ["No high risk factors"],
        }

        # Thread-safe mutation of shared audit log
        with AUDIT_LOG_LOCK:
            SESSION_AUDIT_LOG.insert(0, audit_entry)
            if len(SESSION_AUDIT_LOG) > 50:
                SESSION_AUDIT_LOG.pop()
            current_log = list(SESSION_AUDIT_LOG)

        return jsonify(
            {
                "invoice_id": invoice.invoice_id,
                "is_fraud": is_fraud_detected,
                "confidence": confidence_str,
                "reasons": reasons,
                "verdict": verdict,
                "audit_log": current_log,
            }
        )

    except (ValidationError, ValueError, TypeError, KeyError) as e:
        logger.warning("Invalid payload or parsing error in /predict: %s", e)
        return jsonify({"⛔ Error": str(e)}), 400

    except Exception as e:
        logger.exception("Unexpected exception occurred during prediction processing.")
        return jsonify({"⛔ Error": f"Internal server error: {e!s}"}), 500


@app.route("/audit_log", methods=["GET"])
def get_audit_log():
    """Returns historical session audit logs."""
    
    with AUDIT_LOG_LOCK:
        return jsonify(list(SESSION_AUDIT_LOG))


if __name__ == "__main__":
    app.run(debug=True, port=5000)