# Import CORS to allow the frontend and backend to communicate across different ports
from flask_cors import CORS
from flask import Flask, request, jsonify, render_template
from core.schemas import InvoiceModel
from core.explainer import explain_prediction
import joblib
import pandas as pd
import random
 
app = Flask(__name__)
CORS(app)

# Load model and encoders once at startup
MODEL =joblib.load("models/fraud_model.pkl")
VENDOR_LE = joblib.load("models/vendor_encoder.pkl")
CAT_LE = joblib.load("models/category_encoder.pkl")
CURR_LE = joblib.load("models/currency_encoder.pkl")

@app.route('/')
def index():
    # This serves up the HTML UI
    return render_template('index.html')

@app.route('/get_sample', methods=['GET'])
def get_sample():

    try:
        # Load the current csv dataset.
        df = pd.read_csv("data/raw/fake_invoices.csv")

        # Pick a random row and convert to a dictionary.
        random_row = df.sample(n=1).to_dict(orient='records')[0]

        # Only send the fields that the Flask UI needs.
        return jsonify({
            "invoice_id": random_row['invoice_id'],
            "vendor_name": random_row['vendor_name'],
            "amount": float(random_row['amount']),
            "category": random_row['category']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():

    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        invoice = InvoiceModel(**data) #type:ignore

        dt = pd.to_datetime(invoice.invoice_date)

        # Transform categorical data with Safety Catches
        try:
            vendor_enc = int(VENDOR_LE.transform([invoice.vendor_name])[0])
        except ValueError:
            vendor_enc = -1  

        try:
            cat_enc = int(CAT_LE.transform([invoice.category])[0])
        except ValueError:
            cat_enc = -1

        # Build the exact feature list (Atomic Casting)
        # Order: amount, invoice_time, vendor_rating, vendor_encoded, category_encoded, 
        # is_duplicate, day_of_week, month, bank_account_change, has_po, 
        # is_govt_official, currency_encoded
        final_features = [
            float(invoice.amount),                                      
            int(invoice.invoice_time),                                  
            float(invoice.vendor_rating),                               
            vendor_enc,                                                 
            cat_enc,                                                    
            1 if str(invoice.is_duplicate).lower() in ['true', '1', 'yes'] else 0, 
            int(dt.dayofweek),                                          
            int(dt.month),                                              
            1 if str(invoice.bank_account_change).lower() in ['true', '1', 'yes'] else 0, 
            1 if invoice.po_number else 0,                              
            1 if str(invoice.is_govt_official).lower() in ['true', '1', 'yes'] else 0, 
            int(CURR_LE.transform([invoice.currency])[0])               
        ]

        # Create DataFrame and FORCE the column alignment
        cols = ['amount', 'invoice_time', 'vendor_rating', 'vendor_encoded',
                'category_encoded', 'is_duplicate', 'day_of_week','month', 
                'bank_account_change', 'has_po', 'is_govt_official', 
                'currency_encoded']
        
        input_df = pd.DataFrame([final_features], columns=cols)

        # Predict Probabilities
        prob_array = MODEL.predict_proba(input_df.values)[0]
        
        # Using Index 0 based on your terminal output check
        fraud_probability = float(prob_array[1]) 

        # Determine Verdict
        is_fraud_detected = True if fraud_probability > 0.5 else False
        
        # DEBUG: Check terminal to see if features are changing!
        # Commented out for clarity. you can uncomment if you wish.
        #print(f"--- ATOMIC CHECK ---")
        #print(f"Vendor: {invoice.vendor_name} (Enc: {vendor_enc})")
        #print(f"Amount: {invoice.amount}")
        #print(f"Probabilities: {prob_array}")

        return jsonify({
            "invoice_id": invoice.invoice_id,
            "is_fraud": is_fraud_detected,
            "confidence": f"{fraud_probability:.2%}",
            "reasons": explain_prediction(input_df) if is_fraud_detected else [],
            "verdict": "⚠️ FRAUD" if is_fraud_detected else "✅ CLEAR"
        })
    
    except Exception as e:
        print(f"ERROR: {str(e)}") # Log to terminal too
        return jsonify({"⛔ Error": str(e)}), 400
    
if __name__ == "__main__":
    app.run(debug=True, port=5000)