import logging

import joblib
from sklearn.exceptions import NotFittedError

# Configure standard logger
logger = logging.getLogger(__name__)

# Load the brain
MODEL = joblib.load("models/fraud_model.pkl")

# Mapping
HUMAN_READABLE = {
    "has_po": "Missing Purchase Order",
    "bank_account_change": "Recent Bank Account Change",
    "amount": "High Invoice Amount",
    "vendor_rating": "Poor Vendor Rating",
    "is_govt_official": "Government Official Involvement",
    "is_duplicate": "Duplicate Invoice ID",
}


def _extract_booster(model_obj):
    """
    Recursively search and extract the fitted 
    XGBoost booster from any wrapper object.
    """

    if model_obj is None:
        return None

    # Direct XGBClassifier or Booster
    if hasattr(model_obj, "get_booster"):
        return model_obj.get_booster()

    # Handle CalibratedClassifierCV wrapper
    if hasattr(model_obj, "calibrated_classifiers_") and len(model_obj.calibrated_classifiers_) > 0:
        cc = model_obj.calibrated_classifiers_[0]
        
        # Check possible attribute names for the fitted inner model across scikit-learn versions
        for attr in ["estimator", "base_estimator", "_fit_estimator"]:
            inner_model = getattr(cc, attr, None)
            if inner_model is not None:
                booster = _extract_booster(inner_model)
                if booster is not None:
                    return booster

    return None


def explain_prediction(input_features_df):
    """Uses XGBoost's built-in feature importance to explain why the model
    is focused on certain attributes.
    """

    try:
        booster = _extract_booster(MODEL)

        if booster is None:
            logger.warning(
                "MODEL object does not expose a recognized booster structure."
            )
            return ["High Fraud Risk Indicators Present"]

        # Use 'booster' variable instead of calling MODEL.get_booster()
        importance_scores = booster.get_score(importance_type="gain")

        # Sort so the most influential features are at the top
        sorted_importance = sorted(
            importance_scores.items(), key=lambda x: x[1], reverse=True
        )

        reasons = []

        # Take the top 3 and translate to human-readable text
        for feature_name, score in sorted_importance[:3]:
            friendly_name = HUMAN_READABLE.get(feature_name, feature_name)
            reasons.append(friendly_name)

        return reasons if reasons else ["High Risk Anomaly Detected"]

    except (AttributeError, KeyError, IndexError, NotFittedError):
        logger.exception("Failed to extract feature importance")
        return ["Invoice Fraud Risk Threshold Exceeded"]