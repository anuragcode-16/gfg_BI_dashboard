# utils/database.py
import pandas as pd
import sqlalchemy
import os

DB_PATH = "sqlite:///insurance_data.db"

def csv_to_sqlite(csv_path):
    """Converts CSV to SQLite database for accurate SQL querying."""
    # Check if DB already exists to avoid re-creating every time
    if not os.path.exists("insurance_data.db"):
        # FIX: Added encoding='cp1252' to handle Windows-specific characters
        # like smart quotes (byte 0x94) which cause UTF-8 errors.
        try:
            df = pd.read_csv(csv_path, encoding='cp1252')
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return None
            
        engine = sqlalchemy.create_engine(DB_PATH)
        df.to_sql("claims", engine, index=False, if_exists='replace')
        print("Database created successfully.")
    return DB_PATH

def get_schema():
    """Returns the database schema to help the LLM understand data structure."""
    # Manually defining schema based on the PDF for high accuracy
    schema = """
    Table: claims
    Columns:
    - life_insurer (TEXT): Name of insurance company (e.g., ABSL, LIC).
    - year (TEXT): Financial year (e.g., 2021-22).
    - claims_pending_start_no (REAL): Count of pending claims at start.
    - claims_pending_start_amt (REAL): Amount of pending claims at start.
    - claims_intimated_no (REAL): Count of new claims.
    - claims_intimated_amt (REAL): Amount of new claims.
    - total_claims_no (REAL): Total claims count.
    - total_claims_amt (REAL): Total claims amount.
    - claims_paid_no (REAL): Count of settled claims.
    - claims_paid_amt (REAL): Amount of settled claims.
    - claims_repudiated_no (REAL): Count of denied claims.
    - claims_repudiated_amt (REAL): Amount of denied claims.
    - claims_rejected_no (REAL): Count of rejected claims.
    - claims_rejected_amt (REAL): Amount of rejected claims.
    - claims_unclaimed_no (REAL): Count of unclaimed settlements.
    - claims_unclaimed_amt (REAL): Amount of unclaimed settlements.
    - claims_pending_end_no (REAL): Count of pending claims at end.
    - claims_pending_end_amt (REAL): Amount of pending claims at end.
    - claims_paid_ratio_no (REAL): Ratio of paid claims (volume).
    - claims_paid_ratio_amt (REAL): Ratio of paid claims (amount).
    - claims_repudiated_rejected_ratio_no (REAL): Ratio of denied claims (volume).
    - claims_repudiated_rejected_ratio_amt (REAL): Ratio of denied claims (amount).
    - claims_pending_ratio_no (REAL): Ratio of pending claims (volume).
    - claims_pending_ratio_amt (REAL): Ratio of pending claims (amount).
    - category (TEXT): Classification of claim.
    """
    return schema

def execute_sql(query):
    """Executes SQL query and returns a dataframe."""
    try:
        engine = sqlalchemy.create_engine(DB_PATH)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            return df, None
    except Exception as e:
        return None, str(e)