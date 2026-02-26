import pandas as pd
import requests

# Load the database - the CSV file.
df = pd.read_csv("data/raw/fake_invoices.csv")

# Filter for only QuickPay UK invoices using Pandas.
# This query is similar to a SQL query 
# (SELECT * FROM invoices WHERE vendor_name = 'QuickPay uk')
vendor_invoices = df[df['vendor_name'] == 'Small Ltd']

print(f"✅ Found {len(vendor_invoices)} | "
      f"invoice for Small Ltd. Sending to API..\n")

def clean_val(val):
    if str(val).strip().lower() in ['true', '1', 'yes']:
        return True # Pydantic will handle the rest
    return False

# Loop through each row and send it to the flask app.
for index, row in vendor_invoices.iterrows():
    # Prepare the information to match the Pydantic schema.
    pyda_schema = {
        "invoice_id": str(row['invoice_id']),
        "vendor_name": str(row['vendor_name']),
        "amount": float(row['amount']),
        "invoice_date": str(row['invoice_date']),
        "invoice_time": int(row['invoice_time']),
        "category": str(row['category']),
        "vendor_rating": float(row['vendor_rating']),
        "bank_account_change": clean_val(row['bank_account_change']),

        "po_number": str(row['po_number']) 
                    if pd.notnull(row['po_number']) 
                    and str(row['po_number']).lower() != 'nan' else None,

        "is_govt_official": clean_val(row['is_govt_official']),
        "currency": str(row['currency']),
        "payment_terms": str(row['payment_terms']),  
        "submitted_by": str(row['submitted_by']),    
        "is_duplicate": (clean_val(row['is_duplicate']))
    }

    # Post the processed data to the running Flask server.
    try:
        # Send request.
        response = requests.post("http://127.0.0.1:5000/predict", json=pyda_schema)
        result = response.json()
        
        # See if the API returns the actual error.
        if 'is_fraud' in result:
            # Use Numpy logic to print the status.
            status_icon = "🤔" if result['is_fraud'] else "✅"

            # use two f strings to break up long lines of code. pep79.
            print(f"[{row['invoice_id']}] Amount: £{row['amount']} | " 
                  f"{status_icon} Verdict: {result['verdict']}")

        else:
            print(f"⚠️ Warning for {row['invoice_id']}: {result}")

    except Exception as e:
        print(f"⛔ Error connecting to API: {e}")
        break

print("\n🚀 Batch Scan Complete.")