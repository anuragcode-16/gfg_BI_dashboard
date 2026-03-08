# llm_engine.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from utils.prompts import SQL_SYSTEM_PROMPT, SQL_FOLLOWUP_PROMPT, SQL_RETRY_PROMPT, VIS_SYSTEM_PROMPT
from utils.database import get_schema

# Load Environment Variables
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("❌ CRITICAL: OPENROUTER_API_KEY not found in .env file!")
else:
    print(f"🔑 OpenRouter Key loaded: {api_key[:10]}...")

# Configure OpenRouter Client
client = None
if api_key:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

# Model ID for Llama 3.3 70B Instruct on OpenRouter
MODEL_NAME = "meta-llama/llama-3.3-70b-instruct"

def get_llm_response(prompt):
    """Generates content using OpenRouter (Llama 3.3)."""
    if not client:
        return None, "API key not configured. Please set OPENROUTER_API_KEY in .env file."
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content, None
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return None, str(e)

def generate_sql(user_query, schema_override=None, conversation_history=None, previous_sql=None):
    """Generates SQL using Llama 3.3, with optional conversation context and custom schema."""
    schema = schema_override if schema_override else get_schema()
    
    # Use follow-up prompt if there's conversation history
    if conversation_history and previous_sql:
        history_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg.get('content', msg.get('text', ''))}" 
            for msg in conversation_history[-6:]  # Last 3 exchanges
        ])
        prompt = SQL_FOLLOWUP_PROMPT.format(
            history=history_text,
            previous_sql=previous_sql,
            schema=schema,
            query=user_query
        )
    else:
        prompt = SQL_SYSTEM_PROMPT.format(schema=schema) + f"\nUser Question: {user_query}"
    
    print(f"🔄 Querying model: {MODEL_NAME}...")
    response, error = get_llm_response(prompt)
    
    if response:
        sql = response.replace("```sql", "").replace("```", "").strip()
        
        # Safety check for refusal
        if "cannot answer" in sql.lower() or "error:" in sql.lower():
            return None, "Model determined it cannot answer this question with the available data."
        
        print(f"✅ SQL Generated successfully.")
        return sql, MODEL_NAME
    
    return None, error

def retry_sql(bad_sql, error_msg, user_query, schema_override=None):
    """Attempts to fix a failed SQL query using the LLM."""
    schema = schema_override if schema_override else get_schema()
    prompt = SQL_RETRY_PROMPT.format(
        bad_sql=bad_sql,
        error=error_msg,
        schema=schema,
        query=user_query
    )
    
    print(f"🔄 Retrying SQL generation...")
    response, error = get_llm_response(prompt)
    
    if response:
        sql = response.replace("```sql", "").replace("```", "").strip()
        if "cannot answer" in sql.lower() or "error:" in sql.lower():
            return None, "Could not fix the query."
        print(f"✅ Corrected SQL generated.")
        return sql, MODEL_NAME
    
    return None, error

def generate_visualization(user_query, df):
    """Decides chart type based on data."""
    data_json = df.head(20).to_json(orient="records")
    prompt = VIS_SYSTEM_PROMPT.format(query=user_query, data=data_json)
    
    response, error = get_llm_response(prompt)
    
    if response:
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed, falling back to table.")
            return {
                "chart_type": "table",
                "title": "Query Results",
                "explanation": "Could not determine optimal chart, showing table.",
                "error": True
            }
    
    return {
        "chart_type": "table",
        "title": "Query Results",
        "explanation": "Displaying raw data.",
        "error": True
    }