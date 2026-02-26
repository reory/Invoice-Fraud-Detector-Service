import pytest
import pandas as pd
import os
from core.generator import generate_data

def test_generate_structure():

    # Arrange rows
    n_rows = 10

    # Act
    df = generate_data(n_rows)

    # Assert
    assert df is not None
    assert len(df) == n_rows
    assert "amount" in df.columns
    assert "vendor_name" in df.columns
    assert df['amount'].dtype == "float64"

    cols_to_ignore = ['po_number', 'category_note']
    clean_df = df.drop(columns=cols_to_ignore, errors='ignore')

    assert not clean_df.isnull().values.any()