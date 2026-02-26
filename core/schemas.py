from pydantic import BaseModel, Field, field_validator, ValidationInfo
from datetime import date
from typing import Optional

class InvoiceModel(BaseModel):
    
    # Standard Files--------------------------------
    invoice_id: str
    vendor_name: str
    # amount must be greater than 0.
    amount: float = Field(..., gt=0) 
    # e.g "GB -35", "Due on receipt"
    payment_terms: str 
    invoice_date: date
    # represented as UNIX timestamp or HHMM.
    invoice_time: int 
    # user id (eg, "UK-3245")
    submitted_by: str 
    # Duplicate invoice 
    is_duplicate: bool = False

    # Categorization--------------------------------
    category: str # 'Utilities' 'software', etc.
    # Specific details or sub-costs.
    category_note: Optional[str] = None
    consulting_fees: float = Field(default=0.0, ge=0)

    # Fraud indicator------------------------------
    # 0 = Normal. 1 = Investigate fraud (Anomaly).
    is_fraud: int = Field(default=0, ge=0, le=1)

    # Metadata and UI logic-----------------------------
    vendor_rating: float = Field(default=1.0, ge=0, le=10.0)
    
    # Grey for suspicious invoices - white for standard.
    invoice_color: str = "white"

    # New fields added after successfully training the Brain.
    po_number: Optional[str] = None
    bank_account_change: bool = False
    is_govt_official: bool = False
    currency: str = "GBP"

    @field_validator('invoice_color', mode='before')
    @classmethod
    def set_invoice_color(cls, v: str, info: ValidationInfo) -> str:
        
        # If vendor rating is low we force the color to grey.
        rating = info.data.get('vendor_rating', 1.0)
        if rating < 2.0:
            return "grey"
        return v

    class Config:
        # This allows spaces to be used with names
        # if ever they get exported to a dictionary for a UI.
        model_config = {
            "populate_by_name": True
        }

    
    
    