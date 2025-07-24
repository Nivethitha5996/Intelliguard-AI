import os
import cv2
import time
import base64
import numpy as np
import pandas as pd
import psycopg2
from PIL import Image
from pathlib import Path
from datetime import datetime
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv
from detection import detect_ppe, process_video
from utils import read_image, save_uploaded_file
from chatbot import get_chatbot_response
from email_service import send_violation_email
from database import ComplianceDB
from user_management import register_user, authenticate_user

# Set page config FIRST, before any other Streamlit commands!
st.set_page_config(
    page_title="Intelliguard: PPE Compliance Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def set_custom_theme():
    """Set custom theme CSS for the entire application"""
    # Get the absolute path to the background image
    bg_path = os.path.join(os.path.dirname(__file__), 'assets', 'background.jpg')
    
    # Convert the image to base64
    bg_base64 = ""
    if os.path.exists(bg_path):
        with open(bg_path, "rb") as img_file:
            bg_base64 = base64.b64encode(img_file.read()).decode()
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    :root {{
        --primary: #1e5fa3;
        --secondary: #3ed598;
        --accent: #ff6b6b;
        --text: #2d3748;
        
        --text-on-dark: #ffffff;
        --bg: #f7fafc;
        --card-bg: #ffffff;
        --success: #3ed598;
        --warning: #ffc107;
        --danger: #ff6b6b;
        --info: #17a2b8;
    }}
    
    /* Base styles */
    * {{
        font-family: 'Poppins', sans-serif !important;
    }}
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5 > div.block-container.st-emotion-cache-z5fcl4.ea3mdgi4 > div > div > div:nth-child(2) > div > div > div > div:nth-child(2) > div:nth-child(1) > p:nth-child(1){{
        color:white;
    }}
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5 > div.block-container.st-emotion-cache-z5fcl4.ea3mdgi4 > div > div > div:nth-child(2) > div > div > div > div:nth-child(2) > div:nth-child(1) > p:nth-child(2){{
        color:white;
    }}
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div.block-container.st-emotion-cache-z5fcl4.ea3mdgi4 > div > div > div.st-emotion-cache-1wmy9hl.e1f1d6gn0 > div > div > div.st-emotion-cache-keje6w.e1f1d6gn2 > div > div > div:nth-child(1) > div > div > div > p{{
        color:gray;
    }}
    /* Login page specific styles */
    .stApp {{
        background-image: url('data:image/jpg;base64,{bg_base64}');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    .login-container {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        padding: 2.5rem;
        margin: 2rem auto;
        max-width: 500px;
    }}
    
    .login-title {{
        color: var(--primary) !important;
        font-weight: 700;
        font-size: 2rem;
        margin-bottom: 0.5rem !important;
        text-align: center;
    }}
    
    .login-subtitle {{
       
        font-size: 1rem;
        text-align: center;
        margin-bottom: 2rem !important;
        font-weight: 400;
    }}
    
    /* Form elements */
    .stTextInput>div>div>input,
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div {{
        
        
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        color: white;
    }}
    
    .stTextInput>div>div>input:focus {{
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px rgba(30, 95, 163, 0.2) !important;
    }}
    
    /* Buttons */
    .stButton>button {{
        background-color: var(--primary) !important;
        color: var(--text-on-dark) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        width: 100%;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        background-color: #164b8a !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 95, 163, 0.2) !important;
        color: var(--text-on-dark) !important;
    }}
    
    /* Dashboard styles */
    .dashboard-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        color: var(--text) !important;
    }}
    
    .dashboard-title {{
        
        font-weight: 700;
        font-size: 1.8rem;
        margin: 0 !important;
    }}
    
    .dashboard-subtitle {{
        
        font-size: 1rem;
        margin: 0.5rem 0 0 0 !important;
        font-weight: 400;
    }}
    
    .card {{
        background-color: var(--card-bg) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        border: none !important;
        color: var(--text) !important;
    }}
    
    .card-title {{
        color: var(--text) !important;
        font-weight: 600;
        font-size: 1.2rem;
        margin-bottom: 1.5rem !important;
    }}
    
    /* Metrics cards */
    .metric-card {{
        background-color: var(--card-bg) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        border-left: 4px solid var(--primary) !important;
        color: var(--text) !important;
    }}
    
    .metric-title {{
        color: var(--text-light) !important;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 0.5rem !important;
    }}
    
    .metric-value {{
        color: var(--text) !important;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0 !important;
    }}
    
    .metric-change {{
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 0.5rem !important;
    }}
    
    .positive {{
        color: var(--success) !important;
    }}
    
    .negative {{
        color: var(--danger) !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        color: var(--text-light) !important;
        font-weight: 500;
        padding: 0.75rem 1.5rem !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--primary) !important;
        background-color: rgba(30, 95, 163, 0.05) !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: var(--primary) !important;
        background-color: rgba(30, 95, 163, 0.1) !important;
    }}
    
    /* Data tables */
    .stDataFrame {{
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        color: var(--text) !important;
    }}
    
    /* Chat bubbles */
    .user-message {{
        background-color: #f0f4f8 !important;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary);
        color: var(--text) !important;
    }}
    
    .bot-message {{
        background-color: #e6f2ff !important;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--secondary);
        color: var(--text) !important;
    }}
    
    /* Hide Streamlit default elements */
    #MainMenu, footer, [data-testid="stToolbar"] {{
        visibility: hidden !important;
    }}
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.st-emotion-cache-uf99v8.ea3mdgi5 > div.block-container.st-emotion-cache-z5fcl4.ea3mdgi4 > div > div > div.st-emotion-cache-1wmy9hl.e1f1d6gn0 > div > div.element-container.st-emotion-cache-1771rd8.e1f1d6gn3 > div{{
      position: relative !important;
      bottom: 0px !important;
      padding-bottom: 70px !important;
      padding-top: 1rem !important;
      background-color: transparent !important;
      z-index: 99 !important; 
    }}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .login-container {{
            padding: 1.5rem;
            margin: 1rem;
        }}
        
        .dashboard-header {{
            flex-direction: column;
            align-items: flex-start;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

def login_form():
    """Render the login form with modern styling"""
    with st.container():
        # Center the login form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="login-container">
                <h1 class="login-title">Welcome to Intelliguard</h1>
                <p class="login-subtitle">Sign in to your account to continue</p>
            """, unsafe_allow_html=True)
            
            with st.form("Login Form", clear_on_submit=False):
                email = st.text_input("User Name", placeholder="Enter your User Name", key="login_email")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
                
                # Login button
                login_btn = st.form_submit_button("LogIn", type="primary")
                
                
                
                if login_btn:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.chat_history = []
                        st.session_state.detection_results = None
                        st.session_state.violations = []
                        st.success(f"Welcome back, {user['full_name']}!")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid User or password")
            
            # Register option: use a Streamlit button instead of HTML link
            if st.button(" Don't have an account? Sign up", key="show_register_btn"):
                st.session_state.show_register = True
                st.experimental_rerun()

def registration_form():
    """Render the registration form with modern styling"""
    with st.container():
        # Center the registration form
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="login-container">
                <h1 class="login-title">Create Account</h1>
                <p class="login-subtitle">Get started with Intelliguard</p>
            """, unsafe_allow_html=True)
            
            with st.form("Registration Form", clear_on_submit=True):
                cols = st.columns(2)
                with cols[0]:
                    first_name = st.text_input("First Name", placeholder="First name", key="reg_firstname")
                with cols[1]:
                    last_name = st.text_input("Last Name", placeholder="Last name", key="reg_lastname")
                
                email = st.text_input("Email Address", placeholder="Your email address", key="reg_email")
                
                cols = st.columns(2)
                with cols[0]:
                    password = st.text_input("Password", type="password", placeholder="Create password", key="reg_password")
                with cols[1]:
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="reg_confirm")
                
                role = st.selectbox("Role", ["Safety Officer", "Administrator"], key="reg_role")
                
                submitted = st.form_submit_button("Create Account", type="primary")
                
                if submitted:
                    if not email or not password or not confirm_password or not first_name or not last_name:
                        st.error("All fields are required!")
                    elif password != confirm_password:
                        st.error("Passwords do not match!")
                    else:
                        full_name = f"{first_name} {last_name}"
                        username = email.split('@')[0]
                        if register_user(username, password, full_name, role.lower()):
                            st.success("Account created successfully! Please login.")
                            st.session_state.show_register = False
                            st.experimental_rerun()
                        else:
                            st.error("Email already exists. Please use a different email.")
            
            # Back to login option: use a Streamlit button instead of HTML link
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("""<div style="text-align: center; margin-top: 1.5rem;"></div>""", unsafe_allow_html=True)
            if st.button("Already have an account? Sign in", key="show_login_btn"):
                st.session_state.show_register = False
                st.experimental_rerun()

def show_dashboard():
    """Render the dashboard with modern styling"""
    # Dashboard header
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">PPE Compliance Dashboard</h1>
            <p class="dashboard-subtitle">Real-time monitoring and analytics</p>
        </div>
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="text-align: right;">
                <p style="margin: 0; font-weight: 600; color: white !important;">{}</p>
                <p style="margin: 0; font-size: 0.9rem; color: white !important;">{}</p>
            </div>
            <div style="width: 40px; height: 40px; border-radius: 50%; background-color: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-weight: 600;">
                {}
            </div>
        </div>
    </div>
    """.format(
        st.session_state.current_user['full_name'],
        st.session_state.current_user['role'].title(),
        st.session_state.current_user['full_name'][0].upper() if st.session_state.current_user.get('full_name') and len(st.session_state.current_user['full_name']) > 0 else "U"
    ), unsafe_allow_html=True)

    # Metrics cards
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 class="card-title">Key Metrics</h2>
    </div>
    """, unsafe_allow_html=True)

    db = ComplianceDB()
    stats = db.get_compliance_stats()

    cols = st.columns(4)
    metrics = [
        ("Total Checks", stats.get('total_checks', 0), "🛡️", "5% increase", "positive"),
        ("Compliance Rate", f"{stats.get('compliant_rate', 0)}%", "✅", "2% increase", "positive"),
        ("Violations", stats.get('violations', 0), "⚠️", "3% decrease", "negative"),
        ("Critical Issues", stats.get('critical', 0), "🚨", "1% increase", "negative")
    ]

    for i, (title, value, icon, change, change_class) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 class="metric-title">{title}</h3>
                    <div style="font-size: 1.5rem;">{icon}</div>
                </div>
                <h2 class="metric-value">{value}</h2>
                <p class="metric-change {change_class}">{change}</p>
            </div>
            """, unsafe_allow_html=True)

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Compliance Overview", "Recent Violations", "Trend Analysis"])

    with tab1:
        # Compliance overview chart
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 class="card-title">Compliance Status</h2>
        </div>
        """, unsafe_allow_html=True)

        with db._managed_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN violations_count = 0 THEN 1 ELSE 0 END) as compliant,
                    SUM(CASE WHEN violations_count > 0 AND violations_count <= 2 THEN 1 ELSE 0 END) as minor,
                    SUM(CASE WHEN violations_count > 2 THEN 1 ELSE 0 END) as major
                FROM compliance_logs
                WHERE timestamp >= current_date - interval '7 days'
            """)
            compliance_data = cur.fetchone()

        if compliance_data:
            total, compliant, minor, major = compliance_data
            data = {
                "Status": ["Compliant", "Minor Violations", "Major Violations"],
                "Count": [compliant, minor, major],
                "Color": ["#3ed598", "#ffc107", "#ff6b6b"]
            }
            fig = px.pie(
                data, 
                values="Count", 
                names="Status", 
                color="Color",
                color_discrete_map={
                    "Compliant": "#3ed598",
                    "Minor Violations": "#ffc107",
                    "Major Violations": "#ff6b6b"
                },
                hole=0.4
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.2,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No compliance data available for the last 7 days")

    with tab2:
        # Recent violations table
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 class="card-title">Recent Violations</h2>
        </div>
        """, unsafe_allow_html=True)

        with db._managed_cursor() as cur:
            cur.execute("""
                SELECT 
                    vd.detail_id as "Detail ID",
                    CASE 
                        WHEN vd.violation_type = 'no_helmet' THEN 'No Helmet'
                        WHEN vd.violation_type = 'no_mask' THEN 'No Mask'
                        WHEN vd.violation_type = 'no_gloves' THEN 'No Gloves'
                        WHEN vd.violation_type = 'no_goggles' THEN 'No Goggles'
                        ELSE vd.violation_type
                    END as "Violation Type",
                    ROUND(vd.confidence::numeric, 2) as "Confidence",
                    to_char(cl.timestamp, 'YYYY-MM-DD HH24:MI:SS') as "Timestamp",
                    (cl.details->>'location') as "Location"
                FROM violation_details vd
                JOIN compliance_logs cl ON vd.log_id = cl.log_id
                ORDER BY cl.timestamp DESC
                LIMIT 10
            """)
            violation_rows = cur.fetchall()

        if violation_rows:
            violations_df = pd.DataFrame(
                violation_rows,
                columns=['Detail ID', 'Violation Type', 'Confidence', 'Timestamp', 'Location']
            )
            
            st.dataframe(
                violations_df,
                column_config={
                    "Timestamp": st.column_config.DatetimeColumn(
                        "Timestamp",
                        format="YYYY-MM-DD HH:mm:ss"
                    ),
                    "Confidence": st.column_config.ProgressColumn(
                        "Confidence",
                        format="%.1f",
                        min_value=0,
                        max_value=1
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("🎉 No violations detected in recent checks!")
    
    with tab3:
        # Trend analysis
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <h2 class="card-title">Compliance Trend</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with db._managed_cursor() as cur:
            cur.execute("""
                SELECT date(timestamp) as day, 
                       COUNT(*) as total,
                       SUM(CASE WHEN violations_count = 0 THEN 1 ELSE 0 END) as compliant
                FROM compliance_logs
                WHERE timestamp >= current_date - interval '30 days'
                GROUP BY day
                ORDER BY day
            """)
            trend_data = cur.fetchall()
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data, columns=['Day', 'Total Checks', 'Compliant'])
            trend_df['Compliance Rate'] = (trend_df['Compliant'] / trend_df['Total Checks']) * 100
            fig = px.line(trend_df, x='Day', y='Compliance Rate', 
                         title="30-Day Compliance Trend",
                         markers=True)
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Date",
                yaxis_title="Compliance Rate (%)",
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No compliance data available for the last 30 days")

def show_upload_detect():
    """Render the PPE detection page with modern styling"""
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">PPE Detection</h1>
            <p class="dashboard-subtitle">Upload images or videos to analyze PPE compliance</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h2 class="card-title">Upload Media</h2>
            <p style="color: var(--text-light); margin-bottom: 1.5rem;">Supported formats: JPG, JPEG, PNG, MP4, AVI, MOV, MPEG4 (Max 200MB)</p>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=['jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov', 'mpeg4'],
            label_visibility="collapsed"
        )
        
        if uploaded_file and st.button("Analyze for PPE Compliance", type="primary"):
            st.session_state.processing = True
            try:
                if uploaded_file.type.startswith('image'):
                    image = read_image(uploaded_file)
                    with st.spinner("🔍 Analyzing image for PPE compliance..."):
                        annotated, violations, metrics = detect_ppe(image, confidence=0.7)
                        st.session_state.detection_results = {
                            "annotated": annotated,
                            "violations": violations,
                            "metrics": metrics,
                            "is_video": False
                        }
                        violation_counts = {}
                        for v in violations:
                            vt = v["violation_type"].replace("no_", "")
                            violation_counts[vt] = violation_counts.get(vt, 0) + 1
                        st.session_state.violation_counts = violation_counts
                        st.session_state.violations = [
                            v["violation_type"].replace("_", " ")
                            for v in violations
                        ]
                        # Log the violation to database
                        db = ComplianceDB()
                        db.log_violation({
                            'violations': violations,
                            'image_path': f"uploads/{uploaded_file.name}",
                            'location': 'Unknown',
                            'camera_id': 'web_upload',
                            'employee_id': st.session_state.current_user['username']
                        })
                        if violations:
                            email_sent = send_violation_email(violations, time_range="just now")
                            if email_sent:
                                st.success("📧 Violation alert email sent to safety heads.")
                else:
                    video_path = save_uploaded_file(uploaded_file)
                    with st.spinner("🎥 Processing video for PPE compliance..."):
                        output_path = os.path.join("outputs", f"processed_{os.path.basename(video_path)}")
                        violations, metrics = process_video(video_path, output_path)
                        st.session_state.detection_results = {
                            "processed_path": output_path,
                            "violations": violations,
                            "metrics": metrics,
                            "is_video": True
                        }
                        violation_counts = {}
                        for v in violations:
                            vt = v["violation_type"].replace("no_", "")
                            violation_counts[vt] = violation_counts.get(vt, 0) + 1
                        st.session_state.violation_counts = violation_counts
                        st.session_state.violations = [
                            v["violation_type"].replace("_", " ")
                            for v in violations
                        ]
                        # Log the violations to database
                        db = ComplianceDB()
                        for violation in violations:
                            db.log_violation({
                                'violations': [violation],
                                'image_path': output_path,
                                'location': 'Unknown',
                                'camera_id': 'web_upload',
                                'employee_id': st.session_state.current_user['username']
                            })
                        if violations:
                            email_sent = send_violation_email(violations, time_range="just now")
                            if email_sent:
                                st.success("📧 Violation alert email sent to safety heads.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            finally:
                st.session_state.processing = False
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.session_state.get('detection_results'):
            result = st.session_state.detection_results
            st.markdown("""
            <div style="margin-top: 2rem;">
                <h2 class="card-title">Detection Results</h2>
            </div>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown("""
                <div class="card">
                """, unsafe_allow_html=True)
                
                if result.get("is_video"):
                    st.video(result["processed_path"])
                else:
                    st.image(result["annotated"], use_column_width=True)
                
                st.markdown("""
                <h3 style="color: var(--text); margin-top: 1.5rem;">Analysis Summary</h3>
                """, unsafe_allow_html=True)
                
                cols = st.columns(2)
                with cols[0]:
                    st.metric("Total Violations", len(st.session_state.violations))
                
                with cols[1]:
                    if st.session_state.violations:
                        st.metric("Status", "Non-Compliant", delta="Violations Detected", delta_color="off")
                    else:
                        st.metric("Status", "Compliant", delta="No Violations", delta_color="normal")
                
                if hasattr(st.session_state, "violation_counts") and st.session_state.violation_counts:
                    st.markdown("""
                    <h3 style="color: var(--text); margin-top: 1.5rem;">Violation Breakdown</h3>
                    """, unsafe_allow_html=True)
                    
                    for vt, count in st.session_state.violation_counts.items():
                        st.progress(count/10, text=f"{count} × {vt.replace('_', ' ').title()}")
                
                if st.session_state.violations and len(st.session_state.violations) > 0:
                    st.markdown("""
                    <h3 style="color: var(--text); margin-top: 1.5rem;">Detailed Violations</h3>
                    """, unsafe_allow_html=True)
                    
                    for violation in st.session_state.violations:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; margin-bottom: 0.5rem; padding: 0.75rem; background-color: orangeRed; border-radius: 8px;">
                            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; 
                                background-color: {'#f44336' if 'helmet' in violation else '#ff9800'}; 
                                margin-right: 0.75rem;"></span>
                            <span style="font-weight: 500;">{violation.title()}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background-color:; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;">
                        <p style="margin: 0; color: #2e7d32; font-weight: 500;">
                            ✅ All PPE requirements are properly worn. No violations detected.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)

def show_chatbot():
    """Render the chatbot page with modern styling"""
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">Intelliguard Assistant</h1>
            <p class="dashboard-subtitle">Ask questions about PPE compliance and safety protocols</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h2 class="card-title">Chat with Intelliguard</h2>
        """, unsafe_allow_html=True)
        
        # Initialize chat history if not exists
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Hello! I'm your PPE compliance assistant. How can I help you today?"}
            ]
        
        # Display chat messages
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--primary);">You</div>
                    <div style="color: var(--text);">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="bot-message">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--secondary);">Intelliguard</div>
                    <div style="color: var(--text);">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Type your question about PPE compliance...")
        if user_input:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
            with st.spinner("Thinking..."):
                try:
                    response = get_chatbot_response(user_input)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response["answer"],
                        "data": response.get("data"),
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                except Exception as e:
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"Sorry, I encountered an error: {str(e)}",
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_logs_reports():
    """Render the logs and reports page with modern styling"""
    st.markdown("""
    <div class="dashboard-header">
        <div>
            <h1 class="dashboard-title">Compliance Logs</h1>
            <p class="dashboard-subtitle">View and export historical compliance data</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div class="card">
            <h2 class="card-title">Recent Compliance Checks</h2>
        """, unsafe_allow_html=True)
        
        db = ComplianceDB()
        with db._managed_cursor() as cur:
            cur.execute("""
                SELECT 
                    log_id as "ID",
                    to_char(timestamp, 'YYYY-MM-DD HH24:MI:SS') as "Timestamp",
                    violations_count as "Violations",
                    anomaly_status as "Status",
                    (details->>'location') as "Location",
                    (details->>'camera_id') as "Camera ID"
                FROM compliance_logs
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            logs = cur.fetchall()
        
        if logs:
            logs_df = pd.DataFrame(
                logs,
                columns=['ID', 'Timestamp', 'Violations', 'Status', 'Location', 'Camera ID']
            )
            
            st.dataframe(
                logs_df,
                column_config={
                    "Timestamp": st.column_config.DatetimeColumn(
                        "Timestamp",
                        format="YYYY-MM-DD HH:mm:ss"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Export options
            st.markdown("""
            <h3 style="color: var(--text); margin-top: 1.5rem;">Export Data</h3>
            """, unsafe_allow_html=True)
            
            cols = st.columns(3)
            with cols[0]:
                if st.button("Export as CSV"):
                    csv = logs_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="compliance_logs.csv",
                        mime="text/csv"
                    )
        else:
            st.info("No compliance logs available")
        
        st.markdown("</div>", unsafe_allow_html=True)

def main_app():
    """Main application layout with navigation"""
    # Navigation sidebar
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; flex-direction: column; height: 100%;">
            <div style="margin-bottom: 2rem;">
                <h2 style="color: var(--primary); margin-bottom: 0;">Intelliguard</h2>
                <p style="color: var(--text-light); margin-top: 0;">PPE Compliance System</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Navigation tabs
        selected_tab = st.radio(
            "Navigation",
            ["Dashboard", "PPE Detection", "Assistant", "Compliance Logs"],
            label_visibility="collapsed"
        )
        
        # Logout button
        st.markdown("""
            <div style="margin-top: auto; padding-bottom: 2rem;">
        """, unsafe_allow_html=True)
        if st.button("Logout", type="primary", key="logout_btn"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.chat_history = []
            st.session_state.detection_results = None
            st.session_state.violations = []
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display selected tab
    if selected_tab == "Dashboard":
        show_dashboard()
    elif selected_tab == "PPE Detection":
        show_upload_detect()
    elif selected_tab == "Assistant":
        show_chatbot()
    elif selected_tab == "Compliance Logs":
        show_logs_reports()

def main():
    """Main application function"""
    # Set custom theme
    set_custom_theme()
    
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # Show login/register if not authenticated
    if not st.session_state.authenticated:
        if st.session_state.show_register:
            registration_form()
        else:
            login_form()
    else:
        # Show main app if authenticated
        main_app()

if __name__ == "__main__":
    main()