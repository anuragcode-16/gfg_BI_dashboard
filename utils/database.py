# utils/database.py
import pandas as pd
import sqlalchemy
import os

DB_PATH = "sqlite:///insurance_data.db"
UPLOAD_DB_PATH = "sqlite:///uploaded_data.db"

def csv_to_sqlite(csv_path, db_path=None, table_name="claims"):
    """Converts CSV to SQLite database for accurate SQL querying."""
    target_db = db_path if db_path else DB_PATH
    db_file = target_db.replace("sqlite:///", "")
    
    # Check if DB already exists to avoid re-creating every time
    if not os.path.exists(db_file):
        try:
            df = pd.read_csv(csv_path, encoding='cp1252')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return None
            
        engine = sqlalchemy.create_engine(target_db)
        df.to_sql(table_name, engine, index=False, if_exists='replace')
        print(f"Database created successfully from {csv_path}.")
    return target_db

def upload_csv_to_sqlite(uploaded_file):
    """Handles uploaded CSV file and creates a SQLite database from it."""
    try:
        # Try multiple encodings
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='cp1252')
        
        # Clean column names (remove spaces, special chars)
        df.columns = [c.strip().replace(' ', '_').replace('.', '_').lower() for c in df.columns]
        
        # Remove old uploaded DB if exists
        db_file = UPLOAD_DB_PATH.replace("sqlite:///", "")
        if os.path.exists(db_file):
            os.remove(db_file)
        
        engine = sqlalchemy.create_engine(UPLOAD_DB_PATH)
        df.to_sql("uploaded_data", engine, index=False, if_exists='replace')
        
        print(f"Uploaded data: {len(df)} rows, {len(df.columns)} columns")
        return UPLOAD_DB_PATH, df, "uploaded_data"
    except Exception as e:
        print(f"Error processing uploaded CSV: {e}")
        return None, None, None

def get_uploaded_schema(df, table_name="uploaded_data"):
    """Generates schema description dynamically from a DataFrame."""
    schema_lines = [f"    Table: {table_name}", "    Columns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        if 'int' in dtype or 'float' in dtype:
            type_label = "REAL"
            sample = f"(e.g., {df[col].dropna().head(3).tolist()})"
        else:
            type_label = "TEXT"
            unique_vals = df[col].dropna().unique()[:5].tolist()
            sample = f"(e.g., {unique_vals})"
        schema_lines.append(f"    - {col} ({type_label}): {sample}")
    
    return "\n".join(schema_lines)

def get_schema():
    """Returns the database schema to help the LLM understand data structure."""
    schema = """
    Dataset Context: This dataset tracks the operational and financial lifecycles of death claims
    processed by various life insurance companies in India. It captures metrics on the volume (number)
    and monetary value (amount) of claims that are pending, newly intimated, paid, repudiated,
    rejected, and unclaimed. It also includes calculated performance ratios.

    Table: claims
    Columns:
    - life_insurer (TEXT): The name of the life insurance company processing the claims (e.g., ABSL, Aegon, Ageas, Aviva, HDFC, ICICI, LIC).
    - year (TEXT): The financial year or reporting period for the claim statistics (e.g., '2021-22', '2020-21').
    - claims_pending_start_no (REAL): The number of unprocessed/pending claims at the beginning of the reporting period.
    - claims_pending_start_amt (REAL): The monetary value of unprocessed/pending claims at the beginning of the period.
    - claims_intimated_no (REAL): The number of newly reported (intimated) claims during the period.
    - claims_intimated_amt (REAL): The monetary value of newly reported claims during the period.
    - total_claims_no (REAL): The total number of claims available for processing (Pending Start + Intimated).
    - total_claims_amt (REAL): The total monetary value of claims available for processing.
    - claims_paid_no (REAL): The number of claims successfully settled and paid out to beneficiaries.
    - claims_paid_amt (REAL): The total monetary amount paid out for settled claims.
    - claims_repudiated_no (REAL): The number of claims formally denied or repudiated by the insurer after investigation.
    - claims_repudiated_amt (REAL): The total monetary amount of claims that were repudiated.
    - claims_rejected_no (REAL): The number of claims rejected upfront, typically due to technical or procedural invalidity.
    - claims_rejected_amt (REAL): The total monetary amount of the rejected claims.
    - claims_unclaimed_no (REAL): The number of approved claims that remain unclaimed by the beneficiaries.
    - claims_unclaimed_amt (REAL): The monetary value of approved claims that remain unclaimed.
    - claims_pending_end_no (REAL): The number of claims remaining unprocessed at the end of the reporting period.
    - claims_pending_end_amt (REAL): The monetary value of claims remaining unprocessed at the end of the period.
    - claims_paid_ratio_no (REAL): The proportion of total claims (by volume) that were successfully paid out.
    - claims_paid_ratio_amt (REAL): The proportion of total claims (by monetary value) that were successfully paid out.
    - claims_repudiated_rejected_ratio_no (REAL): The proportion of total claims (by volume) that were repudiated or rejected.
    - claims_repudiated_rejected_ratio_amt (REAL): The proportion of total claims (by monetary value) that were repudiated or rejected.
    - claims_pending_ratio_no (REAL): The proportion of total claims (by volume) that remain pending at the end of the period.
    - claims_pending_ratio_amt (REAL): The proportion of total claims (by monetary value) that remain pending at the end of the period.
    - category (TEXT): The specific classification of the death claim (e.g., 'Individual Death Claims' for individual vs. group policies).

    Potential Use Cases:
    - Benchmarking Operational Efficiency: Comparing claim settlement ratios (claims_paid_ratio_no) across insurers.
    - Financial Risk & Liquidity Forecasting: Using historical claim volumes and payout amounts to predict future cash flow.
    - Anomaly Detection in Rejections: Flagging unusually high denial rates using repudiated/rejected ratios.
    """
    return schema

def execute_sql(query, db_path=None):
    """Executes SQL query and returns a dataframe."""
    target_db = db_path if db_path else DB_PATH
    try:
        engine = sqlalchemy.create_engine(target_db)
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            return df, None
    except Exception as e:
        return None, str(e)