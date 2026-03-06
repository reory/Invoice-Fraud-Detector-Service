import pytest
import pandas as pd
import os
from core.generator import generate_data

def test_generate_structure():
    """Test that the generate structure returns the expected format."""

    # Arrange rows
    n_rows = 10

    # Create a DataFrame with n_rows f synthetic test data.
    df = generate_data(n_rows)

    # Assert
    assert df is not None
    assert len(df) == n_rows
    assert "amount" in df.columns
    assert "vendor_name" in df.columns
    assert df['amount'].dtype == "float64"
    
    # Colums to exclude from processing.
    cols_to_ignore = ['po_number', 'category_note']

    # Remove unwanted columns without failing if they're missing
    clean_df = df.drop(columns=cols_to_ignore, errors='ignore')
    
    # Verify no missing values remain after cleaning.
    assert not clean_df.isnull().values.any()