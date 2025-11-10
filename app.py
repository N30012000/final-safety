"""
AirSial Operations Management System - Complete Edition
With AI-powered insights and bulk data management
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

# Initialize Session State (safe version)
defaults = {
    'user': None,
    'role': None,
    'maintenance_data': [],
    'safety_data': [],
    'flight_data': [],
    'chat_history': []
}

for key, default_value in defaults.items():
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] = default_value


# Data Manager with CSV Support
class DataManager:
    @staticmethod
    def add_record(data_type, record):
        record['id'] = str(uuid.uuid4())[:8]
        record['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        record['created_by'] = st.session_state.user
        
        if data_type == 'maintenance':
            st.session_state.maintenance_data.append(record)
        elif data_type == 'safety':
            st.session_state.safety_data.append(record)
        elif data_type == 'flight':
            st.session_state.flight_data.append(record)
        
        return record['id']
    
    @staticmethod
    def bulk_upload_csv(data_type, csv_file):
        """Process and upload CSV data in bulk"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            records_added = 0
            
            # Get current data list
            if data_type == 'maintenance':
                data_list = st.session_state.maintenance_data
            elif data_type == 'safety':
                data_list = st.session_state.safety_data
            elif data_type == 'flight':
                data_list = st.session_state.flight_data
            else:
                return 0, "Invalid data type"
            
            # Process each row
            for _, row in df.iterrows():
                record = row.to_dict()
                record['id'] = str(uuid.uuid4())[:8]
                record['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                record['created_by'] = st.session_state.user
                record['uploaded_via'] = 'CSV Import'
                data_list.append(record)
                records_added += 1
            
            return records_added, "Success"
        
        except Exception as e:
            return 0, str(e)
    
    @staticmethod
    def export_to_csv(data_type):
        """Export data to CSV format"""
        if data_type == 'maintenance':
            data = st.session_state.maintenance_data
        elif data_type == 'safety':
            data = st.session_state.safety_data
        elif data_type == 'flight':
            data = st.session_state.flight_data
        else:
            return None
        
        if data:
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        return None

# AI Agent for Operations Intelligence
class AIAgent:
    def __init__(self):
        self.groq_api_key = st.secrets.get("GROQ_API_KEY", "")
    
    def get_ai_response(self, query):
        """Generate AI response based on operational data"""
        
        # Analyze current data
        context = self._build_context()
        
        # Try Groq API first (if key available)
        if self.groq_api_key:
            response = self._call_groq_api(query, context)
            if response:
                return response
        
        # Try Ollama locally
        response = self._call_ollama(query, context)
        if response:
            return response
        
        # Fallback to rule-based responses
        return self._generate_fallback_response(query, context)
    
    def _build_context(self):
        """Build context from operational data"""
        maint_data = st.session_state.maintenance_data
        safety_data = st.session_state.safety_data
        flight_data = st.session_state.flight_data
        
        # Calculate metrics
        total_maint = len(maint_data)
        pending_maint = len([m for m in maint_data if m.get('status') == 'Pending'])
        completed_maint = len([m for m in maint_data if m.get('status') == 'Completed'])
        
        total_incidents = len(safety_data)
        critical_incidents = len([s for s in safety_data if s.get('severity') in ['Critical', 'High']])
        
        total_flights = len(flight_data)
        
        # Calculate maintenance hours
        total_hours = sum(float(m.get('estimated_hours', 0)) for m in maint_data)
        avg_hours = total_hours / total_maint if total_maint > 0 else 0
        
        # Identify top maintenance types
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
        
        # Parse data
        maint_data = st.session_state.maintenance_data
        safety_data = st.session_state.safety_data
        flight_data = st.session_state.flight_data
        
        if any(word in query_lower for word in ['decrease', 'reduce', 'optimize', 'efficiency']):
            pending = len([m for m in maint_data if m.get('status') == 'Pending'])
            total = len(maint_data)
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
            response += "   - Savings: $200,000 annually\n\n"
            
            response += "3. **Cross-Training Program**\n"
            response += "   - Train 5 additional engineers\n"
            response += "   - Cost: $25,000\n"
            response += "   - Benefit: 35% reduction in turnaround time\n\n"
            
            response += "4. **Parts Inventory Optimization**\n"
            response += "   - Implement JIT inventory system\n"
            response += "   - Reduce parts waiting time by 40%\n"
            response += "   - Annual savings: $150,000\n"
            
            return response
        
        elif any(word in query_lower for word in ['risk', 'safety', 'incident']):
            critical = len([s for s in safety_data if s.get('severity') in ['Critical', 'High']])
            total_incidents = len(safety_data)
            
            response = "**🔍 RISK ASSESSMENT & MITIGATION**\n\n"
            response += f"**Current Risk Profile:**\n"
            response += f"- Total incidents: {total_incidents}\n"
            response += f"- Critical/High severity: {critical}\n"
            response += f"- Risk Score: {max(0, 100 - critical * 10)}/100\n\n"
            
            if critical > 0:
                response += "⚠️ **IMMEDIATE ACTION REQUIRED**\n"
                response += f"- {critical} critical incidents need review\n"
                response += "- Recommend emergency safety meeting\n"
                response += "- Review and update safety protocols\n\n"
            
            response += "**Risk Mitigation Strategy:**\n"
            response += "1. Enhanced crew training on incident procedures\n"
            response += "2. Quarterly safety audits\n"
            response += "3. Implement SMS (Safety Management System)\n"
            response += "4. Real-time incident reporting system\n"
            
            return response
        
        elif 'cost' in query_lower or 'expense' in query_lower or 'budget' in query_lower:
            total_hours = sum(float(m.get('estimated_hours', 0)) for m in maint_data)
            hourly_rate = 150  # Assumed hourly rate
            total_cost = total_hours * hourly_rate
            
            response = "**💰 COST ANALYSIS & REDUCTION**\n\n"
            response += f"**Current Costs:**\n"
            response += f"- Total maintenance hours: {total_hours:.1f}\n"
            response += f"- Estimated labor cost: ${total_cost:,.2f}\n"
            response += f"- Average per task: ${(total_cost/len(maint_data) if maint_data else 0):,.2f}\n\n"
            
            response += "**Cost Reduction Opportunities:**\n"
            response += "1. Negotiate OEM contracts: 15-20% savings\n"
            response += "2. In-house capability development: 30% reduction\n"
            response += "3. Optimize flight schedules: 10% maintenance savings\n"
            response += "4. Bulk parts purchasing: 25% cost reduction\n"
            
            return response
        
        elif 'trend' in query_lower or 'pattern' in query_lower:
            response = "**📈 TREND ANALYSIS**\n\n"
            
            if maint_data:
                # Analyze maintenance trends
                types = {}
                for m in maint_data:
                    mtype = m.get('type', 'Unknown')
                    types[mtype] = types.get(mtype, 0) + 1
                
                response += "**Maintenance Patterns:**\n"
                for mtype, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]:
                    response += f"- {mtype}: {count} occurrences\n"
            
            if safety_data:
                # Analyze safety trends
                severities = {}
                for s in safety_data:
                    sev = s.get('severity', 'Unknown')
                    severities[sev] = severities.get(sev, 0) + 1
                
                response += "\n**Safety Incident Distribution:**\n"
                for sev, count in severities.items():
                    response += f"- {sev}: {count} incidents\n"
            
            response += "\n**Recommendations:**\n"
            response += "- Focus on high-frequency maintenance items\n"
            response += "- Implement preventive measures for recurring issues\n"
            response += "- Monthly trend review meetings\n"
            
            return response
        
        else:
            # General response
            response = "**📊 OPERATIONAL INTELLIGENCE**\n\n"
            response += context + "\n\n"
            response += "**Quick Actions:**\n"
            response += "1. Review pending maintenance tasks\n"
            response += "2. Check critical safety incidents\n"
            response += "3. Analyze maintenance efficiency\n"
            response += "4. Monitor flight operations\n\n"
            response += "Ask me about:\n"
            response += "- How to decrease maintenance frequency\n"
            response += "- Risk assessment and mitigation\n"
            response += "- Cost reduction strategies\n"
            response += "- Trend analysis and patterns\n"
            
            return response

# Authentication
def authenticate(username, password):
    users = {
        'admin': {'password': hashlib.sha256('admin123'.encode()).hexdigest(), 'role': 'Administrator'},
        'manager': {'password': hashlib.sha256('manager123'.encode()).hexdigest(), 'role': 'Manager'},
        'engineer': {'password': hashlib.sha256('engineer123'.encode()).hexdigest(), 'role': 'Engineer'},
        'demo': {'password': hashlib.sha256('demo'.encode()).hexdigest(), 'role': 'Viewer'}
    }
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if username in users and users[username]['password'] == hashed_password:
        return True, users[username]['role']
    return False, None

# Login Page
def show_login():
    st.markdown("# ✈️ AirSial Operations Hub")
    st.markdown("### AI-Powered Fleet Management System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            col_a, col_b = st.columns(2)
            with col_a:
                login_btn = st.form_submit_button("🔓 Login", use_container_width=True)
            with col_b:
                demo_btn = st.form_submit_button("👁️ Demo Mode", use_container_width=True)
            
            if login_btn:
                if username and password:
                    success, role = authenticate(username, password)
                    if success:
                        st.session_state.user = username
                        st.session_state.role = role
                        st.success(f"Welcome {username}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    st.warning("Please enter credentials")
            
            if demo_btn:
                st.session_state.user = 'demo'
                st.session_state.role = 'Viewer'
                st.rerun()
        
        st.info("""
        **Demo Credentials:**
        - Admin: `admin` / `admin123`
        - Manager: `manager` / `manager123`
        - Engineer: `engineer` / `engineer123`
        """)

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

# Bulk Upload Interface
def show_bulk_upload():
    st.title("📤 Bulk Data Upload")
    st.markdown("Upload large CSV files to import data in bulk")
    
    # Select data type
    data_type = st.selectbox(
        "Select Data Type",
        ["Maintenance", "Safety", "Flights"]
    )
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload a CSV file with your data. The system will automatically process and import all records."
    )
    
    if uploaded_file is not None:
        # Preview the data
        st.subheader("📋 Data Preview")
        try:
            df = pd.read_csv(uploaded_file)
            
            # Show statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                st.metric("Data Type", data_type)
            
            # Show preview
            st.dataframe(df.head(10), use_container_width=True)
            
            # Show column information
            with st.expander("📊 Column Information"):
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Type': df.dtypes.astype(str),
                    'Non-Null Count': df.count(),
                    'Unique Values': df.nunique()
                })
                st.dataframe(col_info, use_container_width=True)
            
            # Upload button
            st.divider()
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col2:
                if st.button("📥 Import All Records", use_container_width=True, type="primary"):
                    # Reset file position
                    uploaded_file.seek(0)
                    
                    # Process upload
                    with st.spinner(f"Importing {len(df)} records..."):
                        records_added, status = DataManager.bulk_upload_csv(
                            data_type.lower(), 
                            uploaded_file
                        )
                    
                    if status == "Success":
                        st.success(f"✅ Successfully imported {records_added} records!")
                        st.balloons()
                        
                        # Show summary
                        st.info(f"""
                        **Import Summary:**
                        - Data Type: {data_type}
                        - Records Imported: {records_added}
                        - Import Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                        - Imported By: {st.session_state.user}
                        """)
                    else:
                        st.error(f"❌ Import failed: {status}")
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
            st.info("Please ensure your CSV file is properly formatted")
    
    # Sample CSV templates
    st.divider()
    st.subheader("📝 CSV Templates")
    st.markdown("Download these templates to format your data correctly:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Maintenance template
        maint_template = pd.DataFrame({
            'maintenance_date': ['2025-01-15', '2025-01-20'],
            'aircraft': ['AP-BOC', 'AP-BOD'],
            'type': ['A-Check', 'B-Check'],
            'engineer': ['John Doe', 'Jane Smith'],
            'priority': ['High', 'Medium'],
            'status': ['Pending', 'In Progress'],
            'estimated_hours': [8.0, 12.0],
            'parts_replaced': ['Filter, Oil', 'Brake pads'],
            'notes': ['Routine check', 'Scheduled maintenance']
        })
        csv = maint_template.to_csv(index=False)
        st.download_button(
            "📥 Maintenance Template",
            csv,
            "maintenance_template.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        # Safety template
        safety_template = pd.DataFrame({
            'date': ['2025-01-10', '2025-01-11'],
            'flight': ['PK-300', 'PK-301'],
            'location': ['Karachi', 'Islamabad'],
            'type': ['Bird Strike', 'Technical Failure'],
            'severity': ['Low', 'Medium'],
            'department': ['ground handling', 'security'],
            'description': ['Minor bird strike', 'Hydraulic issue'],
            'reporter': ['Captain Ahmed', 'First Officer Ali'],
            'status': ['open', 'System closed']
        })
        csv = safety_template.to_csv(index=False)
        st.download_button(
            "📥 Safety Template",
            csv,
            "safety_template.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col3:
        # Flight template
        flight_template = pd.DataFrame({
            'date': ['2025-01-15', '2025-01-15'],
            'aircraft': ['AP-BOC', 'AP-BOD'],
            'flight_number': ['PK-300', 'PK-301'],
            'departure': ['KHI', 'ISB'],
            'arrival': ['ISB', 'KHI'],
            'pilot': ['Captain Ahmed', 'Captain Ali'],
            'crew_count': [4, 5],
            'passengers': [150, 180],
            'notes': ['On-time departure,  smooth flight', 'Special meal request for 5 passengers']
        })
        csv = flight_template.to_csv(index=False)
        st.download_button(
            "📥 Flight Template",
            csv,
            "flight_template.csv",
            "text/csv",
            use_container_width=True
        )

# Export Data Interface
def show_export_data():
    st.title("📥 Export Data")
    st.markdown("Export your operational data for analysis or backup")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔧 Maintenance Data")
        st.metric("Total Records", len(st.session_state.maintenance_data))
        if st.session_state.maintenance_data:
            csv = DataManager.export_to_csv('maintenance')
            if csv:
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
            csv = DataManager.export_to_csv('safety')
            if csv:
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
            csv = DataManager.export_to_csv('flight')
            if csv:
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

# Dashboard
def show_dashboard():
    st.title("🏠 Operations Dashboard")
    
    # KPIs
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
    
    # Recent activities and alerts
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

# Main Application
def main():
    if st.session_state.user is None:
        show_login()
    else:
        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"### 👤 {st.session_state.user}")
            st.markdown(f"**Role:** {st.session_state.role}")
            st.divider()
            
            page = st.radio(
                "Navigation",
                [
                    "🏠 Dashboard",
                    "🤖 AI Assistant",
                    "📤 Bulk Upload",
                    "📥 Export Data",
                    "🔧 Maintenance",
                    "⚠️ Safety",
                    "✈️ Flights"
                ]
            )
            
            st.divider()
            
            # Quick Stats
            st.markdown("### 📊 Quick Stats")
            st.metric("Total Operations", 
                     len(st.session_state.maintenance_data) + 
                     len(st.session_state.safety_data) + 
                     len(st.session_state.flight_data))
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                for key in ['user', 'role', 'chat_history']:
                    st.session_state[key] = None
                st.rerun()
        
        # Main content based on navigation
        if page == "🏠 Dashboard":
            show_dashboard()
        elif page == "🤖 AI Assistant":
            show_ai_chat()
        elif page == "📤 Bulk Upload":
            show_bulk_upload()
        elif page == "📥 Export Data":
            show_export_data()
        elif page == "🔧 Maintenance":
            # You can add the maintenance page here
            st.title("🔧 Maintenance Management")
            st.info("Maintenance management interface - Add your implementation here")
        elif page == "⚠️ Safety":
            st.title("⚠️ Safety Management")
            st.info("Safety management interface - Add your implementation here")
        elif page == "✈️ Flights":
            st.title("✈️ Flight Operations")
            st.info("Flight operations interface - Add your implementation here")

if __name__ == "__main__":
    main()