# llm_engine.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from utils.prompts import SQL_SYSTEM_PROMPT, VIS_SYSTEM_PROMPT
from utils.database import get_schema

# Load Environment Variables
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("❌ CRITICAL: OPENROUTER_API_KEY not found in .env file!")
else:
    print(f"🔑 OpenRouter Key loaded: {api_key[:10]}...")

# Configure OpenRouter Client
# OpenRouter is compatible with the OpenAI SDK
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Model ID for Llama 3.3 70B Instruct on OpenRouter
MODEL_NAME = "meta-llama/llama-3.3-70b-instruct"

def get_llm_response(prompt):
    """Generates content using OpenRouter (Llama 3.3)."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1, # Low temperature for factual SQL/Data tasks
        )
        return response.choices[0].message.content, None
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return None, str(e)

def generate_sql(user_query):
    """Generates SQL using Llama 3.3."""
    schema = get_schema()
    prompt = SQL_SYSTEM_PROMPT.format(schema=schema) + f"\nUser Question: {user_query}"
    
    print(f"🔄 Querying model: {MODEL_NAME}...")
    response, error = get_llm_response(prompt)
    
    if response:
        # Clean up the response (Llama usually follows instructions well)
        sql = response.replace("```sql", "").replace("```", "").strip()
        
        # Safety check for hallucinations
        if "cannot answer" in sql.lower() or "error" in sql.lower():
            return None, "Model determined it cannot answer this question."
        
        print(f"✅ SQL Generated successfully.")
        return sql, MODEL_NAME
    
    return None, error

def generate_visualization(user_query, df):
    """Decides chart type based on data."""
    data_json = df.head(20).to_json(orient="records")
    prompt = VIS_SYSTEM_PROMPT.format(query=user_query, data=data_json)
    
    response, error = get_llm_response(prompt)
    
    if response:
        try:
            # Clean potential markdown wrappers
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback if Llama returns text mixed with JSON
            print("⚠️ JSON parsing failed, falling back to table.")
            return {
                "chart_type": "table",
                "title": "Query Results",
                "explanation": "Could not determine optimal chart, showing table.",
                "error": True
            }
    
    # Fallback
    return {
        "chart_type": "table",
        "title": "Query Results",
        "explanation": "Displaying raw data.",
        "error": True
    }