# Main Streamlit Application
# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from utils.database import csv_to_sqlite, execute_sql, upload_csv_to_sqlite, get_uploaded_schema, get_schema
from llm_engine import generate_sql, generate_visualization, retry_sql

# Load Environment Variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="InsightAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for Sleek, Minimalist Design ──────────────────────────────────
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

    /* Global Selection Effect */
    ::selection {
        background-color: #FFB6C1;
        color: #000000;
    }

    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #FFFFFF;
    }

    /* Typography */
    .main-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, hsl(351, 100%, 86%), hsl(330, 100%, 71%));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        line-height: 1.1;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #FFB6C1;
        font-weight: 400;
        margin-top: 0;
        letter-spacing: -0.01em;
    }

    /* Sidebar Styles */
    [data-testid="stSidebar"] {
        background-color: rgba(18, 18, 18, 0.6) !important;
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-right: 1px solid #262626;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #262626;
    }
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: #FFFFFF !important;
        font-weight: 600;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, hsl(351, 100%, 86%), hsl(330, 100%, 71%));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Base Chat Layout */
    .stChatMessage {
        background-color: transparent;
        border: none;
        padding: 0.5rem 0;
        margin-bottom: 0.5rem;
    }

    /* Hide the Streamlit default avatar borders and backgrounds */
    [data-testid="stChatMessageAvatarUser"],
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* Hide the user and assistant icons entirely for a cleaner bubble look */
    [data-testid="chatAvatarIcon-user"],
    [data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }
    
    /* User Message Bubble Container Options */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        display: flex;
        flex-direction: row-reverse;
    }
    
    /* Right-align the bubble inside its stretching container without collapsing width */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"] {
        display: block;
        text-align: right;
    }
    
    /* User Markdown Bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdown {
        background: linear-gradient(135deg, hsl(330, 80%, 40%), hsl(310, 60%, 30%)) !important; /* Muted deep pink/purple */
        color: #FFFFFF !important;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        display: inline-block;
        width: fit-content;
        max-width: 80%;
        text-align: left;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }

    /* Assistant Message Bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stMarkdown {
        background-color: transparent !important;
        color: #FFFFFF !important;
        padding: 8px 0px;
    }
    
    /* Align Assistant chat container to the left */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        display: flex;
        justify-content: flex-start;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, hsl(351, 100%, 86%), hsl(330, 100%, 71%));
        color: #000000 !important;
        border: none;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        padding: 0.5rem 1.25rem;
        transition: all 0.3s ease;
        box-shadow: 0 0 10px rgba(255, 105, 180, 0.2);
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px rgba(255, 105, 180, 0.6);
        transform: translateY(-1px);
    }
    
    /* Secondary/Action Buttons in Sidebar */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #262626;
        background: none;
        color: #FFB6C1 !important;
        border: 1px solid #FFB6C1;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(255, 182, 193, 0.1);
        border: 1px solid hsl(351, 100%, 86%);
        color: hsl(351, 100%, 86%) !important;
        box-shadow: 0 0 10px rgba(255, 105, 180, 0.3);
    }

    /* Example Query Chips */
    .example-chip {
        background-color: #121212;
        border: 1px solid #262626;
        border-radius: 6px;
        padding: 10px 14px;
        margin: 6px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
        color: #FFFFFF;
    }
    .example-chip:hover {
        background-color: rgba(255, 182, 193, 0.05);
        border-color: #FFB6C1;
        color: #FFB6C1;
    }

    /* Metric Cards */
    .metric-card {
        background-color: rgba(18, 18, 18, 0.6);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #262626;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        height: 100%;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -5px rgba(255, 105, 180, 0.2);
        border-color: rgba(255, 105, 180, 0.5);
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: hsl(351, 100%, 86%);
        margin-bottom: 8px;
        text-shadow: 0 0 10px rgba(255, 105, 180, 0.3);
    }
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #FFFFFF;
        opacity: 0.8;
        line-height: 1.5;
    }

    /* Data Info Badge */
    .data-badge {
        background-color: rgba(255, 105, 180, 0.1);
        color: hsl(351, 100%, 86%);
        padding: 6px 14px;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
        margin: 4px 0 16px 0;
        border: 1px solid rgba(255, 105, 180, 0.3);
    }

    /* Cleaner Expander */
    .streamlit-expanderHeader {
        background-color: rgba(18, 18, 18, 0.6);
        backdrop-filter: blur(24px);
        color: #FFFFFF;
        border: 1px solid #262626;
        border-radius: 6px;
        font-family: 'Inter', sans-serif;
    }

    /* Status Container */
    .status-container {
        border-left: 2px solid hsl(351, 100%, 86%);
        padding-left: 12px;
        margin: 12px 0;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# ── Initialize Session State ─────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "using_uploaded" not in st.session_state:
    st.session_state.using_uploaded = False
if "uploaded_schema" not in st.session_state:
    st.session_state.uploaded_schema = None
if "uploaded_db_path" not in st.session_state:
    st.session_state.uploaded_db_path = None
if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

# ── Initialize Default Database ──────────────────────────────────────────────
@st.cache_resource
def init_db():
    csv_path = "data/India Life Insurance Claims.csv"
    if os.path.exists(csv_path):
        csv_to_sqlite(csv_path)
        return True
    return False

db_ready = init_db()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Data Configuration")
    
    if st.session_state.using_uploaded:
        st.markdown('<span class="data-badge">Custom Dataset Active</span>', unsafe_allow_html=True)
        if st.button("Revert to Default Dataset"):
            st.session_state.using_uploaded = False
            st.session_state.uploaded_schema = None
            st.session_state.uploaded_db_path = None
            st.session_state.history = []
            st.session_state.last_sql = None
            st.rerun()
    else:
        st.markdown('<span class="data-badge">Insurance Claims Verified Data</span>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload custom CSV data", type=["csv"], label_visibility="visible")
    
    if uploaded_file is not None:
        if st.button("Process Dataset"):
            with st.spinner("Processing..."):
                db_path, df, table_name = upload_csv_to_sqlite(uploaded_file)
                if db_path and df is not None:
                    st.session_state.using_uploaded = True
                    st.session_state.uploaded_db_path = db_path
                    st.session_state.uploaded_schema = get_uploaded_schema(df, table_name)
                    st.session_state.history = []
                    st.session_state.last_sql = None
                    st.rerun()

    st.markdown("---")

    st.markdown("### Suggested Inquiries")
    
    if st.session_state.using_uploaded:
        example_queries = [
            "Show me the first 10 rows of the dataset",
            "What is the total count of records?",
            "Provide a summary of the numerical columns",
            "List the unique categories in the dataset",
            "What are the top 5 highest values?",
        ]
    else:
        example_queries = [
            "Show total claims paid by insurer for 2021-22",
            "What is the trend of claims intimated over time?",
            "Top 5 insurers by claim settlement ratio",
            "Compare HDFC and ICICI paid amounts",
            "Which providers show the highest rejection rate?",
            "Distribution of claims by category",
        ]
    
    for q in example_queries:
        if st.button(q, key=f"chip_{q}", use_container_width=True):
            st.session_state.trigger_query = q

    st.markdown("---")

    if st.button("Clear Session"):
        st.session_state.history = []
        st.session_state.last_sql = None
        st.rerun()

# ── Helper: Render Chart ─────────────────────────────────────────────────────
def render_chart(df, vis_config, user_query):
    """Renders sleek, minimalist charts with neon pink theme."""
    chart_type = vis_config.get("chart_type", "table")
    title = vis_config.get("title", "Analysis Result")
    
    plotly_template = "plotly_dark"
    # Unified, professional color scheme (neon pinks)
    primary_color = "hsl(351, 100%, 86%)" 
    secondary_color = "hsl(330, 100%, 71%)"
    theme_pink = "#FFB6C1"
    hot_pink = "#FF69B4"
    categorical_colors = [primary_color, secondary_color, hot_pink, theme_pink, "#FFFFFF", "#262626"]
    
    # Common layout settings for minimalism
    common_layout = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", color="#FFFFFF", size=12),
        title=dict(text=title, font=dict(family="Space Grotesk", color="#FFFFFF", size=18, weight="bold"), pad=dict(b=20)),
        margin=dict(t=60, b=40, l=40, r=20),
        xaxis=dict(gridcolor='#262626', zerolinecolor='#262626', showline=False),
        yaxis=dict(gridcolor='#262626', zerolinecolor='#262626', showline=False),
    )
    
    try:
        if chart_type == "bar":
            fig = px.bar(
                df, 
                x=vis_config['x_axis'], 
                y=vis_config['y_axis'],
                text_auto='.2s',
                color_discrete_sequence=[primary_color],
                template=plotly_template
            )
            fig.update_traces(
                textfont_size=11, textfont_color="#FFFFFF", textangle=0, 
                textposition="outside", cliponaxis=False,
                marker_line_width=0
            )
            fig.update_layout(**common_layout)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        elif chart_type == "line":
            fig = px.line(
                df, 
                x=vis_config['x_axis'], 
                y=vis_config['y_axis'],
                markers=True,
                template=plotly_template,
                color_discrete_sequence=[primary_color]
            )
            fig.update_traces(line=dict(width=2), marker=dict(size=6, color="#000000", line=dict(width=2, color=primary_color)))
            fig.update_layout(**common_layout)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        elif chart_type == "pie":
            fig = px.pie(
                df, 
                names=vis_config['x_axis'], 
                values=vis_config['y_axis'],
                template=plotly_template,
                color_discrete_sequence=categorical_colors,
                hole=0.6
            )
            fig.update_traces(textposition='outside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
            fig.update_layout(**common_layout, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        elif chart_type == "scatter":
            fig = px.scatter(
                df,
                x=vis_config['x_axis'],
                y=vis_config['y_axis'],
                template=plotly_template,
                color_discrete_sequence=[primary_color],
                size_max=12
            )
            fig.update_traces(marker=dict(opacity=0.7, line=dict(width=1, color="#FFFFFF")))
            fig.update_layout(**common_layout)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        else:
            if len(df) == 1 and len(df.columns) == 1:
                st.markdown(f"**{title}**")
                # Format a single value dynamically as a clean metric
                st.metric(label=str(df.columns[0]), value=str(df.iloc[0, 0]))
            else:
                st.markdown(f"**{title}**")
                st.dataframe(df, use_container_width=True, hide_index=True)
            
        if vis_config.get("explanation"):
            st.markdown(f"<div style='font-size: 0.95rem; color: #FFFFFF; font-family: Inter, sans-serif; opacity: 0.9; margin-top: 15px;'>{vis_config['explanation']}</div>", unsafe_allow_html=True)
            
    except Exception as e:
        if len(df) == 1 and len(df.columns) == 1:
            st.metric(label=str(df.columns[0]), value=str(df.iloc[0, 0]))
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

# ── Main Content ─────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">InsightAI - Data Intelligence Platform</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Natural language interface for enterprise reporting</p>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Display Chat History ─────────────────────────────────────────────────────
for message in st.session_state.history:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            if "text" in message:
                st.write(message["text"])
            if "sql" in message:
                with st.expander("Query Details"):
                    st.code(message["sql"], language="sql")
            if "df" in message and "vis_config" in message:
                df = pd.DataFrame(message["df"])
                render_chart(df, message["vis_config"], message.get("query", ""))
            if "explanation" in message and "df" not in message: # Handle text-only explanations
                st.markdown(f"<div style='color: #FFFFFF; opacity: 0.8; font-size: 0.95rem; font-family: Inter, sans-serif;'>{message['explanation']}</div>", unsafe_allow_html=True)

# ── Chat Input ───────────────────────────────────────────────────────────────
user_input = st.chat_input("Enter your reporting request...")
active_query = user_input if user_input else st.session_state.get('trigger_query', None)

# ── Welcome State (No Messages Yet) ─────────────────────────────────────────
welcome_placeholder = st.empty()
if len(st.session_state.history) == 0:
    with welcome_placeholder.container():
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">Automated Synthesis</div>
                <div class="metric-label">
                    Natural Language Processing translates unstructured requests into precise SQL execution plans dynamically.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">Visual Intelligence</div>
                <div class="metric-label">
                    Algorithmic determination of optimal chart architectures tailored precisely to the returned data structure.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">Continuous Context</div>
                <div class="metric-label">
                    Stateful session memory enables iterative drill-downs and multi-step analytical workflows. 
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("##### System Initialization")
        st.markdown("""
        <div style='color: #FFFFFF; font-family: Inter, sans-serif; opacity: 0.8; font-size: 0.95rem; line-height: 1.6;'>
        The platform is connected to the default operational database. You may submit ad-hoc reporting requests 
        via the command interface below, or inject a custom reporting schema via the sidebar connection manager.
        Results will be rendered asynchronously.
        </div>
        """, unsafe_allow_html=True)

# Determine active DB and schema
active_db = st.session_state.uploaded_db_path if st.session_state.using_uploaded else None
active_schema = st.session_state.uploaded_schema if st.session_state.using_uploaded else None

if active_query and (db_ready or st.session_state.using_uploaded):
    # Clear the welcome placeholder immediately
    welcome_placeholder.empty()
    
    st.session_state.history.append({"role": "user", "content": active_query})
    st.chat_message("user").write(active_query)
    
    # Clear the trigger token if it was used
    if 'trigger_query' in st.session_state:
        st.session_state.trigger_query = None
    
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            
            conversation_history = st.session_state.history if len(st.session_state.history) > 1 else None
            previous_sql = st.session_state.last_sql
            
            sql, model_used = generate_sql(
                user_query=active_query, 
                schema_override=active_schema, 
                conversation_history=conversation_history,
                previous_sql=previous_sql
            )
            
            if not sql:
                error_text = "The requested information is not available in the current dataset schema. Please adjust your parameters."
                st.markdown(f"<span style='color: #FF69B4;'>{error_text}</span>", unsafe_allow_html=True)
                st.session_state.history.append({
                    "role": "assistant",
                    "text": error_text
                })
            else:
                df, error = execute_sql(sql, db_path=active_db)
                
                if error:
                    corrected_sql, _ = retry_sql(sql, error, user_input, schema_override=active_schema)
                    if corrected_sql:
                        df, error = execute_sql(corrected_sql, db_path=active_db)
                        if not error:
                            sql = corrected_sql
                
                if error:
                    st.error("System encountered an exception during data retrieval.")
                    st.session_state.history.append({
                        "role": "assistant",
                        "text": "System encountered an exception during data retrieval.",
                        "sql": sql
                    })
                elif df is None or df.empty:
                    st.markdown("<span style='color: #FFB6C1;'>The execution returned zero records. Please relax your filter constraints.</span>", unsafe_allow_html=True)
                    st.session_state.history.append({
                        "role": "assistant",
                        "text": "The execution returned zero records.",
                        "sql": sql
                    })
                else:
                    vis_config = generate_visualization(active_query, df)
                    
                    st.session_state.last_sql = sql
                    
                    with st.expander("Query Details"):
                        st.code(sql, language="sql")
                        
                    render_chart(df, vis_config, active_query)
                    
                    st.session_state.history.append({
                        "role": "assistant",
                        "text": "",
                        "sql": sql,
                        "df": df.to_dict(orient="records"),
                        "vis_config": vis_config,
                        "query": active_query
                    })

elif not db_ready and not st.session_state.using_uploaded:
    st.error("Data source unavailable. Please initiate a connection.")

