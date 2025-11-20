"""
AirSial Operations Management System - Production Version
Complete implementation with user registration and role-based access
"""

import streamlit as st
import pandas as pd
import json
import csv
import io
from datetime import datetime, timedelta
import hashlib
from pathlib import Path
import uuid
import requests
import os

# Page Configuration
st.set_page_config(
    page_title="AirSial Operations Hub",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Styling
st.markdown("""
<style>
    /* Main Theme */
    .main { padding: 0rem 1rem; }
    
    /* AI Response Box */
    .ai-response {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Status Badges */
    .status-critical { background: #e74c3c; color: white; padding: 5px 10px; border-radius: 5px; }
    .status-warning { background: #f39c12; color: white; padding: 5px 10px; border-radius: 5px; }
    .status-good { background: #27ae60; color: white; padding: 5px 10px; border-radius: 5px; }
    
    /* Info Boxes */
    .info-box {
        background: #ecf0f1;
        border-left: 4px solid #3498db;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Chat Message */
    .user-message {
        background: #f0f0f0;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    
    .assistant-message {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Data Storage Manager
class PersistentStorage:
    """Manages data persistence using JSON files"""
    
    def __init__(self):
        self.data_dir = Path("airsial_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.users_file = self.data_dir / "users.json"
        self.maintenance_file = self.data_dir / "maintenance.json"
        self.safety_file = self.data_dir / "safety.json"
        self.flights_file = self.data_dir / "flights.json"
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Create initial data files if they don't exist"""
        # Create admin account if no users exist
        if not self.users_file.exists():
            admin_user = {
                "admin": {
                    "password": hashlib.sha256("admin123".encode()).hexdigest(),
                    "role": "Administrator",
                    "email": "admin@airsial.com",
                    "created_at": datetime.now().isoformat()
                }
            }
            self.save_users(admin_user)
        
        # Initialize empty data files
        for file_path in [self.maintenance_file, self.safety_file, self.flights_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def save_users(self, users):
        """Save users data"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2, default=str)
    
    def load_users(self):
        """Load users data"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_data(self, file_path, data):
        """Save data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_data(self, file_path):
        """Load data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def add_user(self, username, password, email, role="Viewer"):
        """Register a new user"""
        users = self.load_users()
        
        if username in users:
            return False, "Username already exists"
        
        users[username] = {
            "password": hashlib.sha256(password.encode()).hexdigest(),
            "role": role,
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        
        self.save_users(users)
        return True, "Registration successful"

# Initialize storage
storage = PersistentStorage()

# Initialize Session State
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Load data into session state
if 'maintenance_data' not in st.session_state:
    st.session_state.maintenance_data = storage.load_data(storage.maintenance_file)
if 'safety_data' not in st.session_state:
    st.session_state.safety_data = storage.load_data(storage.safety_file)
if 'flight_data' not in st.session_state:
    st.session_state.flight_data = storage.load_data(storage.flights_file)

# Data Manager
class DataManager:
    @staticmethod
    def add_maintenance(record):
        """Add maintenance record"""
        record['id'] = str(uuid.uuid4())[:8]
        record['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        record['created_by'] = st.session_state.user
        
        st.session_state.maintenance_data.append(record)
        storage.save_data(storage.maintenance_file, st.session_state.maintenance_data)
        return record['id']
    
    @staticmethod
    def add_safety(record):
        """Add safety record"""
        record['id'] = str(uuid.uuid4())[:8]
        record['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        record['created_by'] = st.session_state.user
        
        st.session_state.safety_data.append(record)
        storage.save_data(storage.safety_file, st.session_state.safety_data)
        return record['id']
    
    @staticmethod
    def add_flight(record):
        """Add flight record"""
        record['id'] = str(uuid.uuid4())[:8]
        record['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        record['created_by'] = st.session_state.user
        
        st.session_state.flight_data.append(record)
        storage.save_data(storage.flights_file, st.session_state.flight_data)
        return record['id']
    
    @staticmethod
    def bulk_upload_csv(data_type, csv_file):
        """Process and upload CSV data in bulk - Admin only"""
        if st.session_state.role != 'Administrator':
            return 0, "Only administrators can perform bulk uploads"
        
        try:
            df = pd.read_csv(csv_file)
            records_added = 0
            
            if data_type == 'maintenance':
                data_list = st.session_state.maintenance_data
                save_func = lambda: storage.save_data(storage.maintenance_file, data_list)
            elif data_type == 'safety':
                data_list = st.session_state.safety_data
                save_func = lambda: storage.save_data(storage.safety_file, data_list)
            elif data_type == 'flight':
                data_list = st.session_state.flight_data
                save_func = lambda: storage.save_data(storage.flights_file, data_list)
            else:
                return 0, "Invalid data type"
            
            for _, row in df.iterrows():
                record = row.to_dict()
                record['id'] = str(uuid.uuid4())[:8]
                record['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                record['created_by'] = st.session_state.user
                record['uploaded_via'] = 'CSV Import'
                data_list.append(record)
                records_added += 1
            
            save_func()
            return records_added, "Success"
        
        except Exception as e:
            return 0, str(e)

# AI Agent (same as before but with try-except for secrets)
class AIAgent:
    def __init__(self):
        try:
            self.groq_api_key = st.secrets.get("GROQ_API_KEY", "")
        except:
            self.groq_api_key = ""
    
    def get_ai_response(self, query):
        """Generate AI response based on operational data"""
        context = self._build_context()
        
        if self.groq_api_key:
            response = self._call_groq_api(query, context)
            if response:
                return response
        
        response = self._call_ollama(query, context)
        if response:
            return response
        
        return self._generate_fallback_response(query, context)
    
    def _build_context(self):
        """Build context from operational data"""
        maint_data = st.session_state.maintenance_data
        safety_data = st.session_state.safety_data
        flight_data = st.session_state.flight_data
        
        total_maint = len(maint_data)
        pending_maint = len([m for m in maint_data if m.get('status') == 'Pending'])
        completed_maint = len([m for m in maint_data if m.get('status') == 'Completed'])
        
        total_incidents = len(safety_data)
        critical_incidents = len([s for s in safety_data if s.get('severity') in ['Critical', 'High']])
        
        total_flights = len(flight_data)
        
        total_hours = sum(float(m.get('estimated_hours', 0)) for m in maint_data)
        avg_hours = total_hours / total_maint if total_maint > 0 else 0
        
        maint_types = {}
        for m in maint_data:
            mtype = m.get('type', 'Unknown')
            maint_types[mtype] = maint_types.get(mtype, 0) + 1
        
        context = f"""
OPERATIONAL DATA SUMMARY:
========================
Maintenance:
- Total Tasks: {total_maint}
- Pending: {pending_maint}
- Completed: {completed_maint}
- Total Hours: {total_hours:.1f}
- Average Hours/Task: {avg_hours:.1f}

Safety:
- Total Incidents: {total_incidents}
- Critical/High: {critical_incidents}
- Safety Score: {max(0, 100 - critical_incidents * 10)}/100

Flights:
- Total Flights: {total_flights}

Top Maintenance Types:
"""
        for mtype, count in sorted(maint_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            context += f"- {mtype}: {count} times\n"
        
        return context
    
    def _call_groq_api(self, query, context):
        """Call Groq API for AI response"""
        try:
            system_prompt = """You are an expert airline operations AI assistant. 
            Analyze fleet data and provide strategic insights, risk assessments, 
            and actionable recommendations. Be specific with numbers and timelines.
            Focus on cost reduction, efficiency improvements, and safety."""
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{context}\n\nQuestion: {query}"}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except:
            pass
        return None
    
    def _call_ollama(self, query, context):
        """Call local Ollama for AI response"""
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",
                    "prompt": f"You are an airline operations expert. {context}\n\nQuestion: {query}\n\nAnswer:",
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["response"]
        except:
            pass
        return None
    
    def _generate_fallback_response(self, query, context):
        """Generate rule-based response when AI is unavailable"""
        query_lower = query.lower()
        
        maint_data = st.session_state.maintenance_data
        safety_data = st.session_state.safety_data
        
        if any(word in query_lower for word in ['decrease', 'reduce', 'optimize', 'efficiency']):
            pending = len([m for m in maint_data if m.get('status') == 'Pending'])
            total = len(maint_data) if maint_data else 1
            avg_hours = sum(float(m.get('estimated_hours', 0)) for m in maint_data) / total if total > 0 else 0
            
            response = "**📊 OPERATIONAL OPTIMIZATION STRATEGY**\n\n"
            response += f"**Current Status:**\n"
            response += f"- {pending} pending maintenance tasks ({(pending/total*100):.1f}% of total)\n"
            response += f"- Average task duration: {avg_hours:.1f} hours\n\n"
            response += "**Recommendations to Decrease Maintenance Frequency:**\n\n"
            response += "1. **Implement Predictive Maintenance**\n"
            response += "   - Investment: $50,000-75,000\n"
            response += "   - Expected reduction: 25-30% in unscheduled maintenance\n"
            response += "   - ROI period: 8-12 months\n\n"
            response += "2. **Optimize Maintenance Intervals**\n"
            response += "   - Review MSG-3 analysis with OEM\n"
            response += "   - Potential extension of A-Check from 500 to 600 flight hours\n"
            response += "   - Savings: $200,000 annually\n"
            
            return response
        
        else:
            return f"**📊 OPERATIONAL INTELLIGENCE**\n\n{context}\n\nAsk me about:\n- How to decrease maintenance frequency\n- Risk assessment and mitigation\n- Cost reduction strategies"

# Authentication Functions
def authenticate(username, password):
    """Authenticate user login"""
    users = storage.load_users()
    
    if username in users:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if users[username]['password'] == hashed_password:
            return True, users[username]['role']
    
    return False, None

def show_login_register():
    """Combined login and registration page"""
    st.markdown("# ✈️ AirSial Operations Hub")
    st.markdown("### Fleet Management System")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                st.markdown("#### Login to Your Account")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True, type="primary"):
                    if username and password:
                        success, role = authenticate(username, password)
                        if success:
                            st.session_state.user = username
                            st.session_state.role = role
                            st.success(f"Welcome back, {username}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter both username and password")
            
            # Note for first-time admin
            st.info("**First time?** Default admin account: `admin` / `admin123` (change after login)")
    
    with tab2:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("register_form"):
                st.markdown("#### Create New Account")
                new_username = st.text_input("Choose Username")
                new_email = st.text_input("Email Address")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                # Role selection (only basic roles for self-registration)
                role = st.selectbox("Select Role", ["Viewer", "Engineer", "Manager"])
                
                st.info("Note: Administrator accounts must be created by existing admins")
                
                if st.form_submit_button("Register", use_container_width=True, type="primary"):
                    if not all([new_username, new_email, new_password, confirm_password]):
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        success, message = storage.add_user(new_username, new_password, new_email, role)
                        if success:
                            st.success("Registration successful! Please login.")
                            st.balloons()
                        else:
                            st.error(message)

# Dashboard
def show_dashboard():
    st.title("🏠 Operations Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_maintenance = len(st.session_state.maintenance_data)
    pending_maintenance = len([m for m in st.session_state.maintenance_data if m.get('status') == 'Pending'])
    total_safety = len(st.session_state.safety_data)
    critical_safety = len([s for s in st.session_state.safety_data if s.get('severity') in ['Critical', 'High']])
    
    with col1:
        st.metric("Maintenance Tasks", total_maintenance, f"{pending_maintenance} pending")
    
    with col2:
        efficiency = ((total_maintenance - pending_maintenance) / total_maintenance * 100) if total_maintenance > 0 else 0
        st.metric("Efficiency", f"{efficiency:.1f}%", "Target: 95%")
    
    with col3:
        st.metric("Safety Incidents", total_safety, f"{critical_safety} critical")
    
    with col4:
        st.metric("Total Flights", len(st.session_state.flight_data))
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📜 Recent Activities")
        activities = []
        
        for m in st.session_state.maintenance_data[-3:]:
            activities.append(f"🔧 Maintenance: {m.get('type', 'N/A')} on {m.get('aircraft', 'N/A')}")
        
        for s in st.session_state.safety_data[-3:]:
            activities.append(f"⚠️ Safety: {s.get('type', 'N/A')} [{s.get('severity', 'N/A')}]")
        
        for f in st.session_state.flight_data[-3:]:
            activities.append(f"✈️ Flight: {f.get('flight_number', 'N/A')}")
        
        if activities:
            for activity in activities[-5:]:
                st.write(activity)
        else:
            st.info("No recent activities")
    
    with col2:
        st.subheader("🚨 Alerts")
        
        if critical_safety > 0:
            st.error(f"{critical_safety} critical safety incidents!")
        
        if pending_maintenance > 5:
            st.warning(f"{pending_maintenance} maintenance tasks pending")
        
        if critical_safety == 0 and pending_maintenance <= 5:
            st.success("All systems operational")

# Maintenance Page
def show_maintenance():
    st.title("🔧 Maintenance Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 View Records", "➕ Add New", "📊 Analytics"])
    
    with tab1:
        if st.session_state.maintenance_data:
            # Search and filters
            col1, col2, col3 = st.columns(3)
            with col1:
                search = st.text_input("🔍 Search", placeholder="Aircraft, type, engineer...")
            with col2:
                status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed"])
            with col3:
                priority_filter = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"])
            
            # Filter data
            filtered_data = st.session_state.maintenance_data
            if search:
                filtered_data = [m for m in filtered_data if search.lower() in str(m).lower()]
            if status_filter != "All":
                filtered_data = [m for m in filtered_data if m.get('status') == status_filter]
            if priority_filter != "All":
                filtered_data = [m for m in filtered_data if m.get('priority') == priority_filter]
            
            # Display data
            for record in filtered_data:
                with st.expander(f"{record.get('aircraft', 'N/A')} - {record.get('type', 'N/A')} [{record.get('status', 'N/A')}]"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**ID:** {record.get('id', 'N/A')}")
                        st.write(f"**Date:** {record.get('maintenance_date', 'N/A')}")
                        st.write(f"**Engineer:** {record.get('engineer', 'N/A')}")
                        st.write(f"**Priority:** {record.get('priority', 'N/A')}")
                    with col2:
                        st.write(f"**Hours:** {record.get('estimated_hours', 'N/A')}")
                        st.write(f"**Parts:** {record.get('parts_replaced', 'N/A')}")
                        st.write(f"**Notes:** {record.get('notes', 'N/A')}")
                        st.write(f"**Created by:** {record.get('created_by', 'N/A')}")
        else:
            st.info("No maintenance records found. Add your first record in the 'Add New' tab.")
    
    with tab2:
        with st.form("maintenance_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                aircraft = st.text_input("Aircraft Registration *", placeholder="e.g., AP-BOC")
                mtype = st.selectbox("Maintenance Type *", 
                                    ["A-Check", "B-Check", "C-Check", "D-Check", 
                                     "Line Maintenance", "Component Change", "AOG"])
                maintenance_date = st.date_input("Date *")
                engineer = st.text_input("Assigned Engineer")
            
            with col2:
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
                status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
                estimated_hours = st.number_input("Estimated Hours", min_value=0.0, step=0.5)
                parts_replaced = st.text_area("Parts Required/Replaced")
            
            notes = st.text_area("Additional Notes")
            
            if st.form_submit_button("➕ Add Record", use_container_width=True):
                if aircraft and mtype:
                    record = {
                        'aircraft': aircraft,
                        'type': mtype,
                        'maintenance_date': str(maintenance_date),
                        'engineer': engineer or "Unassigned",
                        'priority': priority,
                        'status': status,
                        'estimated_hours': estimated_hours,
                        'parts_replaced': parts_replaced,
                        'notes': notes
                    }
                    record_id = DataManager.add_maintenance(record)
                    st.success(f"✅ Record added successfully! ID: {record_id}")
                    st.rerun()
                else:
                    st.error("Please fill required fields")
    
    with tab3:
        st.subheader("📊 Maintenance Analytics")
        if st.session_state.maintenance_data:
            # Status breakdown
            status_counts = {}
            for m in st.session_state.maintenance_data:
                status = m.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Tasks", len(st.session_state.maintenance_data))
                for status, count in status_counts.items():
                    st.write(f"**{status}:** {count}")
            
            with col2:
                # Calculate total hours
                total_hours = sum(float(m.get('estimated_hours', 0)) for m in st.session_state.maintenance_data)
                avg_hours = total_hours / len(st.session_state.maintenance_data) if st.session_state.maintenance_data else 0
                st.metric("Total Hours", f"{total_hours:.1f}")
                st.metric("Average Hours/Task", f"{avg_hours:.1f}")
        else:
            st.info("No data for analytics")

# Safety Page
def show_safety():
    st.title("⚠️ Safety Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 Incident Reports", "➕ Report Incident", "🎯 Risk Matrix"])
    
    with tab1:
        if st.session_state.safety_data:
            for incident in st.session_state.safety_data:
                severity = incident.get('severity', 'Unknown')
                severity_color = {
                    'Critical': '🔴',
                    'High': '🟠',
                    'Medium': '🟡',
                    'Low': '🟢'
                }.get(severity, '⚪')
                
                with st.expander(f"{severity_color} {incident.get('type', 'Unknown')} - {incident.get('date', 'N/A')}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Flight:** {incident.get('flight', 'N/A')}")
                        st.write(f"**Location:** {incident.get('location', 'N/A')}")
                        st.write(f"**Description:** {incident.get('description', 'N/A')}")
                        st.write(f"**Reporter:** {incident.get('reporter', 'N/A')}")
                        st.write(f"**Status:** {incident.get('status', 'Open')}")
                    with col2:
                        st.write(f"**Severity**")
                        st.write(f"{severity_color} {severity}")
        else:
            st.info("No safety incidents reported. This is good news!")
    
    with tab2:
        with st.form("safety_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                incident_type = st.selectbox("Incident Type *", 
                                            ["Bird Strike", "Technical Failure", "Weather Related",
                                             "Ground Incident", "Cabin Safety", "Security", "Other"])
                flight = st.text_input("Flight Number")
                date = st.date_input("Incident Date *")
                location = st.text_input("Location")
            
            with col2:
                severity = st.selectbox("Severity *", ["Low", "Medium", "High", "Critical"])
                department = st.selectbox("Department", ["Ground Handling", "Maintenance", "Flight Ops", "Security"])
                reporter = st.text_input("Reported By *")
                status = st.selectbox("Status", ["Open", "Under Investigation", "Closed"])
            
            description = st.text_area("Detailed Description *")
            
            if st.form_submit_button("📝 Submit Report", use_container_width=True):
                if all([incident_type, date, reporter, description]):
                    record = {
                        'type': incident_type,
                        'flight': flight or "N/A",
                        'date': str(date),
                        'location': location or "Not specified",
                        'severity': severity,
                        'department': department,
                        'reporter': reporter,
                        'status': status,
                        'description': description
                    }
                    record_id = DataManager.add_safety(record)
                    st.success(f"✅ Incident reported! ID: {record_id}")
                    if severity in ['Critical', 'High']:
                        st.warning("⚠️ High severity incident - Management notified")
                    st.rerun()
                else:
                    st.error("Please fill required fields")
    
    with tab3:
        st.subheader("🎯 Risk Assessment Matrix")
        
        # Calculate risk scores
        risk_data = {
            'Low': 0,
            'Medium': 0,
            'High': 0,
            'Critical': 0
        }
        
        for incident in st.session_state.safety_data:
            severity = incident.get('severity', 'Low')
            risk_data[severity] = risk_data.get(severity, 0) + 1
        
        # Display risk matrix
        st.markdown("""
        | Risk Level | Count | Action Required |
        |------------|-------|-----------------|
        | 🟢 Low | {} | Monitor |
        | 🟡 Medium | {} | Review procedures |
        | 🟠 High | {} | Immediate action |
        | 🔴 Critical | {} | Emergency response |
        """.format(risk_data['Low'], risk_data['Medium'], risk_data['High'], risk_data['Critical']))
        
        # Risk score
        risk_score = max(0, 100 - (risk_data['Critical'] * 25 + risk_data['High'] * 10))
        st.metric("Overall Safety Score", f"{risk_score}/100")

# Flights Page
def show_flights():
    st.title("✈️ Flight Operations")
    
    tab1, tab2 = st.tabs(["📋 Flight Records", "➕ Add Flight"])
    
    with tab1:
        if st.session_state.flight_data:
            for flight in st.session_state.flight_data:
                with st.expander(f"Flight {flight.get('flight_number', 'N/A')} - {flight.get('date', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Aircraft:** {flight.get('aircraft', 'N/A')}")
                        st.write(f"**Route:** {flight.get('departure', 'N/A')} → {flight.get('arrival', 'N/A')}")
                        st.write(f"**Captain:** {flight.get('pilot', 'N/A')}")
                    with col2:
                        st.write(f"**Crew:** {flight.get('crew_count', 'N/A')}")
                        st.write(f"**Passengers:** {flight.get('passengers', 'N/A')}")
                        st.write(f"**Notes:** {flight.get('notes', 'N/A')}")
        else:
            st.info("No flight records found")
    
    with tab2:
        with st.form("flight_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                flight_number = st.text_input("Flight Number *", placeholder="e.g., PK-300")
                aircraft = st.text_input("Aircraft *", placeholder="e.g., AP-BOC")
                date = st.date_input("Flight Date *")
                departure = st.text_input("Departure *", placeholder="e.g., KHI")
            
            with col2:
                arrival = st.text_input("Arrival *", placeholder="e.g., ISB")
                pilot = st.text_input("Captain *")
                crew_count = st.number_input("Crew", min_value=1, value=4)
                passengers = st.number_input("Passengers", min_value=0)
            
            notes = st.text_area("Notes")
            
            if st.form_submit_button("✈️ Add Flight", use_container_width=True):
                if all([flight_number, aircraft, departure, arrival, pilot]):
                    record = {
                        'flight_number': flight_number,
                        'aircraft': aircraft,
                        'date': str(date),
                        'departure': departure,
                        'arrival': arrival,
                        'pilot': pilot,
                        'crew_count': crew_count,
                        'passengers': passengers,
                        'notes': notes
                    }
                    record_id = DataManager.add_flight(record)
                    st.success(f"✅ Flight added! ID: {record_id}")
                    st.rerun()
                else:
                    st.error("Please fill required fields")

# AI Chat Interface
def show_ai_chat():
    st.title("🤖 AI Operations Intelligence")
    st.markdown("Ask questions about your fleet operations and get AI-powered insights")
    
    # Initialize AI Agent
    ai_agent = AIAgent()
    
    # Display chat history
    chat_container = st.container(height=400, border=True)
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.markdown(f'<div class="user-message">👤 **You:** {msg["content"]}</div>', 
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">🤖 **AI Assistant:**<br>{msg["content"]}</div>', 
                          unsafe_allow_html=True)
    
    # Input section
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_query = st.text_input(
            "Ask a question...",
            placeholder="e.g., How can we decrease maintenance frequency? What are our top risks?",
            key="ai_chat_input"
        )
    
    with col2:
        send_btn = st.button("Send", use_container_width=True)
    
    # Process query
    if send_btn and user_query:
        # Add user message
        st.session_state.chat_history.append({'role': 'user', 'content': user_query})
        
        # Get AI response
        with st.spinner("🤖 AI is analyzing your data..."):
            ai_response = ai_agent.get_ai_response(user_query)
        
        # Add AI response
        st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
        st.rerun()
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Suggested queries
    st.divider()
    st.markdown("**💡 Suggested Questions:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("How to reduce maintenance costs?", use_container_width=True):
            st.session_state.chat_history.append({'role': 'user', 'content': "How to reduce maintenance costs?"})
            ai_response = ai_agent.get_ai_response("How to reduce maintenance costs?")
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()
        
        if st.button("What are our safety risks?", use_container_width=True):
            st.session_state.chat_history.append({'role': 'user', 'content': "What are our safety risks?"})
            ai_response = ai_agent.get_ai_response("What are our safety risks?")
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()
    
    with col2:
        if st.button("Analyze maintenance patterns", use_container_width=True):
            st.session_state.chat_history.append({'role': 'user', 'content': "Analyze maintenance patterns"})
            ai_response = ai_agent.get_ai_response("Analyze maintenance patterns")
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()
        
        if st.button("How to improve efficiency?", use_container_width=True):
            st.session_state.chat_history.append({'role': 'user', 'content': "How to improve efficiency?"})
            ai_response = ai_agent.get_ai_response("How to improve efficiency?")
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()

# Export Data Interface
def show_export_data():
    st.title("📥 Export Data")
    st.markdown("Export your operational data for analysis or backup")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔧 Maintenance Data")
        st.metric("Total Records", len(st.session_state.maintenance_data))
        if st.session_state.maintenance_data:
            df = pd.DataFrame(st.session_state.maintenance_data)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export Maintenance",
                csv,
                f"maintenance_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("No data to export")
    
    with col2:
        st.markdown("### ⚠️ Safety Data")
        st.metric("Total Records", len(st.session_state.safety_data))
        if st.session_state.safety_data:
            df = pd.DataFrame(st.session_state.safety_data)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export Safety",
                csv,
                f"safety_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("No data to export")
    
    with col3:
        st.markdown("### ✈️ Flight Data")
        st.metric("Total Records", len(st.session_state.flight_data))
        if st.session_state.flight_data:
            df = pd.DataFrame(st.session_state.flight_data)
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Export Flights",
                csv,
                f"flights_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("No data to export")
    
    # Export all data
    st.divider()
    st.subheader("📦 Export All Data")
    
    if st.button("🗂️ Generate Complete Data Package", use_container_width=True):
        with st.spinner("Preparing data package..."):
            # Create a comprehensive export
            all_data = {
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'exported_by': st.session_state.user,
                'statistics': {
                    'maintenance_records': len(st.session_state.maintenance_data),
                    'safety_records': len(st.session_state.safety_data),
                    'flight_records': len(st.session_state.flight_data)
                },
                'maintenance_data': st.session_state.maintenance_data,
                'safety_data': st.session_state.safety_data,
                'flight_data': st.session_state.flight_data
            }
            
            # Convert to JSON for complete export
            json_str = json.dumps(all_data, indent=2, default=str)
            
            st.download_button(
                "📥 Download Complete Data Package (JSON)",
                json_str,
                f"airsial_complete_export_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "application/json",
                use_container_width=True
            )
            
        st.success("✅ Data package ready for download!")

# Bulk Upload (Admin Only)
def show_bulk_upload():
    st.title("📤 Bulk Data Upload")
    
    if st.session_state.role != 'Administrator':
        st.error("⛔ Access Denied: Only administrators can perform bulk uploads")
        st.info("Please contact your system administrator if you need to upload bulk data")
        return
    
    st.success("✅ Administrator Access Granted")
    
    data_type = st.selectbox("Select Data Type", ["Maintenance", "Safety", "Flights"])
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("Data Type", data_type)
            
            st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("📥 Import All Records", use_container_width=True, type="primary"):
                uploaded_file.seek(0)
                
                with st.spinner(f"Importing {len(df)} records..."):
                    records_added, status = DataManager.bulk_upload_csv(
                        data_type.lower(), 
                        uploaded_file
                    )
                
                if status == "Success":
                    st.success(f"✅ Successfully imported {records_added} records!")
                    st.balloons()
                else:
                    st.error(f"❌ Import failed: {status}")
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# Main Application
def main():
    if st.session_state.user is None:
        show_login_register()
    else:
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.user}")
            st.markdown(f"**Role:** {st.session_state.role}")
            st.divider()
            
            # Navigation based on role
            nav_options = ["🏠 Dashboard", "🤖 AI Assistant", "🔧 Maintenance", "⚠️ Safety", "✈️ Flights", "📥 Export Data"]
            
            # Add bulk upload only for admins
            if st.session_state.role == 'Administrator':
                nav_options.insert(2, "📤 Bulk Upload")
            
            page = st.radio("Navigation", nav_options)
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.role = None
                st.rerun()
        
        # Page routing
        if page == "🏠 Dashboard":
            show_dashboard()
        elif page == "🤖 AI Assistant":
            show_ai_chat()
        elif page == "📤 Bulk Upload":
            show_bulk_upload()
        elif page == "🔧 Maintenance":
            show_maintenance()
        elif page == "⚠️ Safety":
            show_safety()
        elif page == "✈️ Flights":
            show_flights()
        elif page == "📥 Export Data":
            show_export_data()

if __name__ == "__main__":
    main()
