import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
import joblib
import os

def trainModel():

    # 1. Load the data
    df = pd.read_csv("data/raw/fake_invoices.csv")

    # Sync Check:
    # Using a robust mapping for any stray "True"/"False" strings
    mapping = {'True': 1, 'False': 0, 1: 1, 0: 0, True: 1, False: 0}
    
    cols_to_fix = ['is_duplicate', 'bank_account_change', 'is_govt_official']
    for col in cols_to_fix:
        df[col] = df[col].map(mapping).fillna(0).astype(int)

    # Sync Check: Feature Engineering (Date & PO)
    df['invoice_date'] = pd.to_datetime(df['invoice_date'])
    df['day_of_week'] = df['invoice_date'].dt.dayofweek #type:ignore
    df['month'] = df['invoice_date'].dt.month #type:ignore
    
    # Transformation: Check if po_number has a value (1) or is empty (0)
    df['has_po'] = df['po_number'].notnull().astype(int)

    # Encoders for Text Categories
    le_vendor = LabelEncoder()
    le_category = LabelEncoder()
    le_curr = LabelEncoder()

    df['vendor_encoded'] = le_vendor.fit_transform(df['vendor_name'])
    df['category_encoded'] = le_category.fit_transform(df['category'])
    df['currency_encoded'] = le_curr.fit_transform(df['currency'])

    # Feature Selection - MUST match scanner.py and app.py
    features = [
        'amount', 'invoice_time', 'vendor_rating', 'vendor_encoded',
        'category_encoded', 'is_duplicate', 'day_of_week', 'month', 
        'bank_account_change', 'has_po', 'is_govt_official', 
        'currency_encoded'
    ]
    
    X = df[features]
    y = df['is_fraud'].astype(int)

    # SMOTE & Training (Small Batch Protection)
    # k_neighbors=1 allows SMOTE to work even if you only have 2 fraud samples
    sm = SMOTE(random_state=42, k_neighbors=1) 
    X_res, y_res = sm.fit_resample(X, y) #type:ignore

    # Use stratify to ensure fraud is represented in both train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42, stratify=y_res
    )
    
    # max_depth=3 is better for small datasets to prevent overfitting (memorization)
    model = XGBClassifier(n_estimators=50, 
                          learning_rate=0.1, 
                          max_depth=3, 
                          random_state=42
    )
    model.fit(X_train, y_train)

    # Save everything
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/fraud_model.pkl")
    joblib.dump(le_vendor, "models/vendor_encoder.pkl")
    joblib.dump(le_category, "models/category_encoder.pkl")
    joblib.dump(le_curr, "models/currency_encoder.pkl")

    print(f"--- TRAINING COMPLETE ---")
    print(f"✅ Trained on {len(features)} features using 100-row sample.")
    print(f"📊 Accuracy on Test Set: {model.score(X_test, y_test):.2%}")

if __name__ == "__main__":
    trainModel()