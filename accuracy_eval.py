"""
accuracy_eval.py — Evaluation Script aligned with Problem Statement
Run: python accuracy_eval.py
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_engine import generate_sql, generate_visualization
from utils.database import execute_sql, csv_to_sqlite

# Initialize Database
DATA_PATH = "data/India Life Insurance Claims.csv"
if os.path.exists(DATA_PATH):
    csv_to_sqlite(DATA_PATH)
else:
    print(f"❌ Error: CSV file not found at {DATA_PATH}")
    sys.exit()

# ── Evaluation Criteria & Test Cases ─────────────────────────────────────────
# We define test cases specifically for the 3 sub-criteria of Accuracy (40%)

TEST_CASES = [
    # 1. DATA RETRIEVAL (Correct SQL generation)
    {
        "category": "Data Retrieval",
        "id": "DR-1",
        "question": "What is the total claims paid amount for LIC in 2021-22?",
        "expected_sql_keywords": ["SUM", "claims_paid_amt", "LIC", "2021-22"],
        # UPDATED: Accepting 'table' here as well because a single number is valid in a table
        "expected_chart": ["bar", "metric", "table"], 
        "should_answer": True,
    },
    {
        "category": "Data Retrieval",
        "id": "DR-2",
        "question": "List the top 3 insurers by claims repudiated ratio in 2020-21",
        "expected_sql_keywords": ["ORDER BY", "DESC", "LIMIT", "repudiated_ratio", "2020-21"],
        "expected_chart": ["bar", "table"],
        "should_answer": True,
    },

    # 2. CONTEXTUAL CHART SELECTION (Correct visualization type)
    {
        "category": "Chart Selection",
        "id": "CS-1",
        "question": "Show the trend of total claims intimated over the years",
        "expected_sql_keywords": ["year", "claims_intimated"],
        "expected_chart": ["line"], # MUST be a line chart for trends
        "should_answer": True,
    },
    {
        "category": "Chart Selection",
        "id": "CS-2",
        "question": "Compare the claims paid amount of HDFC and ICICI",
        "expected_sql_keywords": ["HDFC", "ICICI", "claims_paid"],
        "expected_chart": ["bar"], # MUST be a bar chart for comparison
        "should_answer": True,
    },

    # 3. HALLUCINATION HANDLING (Refusing to answer impossible questions)
    {
        "category": "Hallucination Handling",
        "id": "HH-1",
        "question": "What is the stock price of HDFC Life today?",
        "expected_sql_keywords": [],
        "expected_chart": [],
        "should_answer": False, # System MUST refuse
    },
    {
        "category": "Hallucination Handling",
        "id": "HH-2",
        "question": "Show me the email addresses of the claimants",
        "expected_sql_keywords": [],
        "expected_chart": [],
        "should_answer": False, # System MUST refuse
    },
]

def evaluate():
    print("\n" + "=" * 80)
    print("  EVALUATION REPORT: ACCURACY FRAMEWORK")
    print("=" * 80)

    results = {
        "Data Retrieval": {"score": 0, "count": 0},
        "Chart Selection": {"score": 0, "count": 0},
        "Hallucination Handling": {"score": 0, "count": 0}
    }
    detailed_rows = []

    for case in TEST_CASES:
        cat = case["category"]
        results[cat]["count"] += 1
        
        print(f"Testing [{case['id']}]: {case['question'][:40]}...")
        
        # 1. Generate SQL
        sql, _ = generate_sql(case["question"])
        
        # Default scores
        sql_score = 0
        chart_score = 0
        status_icon = "❌"

        # ── SCORING LOGIC ──
        
        # CASE A: System should REFUSE (Hallucination Tests)
        if not case["should_answer"]:
            if sql is None or "ERROR" in str(sql).upper() or "CANNOT" in str(sql).upper():
                sql_score = 1.0
                status_icon = "✅ (Refused correctly)"
                results[cat]["score"] += 1
            else:
                status_icon = "❌ (Hallucinated!)"
                # Score remains 0

        # CASE B: System should ANSWER (Retrieval & Chart Tests)
        else:
            # Check SQL Keywords
            if sql:
                sql_lower = sql.lower()
                matches = sum(1 for kw in case["expected_sql_keywords"] if kw.lower() in sql_lower)
                sql_score = matches / len(case["expected_sql_keywords"])
                
                # Execute SQL
                df, err = execute_sql(sql)
                
                if df is not None and not df.empty:
                    # Check Chart Selection
                    vis = generate_visualization(case["question"], df)
                    c_type = vis.get("chart_type", "table")
                    
                    if c_type in case["expected_chart"]:
                        chart_score = 1.0
                        status_icon = "✅"
                        results[cat]["score"] += 1 # Full point for correct answer
                    else:
                        status_icon = "🟡 (Wrong Chart)"
                        results[cat]["score"] += 0.5 # Half point for data retrieval

        detailed_rows.append({
            "id": case["id"],
            "cat": cat,
            "sql_score": sql_score,
            "chart_score": chart_score,
            "status": status_icon,
            "question": case["question"][:30]
        })

    # ── PRINT REPORT ──
    print("\n" + "─" * 80)
    print(f"{'ID':<6} {'Category':<25} {'Status':<20} Question")
    print("─" * 80)
    
    for r in detailed_rows:
        print(f"{r['id']:<6} {r['cat']:<25} {r['status']:<20} {r['question']}...")

    print("─" * 80)
    
    # Calculate Final Scores
    dr_score = (results["Data Retrieval"]["score"] / results["Data Retrieval"]["count"]) * 100
    cs_score = (results["Chart Selection"]["score"] / results["Chart Selection"]["count"]) * 100
    hh_score = (results["Hallucination Handling"]["score"] / results["Hallucination Handling"]["count"]) * 100
    
    total_accuracy = (dr_score + cs_score + hh_score) / 3

    print(f"\n📊 DETAILED SCORES:")
    print(f"1. Data Retrieval         : {dr_score:.0f}%")
    print(f"2. Contextual Chart Select: {cs_score:.0f}%")
    print(f"3. Hallucination Handling : {hh_score:.0f}%")
    
    print(f"\n🏆 OVERALL ACCURACY SCORE: {total_accuracy:.1f}%")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    evaluate()