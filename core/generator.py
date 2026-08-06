import sys
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import random

import pandas as pd
from faker import Faker

from core.schemas import InvoiceModel

# Initialize Faker library to generate realistic synthetic data
fake = Faker()
Faker.seed(42)
random.seed(42)

VENDORS = {
    "Trusted": [fake.company() for _ in range(10)],
    "Suspicious": ["QuickPay UK", "Legacy Consulting Group", "Global Tech Service"]
}

def generate_data(n=500):
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

        # Overlapping continuous distributions
        rating = round(random.uniform(2.0, 5.0), 1)
        amount = round(random.uniform(200, 12000), 2)
        po = f"PO-{random.randint(1000, 9999)}"
        vendor_name = random.choice(VENDORS['Trusted'])

        # Fraud Logic (20% chance to ensure enough samples in a small batch)
        if random.random() < 0.20:
            is_fraud = 1
            vendor_name = random.choice(
                VENDORS["Suspicious"] + VENDORS["Trusted"][:3]
            )

            # Continuous overlap: Some subtle fraud, some blatant fraud
            amount = round(random.uniform(3000, 45000), 2)
            rating = round(random.uniform(1.0, 3.5), 1)

            # Probabilistic red flags (not 100% deterministic)
            bank_change = random.random() < 0.55
            is_duplicate = random.random() < 0.35
            po = None if random.random() < 0.60 else po

        else:
            # Legitimate transactions with occasional benign noise (false alarms)
            vendor_name = random.choice(VENDORS["Trusted"])
            amount = round(random.uniform(100, 15000), 2)
            rating = round(random.uniform(2.5, 5.0), 1)

            # Small chance of benign edge cases
            bank_change = random.random() < 0.08
            is_duplicate = random.random() < 0.04
            po = None if random.random() < 0.15 else po

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
            "bank_account_change": bank_change,
            "po_number": po,
            "is_govt_official": govt_official,
            "is_duplicate": is_duplicate,
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
    print(f"😁 Fresh start! Generated {n} invoices in data/raw/fake_invoices.csv")

    return df

if __name__ == "__main__":
    generate_data(500)