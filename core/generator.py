import random
import pandas as pd
from faker import Faker
from core.schemas import InvoiceModel

# Initialize Faker library to generate realistic synthetic data
fake = Faker()

VENDORS = {
    "Trusted": [fake.company() for _ in range(10)],
    "Suspicious": ["QuickPay UK", "Legacy Consulting Group", "Global Tech Service"]
}

def generate_data(n=100):
    """
    Function to generate a synthetic dataset of n invoice records
    """
    data = []
    for _ in range(n):
        # Default State
        is_fraud = 0
        is_duplicate = False
        bank_change = False
        govt_official = random.random() < 0.05
        rating = round(random.uniform(3.5, 5.0), 1)
        amount = round(random.uniform(100, 5000), 2)
        po = f"PO-{random.randint(1000, 9999)}"
        vendor_name = random.choice(VENDORS['Trusted'])

        # Fraud Logic (15% chance to ensure enough samples in a small batch)
        if random.random() < 0.15:
            is_fraud = 1
            vendor_name = random.choice(VENDORS['Suspicious'])
            amount = round(random.uniform(15000, 50000), 2) # High Amount
            rating = round(random.uniform(1.0, 2.0), 1)     # Low Rating
            bank_change = True                              # Red Flag
            po = None if random.random() < 0.7 else po      # Missing PO

        # Build dictionary (matching your schemas.py expectations)
        invoice_data = {
            "invoice_id": f"INV-{random.randint(10000, 99999)}",
            "vendor_name": vendor_name,
            "amount": amount,
            "payment_terms": random.choice(["Net-30", "Net-60"]),
            "category": random.choice(["Consulting", "Software", "Utilities"]),
            "invoice_date": fake.date_this_year().isoformat(),
            "invoice_time": random.randint(800, 1800),
            "submitted_by": f"EMP-{random.randint(100, 500)}",
            "vendor_rating": rating,
            "bank_account_change": 1 if bank_change else 0,
            "po_number": po,
            "is_govt_official": 1 if govt_official else 0,
            "is_duplicate": 1 if is_duplicate else 0,
            "currency": "GBP",
            "is_fraud": is_fraud
        }

        # Validate through Pydantic to ensure formats are correct
        validated = InvoiceModel(**invoice_data).model_dump()
        
        # Ensure target is an int for the CSV
        validated["is_fraud"] = is_fraud
        data.append(validated)

    df = pd.DataFrame(data)
    df.to_csv("data/raw/fake_invoices.csv", index=False)
    print(f"✨ Fresh start! Generated {n} invoices in data/raw/fake_invoices.csv")

if __name__ == "__main__":
    generate_data(100)