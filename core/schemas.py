from pydantic import BaseModel, Field, field_validator, ValidationInfo, ConfigDict
from datetime import date
from typing import Optional

class InvoiceModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    # --- Standard Fields ---
    invoice_id: str
    vendor_name: str
    amount: float = Field(..., gt=0) # Amount must be greater than 0
    payment_terms: str               # e.g., "Net 30", "Due on receipt"
    invoice_date: date
    invoice_time: int                # Represented as UNIX timestamp or HHMM
    submitted_by: str                # User ID (e.g., "UK-3245")
    is_duplicate: bool = False

    # --- Categorization ---
    # 'Utilities', 'Software', etc.
    category: str 
    category_note: Optional[str] = None
    consulting_fees: float = Field(default=0.0, ge=0)

    # --- Fraud Indicator ---
    # 0 = Normal, 1 = Investigate fraud (Anomaly)
    is_fraud: int = Field(default=0, ge=0, le=1)

    # --- Metadata and UI Logic ---
    vendor_rating: float = Field(default=1.0, ge=0, le=10.0)
    
    # Grey for suspicious invoices, white for standard
    invoice_color: str = "white"

    # --- Brain-Training Fields ---
    po_number: Optional[str] = None
    bank_account_change: bool = False
    is_govt_official: bool = False
    currency: str = "GBP"

    #--------v2.0.0-----------------
    @field_validator('invoice_color', mode='before')
    @classmethod
    def set_invoice_color(cls, v: str, info: ValidationInfo) -> str:
        # If vendor rating is low, we force the color to grey
        # Note: .get() defaults to 1.0 if rating isn't provided yet
        rating = info.data.get('vendor_rating', 1.0)
        if rating < 2.0:
            return "grey"
        return v


    
    
    