# llm_engine.py
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from utils.prompts import (
    SQL_SYSTEM_PROMPT,
    SQL_FOLLOWUP_PROMPT,
    SQL_RETRY_PROMPT,
    VIS_SYSTEM_PROMPT,
    RAG_SQL_PROMPT,
    RAG_CONTEXT_HEADER,
    RAG_EXAMPLE_TEMPLATE,
)
from utils.database import get_schema
from utils.rag_store import rag_store

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

def _build_rag_context(user_query: str, session_id: str | None) -> str:
    """
    Retrieve the top-3 semantically similar past interactions from the RAG store
    and format them as a few-shot context block for injection into the prompt.
    Returns an empty string when no relevant history is found.
    """
    similar = rag_store.retrieve_similar(user_query, n_results=3, session_id=session_id)
    if not similar:
        return ""

    examples_text = "\n\n".join(
        RAG_EXAMPLE_TEMPLATE.format(
            query=item["query"],
            sql=item["sql"],
            result_summary=item["result_summary"],
        )
        for item in similar
    )
    rag_context = RAG_CONTEXT_HEADER.format(examples=examples_text)
    print(f"📚 RAG: injecting {len(similar)} similar interaction(s) into prompt.")
    return rag_context


def generate_sql(
    user_query,
    schema_override=None,
    conversation_history=None,
    previous_sql=None,
    session_id=None,
):
    """
    Generates SQL using Llama 3.3.

    Priority order for context:
      1. Conversation history + previous SQL  → SQL_FOLLOWUP_PROMPT
      2. RAG-retrieved similar past examples   → RAG_SQL_PROMPT (new)
      3. No prior context                      → SQL_SYSTEM_PROMPT (baseline)
    """
    schema = schema_override if schema_override else get_schema()

    if conversation_history and previous_sql:
        # In-session follow-up: use the dedicated follow-up prompt
        history_text = "\n".join(
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg.get('content', msg.get('text', ''))}"
            for msg in conversation_history[-6:]  # last 3 exchanges
        )
        prompt = SQL_FOLLOWUP_PROMPT.format(
            history=history_text,
            previous_sql=previous_sql,
            schema=schema,
            query=user_query,
        )
    else:
        # First question (or new session) – enrich with RAG context
        rag_context = _build_rag_context(user_query, session_id)
        if rag_context:
            prompt = RAG_SQL_PROMPT.format(
                schema=schema,
                rag_context=rag_context,
                query=user_query,
            )
        else:
            # Pure baseline – no prior context available
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