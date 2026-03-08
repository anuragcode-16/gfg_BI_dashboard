# Main Streamlit Application
# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from utils.database import csv_to_sqlite, execute_sql
from llm_engine import generate_sql, generate_visualization

# Load Environment Variables
load_dotenv()

# Page Configuration
st.set_page_config(page_title="BI Dashboard AI", layout="wide")

# Custom CSS for Aesthetics
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E3A8A; font-weight: 700;}
    .sub-header {font-size: 1.5rem; color: #4B5563;}
    .stButton>button {background-color: #1E3A8A; color: white;}
    .css-1v0mbdj {margin-top: -5rem;} /* Remove default margins */
</style>
""", unsafe_allow_html=True)

# Initialize Database
@st.cache_resource
def init_db():
    csv_path = "data/India Life Insurance Claims.csv"
    if os.path.exists(csv_path):
        csv_to_sqlite(csv_path)
        return True
    return False

db_ready = init_db()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9472/9472146.png", width=100)
    st.markdown("## Dashboard Controls")
    st.info("This prototype uses the **India Life Insurance Claims** dataset.")
    
    # Chat History
    if "history" not in st.session_state:
        st.session_state.history = []
    
    if st.button("Clear History"):
        st.session_state.history = []
        st.rerun()

# Main Layout
st.markdown('<p class="main-header">Conversational Business Intelligence</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Ask a question about your insurance data</p>', unsafe_allow_html=True)

# Input Area
user_input = st.chat_input("e.g., Show total paid claims amount by life insurer for 2021-22")

if user_input and db_ready:
    # 1. Display User Query
    st.chat_message("user").write(user_input)
    
    with st.chat_message("assistant"):
        with st.status("Analyzing request...", expanded=True) as status:
            # Step A: Generate SQL
            st.write("🧠 Thinking... Generating SQL query...")
            sql, model_used = generate_sql(user_input)
            
            if not sql:
                st.error("❌ I could not generate a query for that request. Please try rephrasing.")
                st.write(f"Error: {model_used}")
            else:
                st.write(f"✅ SQL Generated (via {model_used}):")
                st.code(sql, language="sql")
                
                # Step B: Execute SQL
                st.write("⚡ Executing query on database...")
                df, error = execute_sql(sql)
                
                if error:
                    st.error(f"SQL Error: {error}")
                elif df.empty:
                    st.warning("Query returned no data.")
                else:
                    # Step C: Generate Visualization
                    st.write("📊 determining best visualization...")
                    vis_config = generate_visualization(user_input, df)
                    
                    # Update Status
                    status.update(label="Analysis Complete!", state="complete")
                    
                    # Display Logic
                    st.markdown(f"### {vis_config.get('title', 'Results')}")
                    
                    chart_type = vis_config.get("chart_type", "table")
                    
                    try:
                        if chart_type == "bar":
                            fig = px.bar(df, x=vis_config['x_axis'], y=vis_config['y_axis'], 
                                         text_auto='.2s', title=vis_config['title'])
                            fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
                            st.plotly_chart(fig, use_container_width=True)
                            
                        elif chart_type == "line":
                            fig = px.line(df, x=vis_config['x_axis'], y=vis_config['y_axis'], 
                                          title=vis_config['title'], markers=True)
                            st.plotly_chart(fig, use_container_width=True)
                            
                        elif chart_type == "pie":
                            fig = px.pie(df, names=vis_config['x_axis'], values=vis_config['y_axis'], 
                                         title=vis_config['title'])
                            st.plotly_chart(fig, use_container_width=True)
                            
                        else: # Default to Table
                            st.dataframe(df, use_container_width=True)
                            
                        # Insight Explanation
                        if vis_config.get("explanation"):
                            st.info(f"💡 **Insight:** {vis_config['explanation']}")
                            
                    except Exception as e:
                        st.error(f"Error rendering chart: {e}")
                        st.dataframe(df, use_container_width=True)

elif not db_ready:
    st.error("Database initialization failed. Please check if CSV exists in /data folder.")