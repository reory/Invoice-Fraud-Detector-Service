import joblib

# Load the brain
MODEL = joblib.load("models/fraud_model.pkl")

# Mapping
HUMAN_READABLE = {
    "has_po": "Missing Purchase Order",
    "bank_account_change": "Recent Bank Account Change",
    "amount": "High Invoice Amount",
    "vendor_rating": "Poor Vendor Rating",
    "is_govt_official": "Government Official Involvement",
    "is_duplicate": "Duplicate Invoice ID"
}

def explain_prediction(input_features_df):
    """
    Uses XGBoost's built-in feature importance to explain why the model 
    is focused on certain attributes.
    """

    # Get the 'Weight' or 'Gain' of each feature from the model
    # This returns a dictionary of how important each column is
    importance_scores = MODEL.get_booster().get_score(importance_type='gain')
    
    # Map those scores to the current input columns
    # Sort them so the most influential features are at the top
    sorted_importance = sorted(importance_scores.items(), 
                               key=lambda x: x[1], reverse=True)
    
    reasons = []
    
    # Take the top 3 and translate to human-readable text.
    for feature_name, score in sorted_importance[:3]:
        friendly_name = HUMAN_READABLE.get(feature_name, feature_name)
        reasons.append(friendly_name)
    
    return reasons