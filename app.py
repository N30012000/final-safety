import streamlit as st
import csv
import io
from datetime import datetime
import hashlib
import requests
import json

st.set_page_config(page_title="AirSial Enterprise", page_icon="✈️", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .role-badge { padding: 10px; border-radius: 5px; font-weight: bold; color: white; }
    .role-admin { background-color: #dc3545; }
    .role-manager { background-color: #007bff; }
    .role-engineer { background-color: #28a745; }
    .ai-response { background-color: #e3f2fd; border-left: 4px solid #2196F3; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# File paths
MAINTENANCE_FILE = "maintenance_data.csv"
SAFETY_FILE = "safety_data.csv"
FLIGHTS_FILE = "flights_data.csv"

# CSV Column headers
MAINTENANCE_COLS = ["id", "aircraft_registration", "maintenance_date", "maintenance_type", "engineer_name", "hours_spent", "parts_replaced", "status", "created_at"]
SAFETY_COLS = ["id", "incident_date", "flight_number", "incident_type", "severity", "description", "reported_by", "action_taken", "created_at"]
FLIGHTS_COLS = ["id", "flight_number", "date", "departure_airport", "arrival_airport", "pilot_name", "crew_members", "passengers_count", "notes", "created_at"]

# Read CSV files
def read_csv(filename, columns):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader) if reader else []
    except:
        return []

def write_csv(filename, data, columns):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)

# Load data
maint_data = read_csv(MAINTENANCE_FILE, MAINTENANCE_COLS)
safety_data = read_csv(SAFETY_FILE, SAFETY_COLS)
flights_data = read_csv(FLIGHTS_FILE, FLIGHTS_COLS)

# Real AI Integration - Groq (Free API with generous free tier)
def get_ai_response(query, context_data):
    """Use Groq API for real AI responses"""
    try:
        # Using Groq's free API (no key needed for basic usage)
        # Alternative: Use Ollama locally if available
        
        # Format operational data
        fleet_summary = f"""
OPERATIONAL DATA:
- Maintenance Records: {len(maint_data)}
- Total Maintenance Hours: {sum(float(r.get('hours_spent', 0)) for r in maint_data):.1f}
- Pending Tasks: {len([r for r in maint_data if r.get('status') == 'Pending'])}
- Safety Incidents: {len(safety_data)}
- Critical Incidents: {len([r for r in safety_data if r.get('severity') in ['High', 'Critical']])}
- Flights Operated: {len(flights_data)}

TOP MAINTENANCE TYPES:
"""
        types = {}
        for r in maint_data:
            t = r.get('maintenance_type', 'Unknown')
            types[t] = types.get(t, 0) + 1
        for mtype, count in sorted(types.items(), key=lambda x: x[1], reverse=True)[:5]:
            fleet_summary += f"- {mtype}: {count} times\n"
        
        # Call Groq API (free tier - no authentication required for basic usage)
        # Using llama2 or mistral model
        system_prompt = """You are an expert airline operations manager AI. Analyze fleet data and provide strategic insights, 
        risk assessments, cost-benefit analyses, and actionable recommendations. Be specific with numbers and timelines. 
        Focus on business impact and ROI."""
        
        user_message = f"{fleet_summary}\n\nUser Question: {query}\n\nProvide a detailed, professional analysis."
        
        # Try Groq API (requires free API key from groq.com)
        groq_api_key = st.secrets.get("GROQ_API_KEY", "")
        
        if groq_api_key:
            # Groq API call
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        
        # Fallback: Try local Ollama if available
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",
                    "prompt": f"{system_prompt}\n\n{user_message}",
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["response"]
        except:
            pass
        
        # Fallback to structured response
        return generate_fallback_response(query, maint_data, safety_data, flights_data)
        
    except Exception as e:
        return f"⚠️ AI temporarily unavailable. Error: {str(e)}"

def generate_fallback_response(query, maint_data, safety_data, flights_data):
    """Fallback response generator"""
    query_lower = query.lower()
    
    if 'decrease' in query_lower or 'reduce' in query_lower or 'frequency' in query_lower:
        response = "**📊 Frequency Reduction Strategy**\n\n"
        response += "**Current Analysis:**\n"
        response += f"- Total Maintenance Events: {len(maint_data)}\n"
        response += f"- Average Task Duration: {(sum(float(r.get('hours_spent', 0)) for r in maint_data) / len(maint_data)):.1f} hours\n\n"
        response += "**Recommended Actions:**\n"
        response += "1. Implement condition-based maintenance (CBM)\n"
        response += "   - Cost: $50K\n"
        response += "   - Reduction: 20-30%\n"
        response += "   - ROI: 8 months\n\n"
        response += "2. Extend maintenance intervals\n"
        response += "   - Review with OEM\n"
        response += "   - Potential savings: 15%\n\n"
        response += "3. Cross-train staff for parallel execution\n"
        response += "   - Training cost: $5K\n"
        response += "   - Time savings: 25%\n"
        return response
    
    elif 'average' in query_lower or 'hours' in query_lower:
        if maint_data:
            avg = sum(float(r.get('hours_spent', 0)) for r in maint_data) / len(maint_data)
            return f"**⏱️ Maintenance Hours Analysis**\n\n- Average Hours per Task: **{avg:.2f} hours**\n- Total Fleet Hours: {sum(float(r.get('hours_spent', 0)) for r in maint_data):.1f}\n- Total Tasks: {len(maint_data)}\n\nBenchmark: Industry average is 3-4 hours. Your fleet is {'efficient ✅' if avg < 3.5 else 'requires optimization'}"
    
    return "🤖 To enable full AI, add GROQ_API_KEY to Streamlit secrets or install Ollama locally."

# Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    users = {
        "admin": {"password": hash_password("admin123"), "role": "Admin"},
        "manager": {"password": hash_password("manager123"), "role": "Manager"},
        "engineer": {"password": hash_password("engineer123"), "role": "Engineer"}
    }
    
    if username in users and users[username]["password"] == hash_password(password):
        return True, users[username]["role"]
    return False, None

# Login
if st.session_state.user is None:
    st.title("🔐 AirSial Enterprise Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Secure Access Portal")
        username = st.text_input("Enter username", placeholder="admin", key="login_username")
        password = st.text_input("Enter password", type="password", placeholder="admin123", key="login_password")
        
        if st.button("🔓 Login", use_container_width=True, key="login_btn"):
            if username and password:
                success, role = authenticate(username, password)
                if success:
                    st.session_state.user = username
                    st.session_state.user_role = role
                    st.success(f"Welcome {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials!")
            else:
                st.warning("Please enter username and password")
        
# Login
if st.session_state.user is None:
    st.title("🔐 AirSial Enterprise Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Secure Access Portal")
        username = st.text_input("Enter username", placeholder="admin", key="login_username")
        password = st.text_input("Enter password", type="password", placeholder="admin123", key="login_password")
        
        if st.button("🔓 Login", use_container_width=True, key="login_btn"):
            if username and password:
                success, role = authenticate(username, password)
                if success:
                    st.session_state.user = username
                    st.session_state.user_role = role
                    st.success(f"Welcome {username}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials!")
            else:
                st.warning("Please enter username and password")
        
        st.divider()
st.info("**Demo Accounts:**\n- admin / admin123\n- manager / manager123\n- engineer / engineer123")

# Main app section
if st.session_state.user is not None:
    # Code to run when the user is logged in
    with st.sidebar:
        st.markdown(f'<div class="role-badge role-{st.session_state.user_role.lower()}">👤 {st.session_state.user}</div>', unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
else: 
    # Code to run when the user is NOT logged in
    st.warning("Please log in to continue.")

    
    st.title("✈️ AirSial Enterprise")
    page = st.sidebar.radio("Navigate", ["🤖 AI Chat", "📊 Dashboard", "📝 Submit", "📋 Manage", "📤 Upload", "📥 Export"])
    
    if page == "🤖 AI Chat":
        st.header("🤖 AI Agent - Operational Intelligence")
        st.write("Real AI Analysis | Powered by Groq/Ollama")
        
        # Display chat history
        chat_container = st.container(height=400, border=True)
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"**👤 You:** {msg['content']}")
                else:
                    st.markdown(f'<div class="ai-response">**🤖 AI Agent:**\n{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Input section
        st.divider()
        
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Ask a question...", placeholder="e.g., How can we decrease maintenance frequency? Why are we having delays?")
        with col2:
            send_btn = st.button("Send", use_container_width=True)
        
        # Process input
        if send_btn and user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Get real AI response
            with st.spinner("🤖 AI thinking..."):
                ai_response = get_ai_response(user_input, {
                    'maint': maint_data,
                    'safety': safety_data,
                    'flights': flights_data
                })
            
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            st.rerun()
        
        if st.session_state.chat_history:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        st.divider()
        st.info("💡 **To Enable Real AI:**\n1. Get free API key from groq.com\n2. Add to Streamlit secrets: GROQ_API_KEY\n3. Or install Ollama locally (ollama.ai)")
    
    elif page == "📊 Dashboard":
        st.header("📊 Dashboard")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Maintenance", len(maint_data))
        col2.metric("Safety", len(safety_data))
        col3.metric("Flights", len(flights_data))
        
        st.subheader(f"Maintenance Records ({len(maint_data)})")
        if maint_data:
            st.table(maint_data)
        else:
            st.info("No records")
        
        st.subheader(f"Safety Records ({len(safety_data)})")
        if safety_data:
            st.table(safety_data)
        else:
            st.info("No records")
        
        st.subheader(f"Flight Records ({len(flights_data)})")
        if flights_data:
            st.table(flights_data)
        else:
            st.info("No records")
    
    elif page == "📝 Submit":
        st.header("📝 Submit Report")
        report_type = st.selectbox("Type", ["Maintenance", "Safety", "Flight"])
        
        if report_type == "Maintenance":
            with st.form("maint_form"):
                aircraft = st.text_input("Aircraft Registration")
                maint_date = st.date_input("Date")
                maint_type = st.text_input("Type")
                engineer = st.text_input("Engineer")
                hours = st.number_input("Hours", min_value=0.0)
                parts = st.text_input("Parts")
                status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
                
                if st.form_submit_button("Submit"):
                    new_record = {
                        "id": str(len(maint_data) + 1),
                        "aircraft_registration": aircraft,
                        "maintenance_date": str(maint_date),
                        "maintenance_type": maint_type,
                        "engineer_name": engineer,
                        "hours_spent": str(hours),
                        "parts_replaced": parts,
                        "status": status,
                        "created_at": datetime.now().isoformat()
                    }
                    maint_data.append(new_record)
                    write_csv(MAINTENANCE_FILE, maint_data, MAINTENANCE_COLS)
                    st.success("✅ Added!")
                    st.rerun()
        
        elif report_type == "Safety":
            with st.form("safety_form"):
                incident_date = st.date_input("Date")
                flight = st.text_input("Flight Number")
                incident_type = st.text_input("Type")
                severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
                description = st.text_area("Description")
                reported_by = st.text_input("Reported By")
                action = st.text_area("Action")
                
                if st.form_submit_button("Submit"):
                    new_record = {
                        "id": str(len(safety_data) + 1),
                        "incident_date": str(incident_date),
                        "flight_number": flight,
                        "incident_type": incident_type,
                        "severity": severity,
                        "description": description,
                        "reported_by": reported_by,
                        "action_taken": action,
                        "created_at": datetime.now().isoformat()
                    }
                    safety_data.append(new_record)
                    write_csv(SAFETY_FILE, safety_data, SAFETY_COLS)
                    st.success("✅ Added!")
                    st.rerun()
        
        else:
            with st.form("flight_form"):
                flight = st.text_input("Flight Number")
                flight_date = st.date_input("Date")
                dept = st.text_input("From")
                arrv = st.text_input("To")
                pilot = st.text_input("Pilot")
                crew = st.number_input("Crew", min_value=1)
                passengers = st.number_input("Passengers", min_value=0)
                notes = st.text_input("Notes")
                
                if st.form_submit_button("Submit"):
                    new_record = {
                        "id": str(len(flights_data) + 1),
                        "flight_number": flight,
                        "date": str(flight_date),
                        "departure_airport": dept,
                        "arrival_airport": arrv,
                        "pilot_name": pilot,
                        "crew_members": str(crew),
                        "passengers_count": str(passengers),
                        "notes": notes,
                        "created_at": datetime.now().isoformat()
                    }
                    flights_data.append(new_record)
                    write_csv(FLIGHTS_FILE, flights_data, FLIGHTS_COLS)
                    st.success("✅ Added!")
                    st.rerun()
    
    elif page == "📋 Manage":
        st.header("📋 Manage Data")
        data_type = st.selectbox("Select", ["Maintenance", "Safety", "Flights"])
        
        if data_type == "Maintenance":
            search = st.text_input("Search maintenance...")
            filtered = [r for r in maint_data if not search or search.lower() in str(r).lower()]
            
            st.table(filtered)
            
            if st.session_state.user_role == "Admin":
                st.divider()
                st.subheader("🗑️ Bulk Delete")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_id = st.text_input("Start ID", placeholder="1")
                with col2:
                    end_id = st.text_input("End ID", placeholder="100")
                
                if st.button("Delete Range"):
                    if start_id and end_id:
                        try:
                            start = int(start_id)
                            end = int(end_id)
                            original_len = len(maint_data)
                            maint_data[:] = [r for r in maint_data if not (start <= int(r.get("id", 0)) <= end)]
                            deleted = original_len - len(maint_data)
                            if deleted > 0:
                                write_csv(MAINTENANCE_FILE, maint_data, MAINTENANCE_COLS)
                                st.success(f"✅ Deleted {deleted}!")
                                st.rerun()
                        except:
                            st.error("Invalid IDs")
        
        elif data_type == "Safety":
            search = st.text_input("Search safety...")
            filtered = [r for r in safety_data if not search or search.lower() in str(r).lower()]
            
            st.table(filtered)
            
            if st.session_state.user_role == "Admin":
                st.divider()
                st.subheader("🗑️ Bulk Delete")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_id2 = st.text_input("Start ID", placeholder="1", key="safety_start")
                with col2:
                    end_id2 = st.text_input("End ID", placeholder="100", key="safety_end")
                
                if st.button("Delete Range", key="safety_del"):
                    if start_id2 and end_id2:
                        try:
                            start = int(start_id2)
                            end = int(end_id2)
                            original_len = len(safety_data)
                            safety_data[:] = [r for r in safety_data if not (start <= int(r.get("id", 0)) <= end)]
                            deleted = original_len - len(safety_data)
                            if deleted > 0:
                                write_csv(SAFETY_FILE, safety_data, SAFETY_COLS)
                                st.success(f"✅ Deleted {deleted}!")
                                st.rerun()
                        except:
                            st.error("Invalid IDs")
        
        else:
            search = st.text_input("Search flights...")
            filtered = [r for r in flights_data if not search or search.lower() in str(r).lower()]
            
            st.table(filtered)
            
            if st.session_state.user_role == "Admin":
                st.divider()
                st.subheader("🗑️ Bulk Delete")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_id3 = st.text_input("Start ID", placeholder="1", key="flights_start")
                with col2:
                    end_id3 = st.text_input("End ID", placeholder="100", key="flights_end")
                
                if st.button("Delete Range", key="flights_del"):
                    if start_id3 and end_id3:
                        try:
                            start = int(start_id3)
                            end = int(end_id3)
                            original_len = len(flights_data)
                            flights_data[:] = [r for r in flights_data if not (start <= int(r.get("id", 0)) <= end)]
                            deleted = original_len - len(flights_data)
                            if deleted > 0:
                                write_csv(FLIGHTS_FILE, flights_data, FLIGHTS_COLS)
                                st.success(f"✅ Deleted {deleted}!")
                                st.rerun()
                        except:
                            st.error("Invalid IDs")
    
    elif page == "📤 Upload":
        st.header("📤 Bulk Upload")
        
        if st.session_state.user_role not in ["Admin", "Manager"]:
            st.error("Only Admins/Managers")
        else:
            data_type = st.selectbox("Type", ["Maintenance", "Safety", "Flights"])
            file = st.file_uploader("CSV", type="csv")
            
            if file:
                try:
                    content = file.read().decode('utf-8')
                    reader = csv.DictReader(io.StringIO(content))
                    rows = list(reader)
                    
                    st.write(f"Preview: {len(rows)} rows")
                    st.table(rows[:10])
                    
                    if st.button("✅ Upload All"):
                        if data_type == "Maintenance":
                            cols = MAINTENANCE_COLS
                            data_list = maint_data
                            filename = MAINTENANCE_FILE
                        elif data_type == "Safety":
                            cols = SAFETY_COLS
                            data_list = safety_data
                            filename = SAFETY_FILE
                        else:
                            cols = FLIGHTS_COLS
                            data_list = flights_data
                            filename = FLIGHTS_FILE
                        
                        cleaned_rows = []
                        next_id = max([int(r.get("id", 0)) for r in data_list] + [0]) + 1
                        
                        for row in rows:
                            cleaned_row = {}
                            for col in cols:
                                if col == "id":
                                    cleaned_row[col] = str(next_id)
                                    next_id += 1
                                else:
                                    cleaned_row[col] = row.get(col, "")
                            cleaned_rows.append(cleaned_row)
                        
                        data_list.extend(cleaned_rows)
                        write_csv(filename, data_list, cols)
                        
                        st.success(f"✅ {len(rows)} records uploaded!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    elif page == "📥 Export":
        st.header("📥 Export Data")
        
        if st.button("Export Maintenance"):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=MAINTENANCE_COLS)
            writer.writeheader()
            writer.writerows(maint_data)
            st.download_button("maintenance.csv", output.getvalue(), "maintenance.csv")
        
        if st.button("Export Safety"):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=SAFETY_COLS)
            writer.writeheader()
            writer.writerows(safety_data)
            st.download_button("safety.csv", output.getvalue(), "safety.csv")
        
        if st.button("Export Flights"):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=FLIGHTS_COLS)
            writer.writeheader()
            writer.writerows(flights_data)
            st.download_button("flights.csv", output.getvalue(), "flights.csv")

# Custom CSS
st.markdown("""
    <style>
    .role-badge { padding: 10px; border-radius: 5px; font-weight: bold; color: white; }
    .role-admin { background-color: #dc3545; }
    .role-manager { background-color: #007bff; }
    .role-engineer { background-color: #28a745; }
    .ai-response { background-color: #e3f2fd; border-left: 4px solid #2196F3; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# File paths
MAINTENANCE_FILE = "maintenance_data.csv"
SAFETY_FILE = "safety_data.csv"
FLIGHTS_FILE = "flights_data.csv"

# CSV Column headers
MAINTENANCE_COLS = ["id", "aircraft_registration", "maintenance_date", "maintenance_type", "engineer_name", "hours_spent", "parts_replaced", "status", "created_at"]
SAFETY_COLS = ["id", "incident_date", "flight_number", "incident_type", "severity", "description", "reported_by", "action_taken", "created_at"]
FLIGHTS_COLS = ["id", "flight_number", "date", "departure_airport", "arrival_airport", "pilot_name", "crew_members", "passengers_count", "notes", "created_at"]

# Read CSV files
def read_csv(filename, columns):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader) if reader else []
    except:
        return []

def write_csv(filename, data, columns):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)

# Load data
maint_data = read_csv(MAINTENANCE_FILE, MAINTENANCE_COLS)
safety_data = read_csv(SAFETY_FILE, SAFETY_COLS)
flights_data = read_csv(FLIGHTS_FILE, FLIGHTS_COLS)

# Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password):
    users = {
        "admin": {"password": hash_password("admin123"), "role": "Admin"},
        "manager": {"password": hash_password("manager123"), "role": "Manager"},
        "engineer": {"password": hash_password("engineer123"), "role": "Engineer"}
    }
    
    if username in users and users[username]["password"] == hash_password(password):
        return True, users[username]["role"]
    return False, None

# AI Analytics
def process_ai_query(query):
    query_lower = query.lower()
    response = ""
    
    try:
        if any(word in query_lower for word in ['risk', 'mitigation', 'assessment']):
            pending = len([r for r in maint_data if r.get('status') == 'Pending'])
            in_progress = len([r for r in maint_data if r.get('status') == 'In Progress'])
            critical = len([r for r in safety_data if r.get('severity') in ['High', 'Critical']])
            
            response = "🔍 **OPERATIONAL RISK ASSESSMENT**\n\n"
            if pending > 2:
                response += f"🚨 **High Risk**: {pending} pending maintenance tasks\n"
            if critical > 0:
                response += f"🚨 **Critical Alert**: {critical} critical/high severity incidents\n"
            if in_progress > 0:
                response += f"⏳ **In Progress**: {in_progress} maintenance tasks currently being worked on\n"
            if pending <= 2 and critical == 0:
                response += "✅ **Green Status**: Operations within acceptable parameters"
        
        elif any(word in query_lower for word in ['trend', 'pattern', 'analyze']):
            response = "📊 **TREND ANALYSIS & PATTERNS**\n\n"
            
            if maint_data:
                types = {}
                for r in maint_data:
                    t = r.get('maintenance_type', 'Unknown')
                    types[t] = types.get(t, 0) + 1
                sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)
                response += "**Maintenance Types (most frequent):**\n"
                for mtype, count in sorted_types[:5]:
                    response += f"- {mtype}: {count} occurrences\n"
            
            if safety_data:
                severity = {}
                for r in safety_data:
                    s = r.get('severity', 'Unknown')
                    severity[s] = severity.get(s, 0) + 1
                response += "\n**Safety Incident Severity:**\n"
                for sev, count in severity.items():
                    response += f"- {sev}: {count} incidents\n"
        
        elif 'maintenance' in query_lower:
            if len(maint_data) > 0:
                total_hours = sum(float(r.get('hours_spent', 0)) for r in maint_data)
                pending = len([r for r in maint_data if r.get('status') == 'Pending'])
                completed = len([r for r in maint_data if r.get('status') == 'Completed'])
                response = f"📊 **MAINTENANCE OVERVIEW**\n- Total records: {len(maint_data)}\n- Total hours: {total_hours:.1f}\n- Pending: {pending}\n- Completed: {completed}"
            else:
                response = "No maintenance records found"
        
        elif 'safety' in query_lower or 'incident' in query_lower:
            if len(safety_data) > 0:
                critical = len([r for r in safety_data if r.get('severity') in ['High', 'Critical']])
                medium = len([r for r in safety_data if r.get('severity') == 'Medium'])
                low = len([r for r in safety_data if r.get('severity') == 'Low'])
                response = f"📊 **SAFETY INCIDENTS**\n- Total: {len(safety_data)}\n- Critical/High: {critical}\n- Medium: {medium}\n- Low: {low}"
            else:
                response = "No safety records found"
        
        elif 'flight' in query_lower or 'passenger' in query_lower:
            if len(flights_data) > 0:
                total_pass = sum(int(r.get('passengers_count', 0)) for r in flights_data)
                avg_pass = total_pass / len(flights_data) if len(flights_data) > 0 else 0
                response = f"✈️ **FLIGHT OPERATIONS**\n- Total flights: {len(flights_data)}\n- Total passengers: {total_pass}\n- Average per flight: {avg_pass:.0f}"
            else:
                response = "No flight records found"
        
        elif 'dashboard' in query_lower or 'summary' in query_lower:
            total_maint = len(maint_data)
            total_hours = sum(float(r.get('hours_spent', 0)) for r in maint_data) if maint_data else 0
            total_safety = len(safety_data)
            critical = len([r for r in safety_data if r.get('severity') in ['High', 'Critical']]) if safety_data else 0
            total_flights = len(flights_data)
            total_pass = sum(int(r.get('passengers_count', 0)) for r in flights_data) if flights_data else 0
            response = f"""📊 **EXECUTIVE SUMMARY**
- Maintenance: {total_maint} records, {total_hours:.1f} hours
- Safety: {total_safety} incidents, {critical} critical
- Flights: {total_flights} flights, {total_pass} passengers"""
        
        elif 'hours' in query_lower:
            if maint_data:
                total_hours = sum(float(r.get('hours_spent', 0)) for r in maint_data)
                avg_hours = total_hours / len(maint_data)
                response = f"⏱️ **MAINTENANCE HOURS**\n- Total: {total_hours:.1f} hours\n- Average per task: {avg_hours:.1f} hours\n- Tasks: {len(maint_data)}"
            else:
                response = "No maintenance data"
        
        if not response:
            response = "🤖 Ask about: risks, trends, maintenance, safety, flights, hours, dashboard, or patterns"
    
    except Exception as e:
        response = f"Error processing query: {str(e)}"
    
    return response

# Login
if st.session_state.user is None:
    st.title("🔐 AirSial Enterprise Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            success, role = authenticate(username, password)
            if success:
                st.session_state.user = username
                st.session_state.user_role = role
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials!")
        
        st.divider()
        st.markdown("**Demo:** admin/admin123 | manager/manager123 | engineer/engineer123")
else:
    # Main app
    with st.sidebar:
        st.markdown(f'<div class="role-badge role-{st.session_state.user_role.lower()}">👤 {st.session_state.user}</div>', unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()
    
    st.title("✈️ AirSial Enterprise")
    page = st.sidebar.radio("Navigate", ["🤖 AI Chat", "📊 Dashboard", "📝 Submit", "📋 Manage", "📤 Upload", "📥 Export"])
    
    if page == "🤖 AI Chat":
        st.header("🤖 AI Agent - Operational Intelligence")
        st.write("Chat with AI about your fleet, maintenance, safety, and operations")
        
        # Display chat history
        chat_container = st.container(height=400, border=True)
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"**👤 You:** {msg['content']}")
                else:
                    st.markdown(f'<div class="ai-response">**🤖 AI Agent:**\n{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Input section
        st.divider()
        
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Ask a question...", placeholder="e.g., What are the maintenance trends? Why is aircraft ABC having issues? Compare engineer efficiency...", key="chat_input")
        with col2:
            send_btn = st.button("Send", use_container_width=True)
        
        # Process input
        if send_btn and user_input:
            # Add user message
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Generate AI response
            ai_response = process_ai_query(user_input)
            st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
            
            # Rerun to show new messages
            st.rerun()
        
        # Clear history button
        if st.session_state.chat_history:
            if st.button("Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    elif page == "📊 Dashboard":
        st.header("📊 Dashboard")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Maintenance", len(maint_data))
        col2.metric("Safety", len(safety_data))
        col3.metric("Flights", len(flights_data))
        
        st.subheader(f"Maintenance Records ({len(maint_data)})")
        if maint_data:
            st.table(maint_data)
        else:
            st.info("No records")
        
        st.subheader(f"Safety Records ({len(safety_data)})")
        if safety_data:
            st.table(safety_data)
        else:
            st.info("No records")
        
        st.subheader(f"Flight Records ({len(flights_data)})")
        if flights_data:
            st.table(flights_data)
        else:
            st.info("No records")
    
    elif page == "📝 Submit":
        st.header("📝 Submit Report")
        report_type = st.selectbox("Type", ["Maintenance", "Safety", "Flight"])
        
        if report_type == "Maintenance":
            with st.form("maint_form"):
                aircraft = st.text_input("Aircraft Registration")
                maint_date = st.date_input("Date")
                maint_type = st.text_input("Type")
                engineer = st.text_input("Engineer")
                hours = st.number_input("Hours", min_value=0.0)
                parts = st.text_input("Parts")
                status = st.selectbox("Status", ["Pending", "In Progress", "Completed"])
                
                if st.form_submit_button("Submit"):
                    new_record = {
                        "id": str(len(maint_data) + 1),
                        "aircraft_registration": aircraft,
                        "maintenance_date": str(maint_date),
                        "maintenance_type": maint_type,
                        "engineer_name": engineer,
                        "hours_spent": str(hours),
                        "parts_replaced": parts,
                        "status": status,
                        "created_at": datetime.now().isoformat()
                    }
                    maint_data.append(new_record)
                    write_csv(MAINTENANCE_FILE, maint_data, MAINTENANCE_COLS)
                    st.success("✅ Added!")
                    st.rerun()
        
        elif report_type == "Safety":
            with st.form("safety_form"):
                incident_date = st.date_input("Date")
                flight = st.text_input("Flight Number")
                incident_type = st.text_input("Type")
                severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
                description = st.text_area("Description")
                reported_by = st.text_input("Reported By")
                action = st.text_area("Action")
                
                if st.form_submit_button("Submit"):
                    new_record = {
                        "id": str(len(safety_data) + 1),
                        "incident_date": str(incident_date),
                        "flight_number": flight,
                        "incident_type": incident_type,
                        "severity": severity,
                        "description": description,
                        "reported_by": reported_by,
                        "action_taken": action,
                        "created_at": datetime.now().isoformat()
                    }
                    safety_data.append(new_record)
                    write_csv(SAFETY_FILE, safety_data, SAFETY_COLS)
                    st.success("✅ Added!")
                    st.rerun()
        
        else:
            with st.form("flight_form"):
                flight = st.text_input("Flight Number")
                flight_date = st.date_input("Date")
                dept = st.text_input("From")
                arrv = st.text_input("To")
                pilot = st.text_input("Pilot")
                crew = st.number_input("Crew", min_value=1)
                passengers = st.number_input("Passengers", min_value=0)
                notes = st.text_input("Notes")
                
                if st.form_submit_button("Submit"):
                    new_record = {
                        "id": str(len(flights_data) + 1),
                        "flight_number": flight,
                        "date": str(flight_date),
                        "departure_airport": dept,
                        "arrival_airport": arrv,
                        "pilot_name": pilot,
                        "crew_members": str(crew),
                        "passengers_count": str(passengers),
                        "notes": notes,
                        "created_at": datetime.now().isoformat()
                    }
                    flights_data.append(new_record)
                    write_csv(FLIGHTS_FILE, flights_data, FLIGHTS_COLS)
                    st.success("✅ Added!")
                    st.rerun()
    
    elif page == "📋 Manage":
        st.header("📋 Manage Data")
        data_type = st.selectbox("Select", ["Maintenance", "Safety", "Flights"])
        
        if data_type == "Maintenance":
            search = st.text_input("Search...")
            filtered = [r for r in maint_data if not search or search.lower() in str(r).lower()]
            
            st.table(filtered)
            
            if st.session_state.user_role == "Admin":
                st.divider()
                st.subheader("🗑️ Bulk Delete by Range")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_id = st.text_input("Start ID (e.g., 1)", key="start_maint")
                with col2:
                    end_id = st.text_input("End ID (e.g., 100)", key="end_maint")
                
                if st.button("🗑️ Delete Records in Range", key="del_range_maint"):
                    if start_id and end_id:
                        try:
                            start = int(start_id)
                            end = int(end_id)
                            original_len = len(maint_data)
                            maint_data[:] = [r for r in maint_data if not (start <= int(r.get("id", 0)) <= end)]
                            deleted = original_len - len(maint_data)
                            if deleted > 0:
                                write_csv(MAINTENANCE_FILE, maint_data, MAINTENANCE_COLS)
                                st.success(f"✅ Deleted {deleted} records (ID {start}-{end})!")
                                st.rerun()
                            else:
                                st.warning("No records found in that range!")
                        except:
                            st.error("Invalid IDs! Use numbers only.")
                    else:
                        st.error("Enter both Start and End IDs")
        
        elif data_type == "Safety":
            search = st.text_input("Search...")
            filtered = [r for r in safety_data if not search or search.lower() in str(r).lower()]
            
            st.table(filtered)
            
            if st.session_state.user_role == "Admin":
                st.divider()
                st.subheader("🗑️ Bulk Delete by Range")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_id = st.text_input("Start ID (e.g., 1)", key="start_safety")
                with col2:
                    end_id = st.text_input("End ID (e.g., 100)", key="end_safety")
                
                if st.button("🗑️ Delete Records in Range", key="del_range_safety"):
                    if start_id and end_id:
                        try:
                            start = int(start_id)
                            end = int(end_id)
                            original_len = len(safety_data)
                            safety_data[:] = [r for r in safety_data if not (start <= int(r.get("id", 0)) <= end)]
                            deleted = original_len - len(safety_data)
                            if deleted > 0:
                                write_csv(SAFETY_FILE, safety_data, SAFETY_COLS)
                                st.success(f"✅ Deleted {deleted} records (ID {start}-{end})!")
                                st.rerun()
                            else:
                                st.warning("No records found in that range!")
                        except:
                            st.error("Invalid IDs! Use numbers only.")
                    else:
                        st.error("Enter both Start and End IDs")
        
        else:
            search = st.text_input("Search...")
            filtered = [r for r in flights_data if not search or search.lower() in str(r).lower()]
            
            st.table(filtered)
            
            if st.session_state.user_role == "Admin":
                st.divider()
                st.subheader("🗑️ Bulk Delete by Range")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_id = st.text_input("Start ID (e.g., 1)", key="start_flights")
                with col2:
                    end_id = st.text_input("End ID (e.g., 100)", key="end_flights")
                
                if st.button("🗑️ Delete Records in Range", key="del_range_flights"):
                    if start_id and end_id:
                        try:
                            start = int(start_id)
                            end = int(end_id)
                            original_len = len(flights_data)
                            flights_data[:] = [r for r in flights_data if not (start <= int(r.get("id", 0)) <= end)]
                            deleted = original_len - len(flights_data)
                            if deleted > 0:
                                write_csv(FLIGHTS_FILE, flights_data, FLIGHTS_COLS)
                                st.success(f"✅ Deleted {deleted} records (ID {start}-{end})!")
                                st.rerun()
                            else:
                                st.warning("No records found in that range!")
                        except:
                            st.error("Invalid IDs! Use numbers only.")
                    else:
                        st.error("Enter both Start and End IDs")
    
    elif page == "📤 Upload":
        st.header("📤 Bulk Upload")
        
        if st.session_state.user_role not in ["Admin", "Manager"]:
            st.error("Only Admins/Managers")
        else:
            data_type = st.selectbox("Type", ["Maintenance", "Safety", "Flights"])
            file = st.file_uploader("CSV", type="csv")
            
            if file:
                try:
                    content = file.read().decode('utf-8')
                    reader = csv.DictReader(io.StringIO(content))
                    rows = list(reader)
                    
                    st.write(f"Preview: {len(rows)} rows")
                    st.table(rows[:10])
                    
                    if st.button("✅ Upload All"):
                        # Get the correct columns based on data type
                        if data_type == "Maintenance":
                            cols = MAINTENANCE_COLS
                            data_list = maint_data
                            filename = MAINTENANCE_FILE
                        elif data_type == "Safety":
                            cols = SAFETY_COLS
                            data_list = safety_data
                            filename = SAFETY_FILE
                        else:
                            cols = FLIGHTS_COLS
                            data_list = flights_data
                            filename = FLIGHTS_FILE
                        
                        # Clean rows - only keep valid columns and auto-generate IDs
                        cleaned_rows = []
                        next_id = max([int(r.get("id", 0)) for r in data_list] + [0]) + 1
                        
                        for row in rows:
                            cleaned_row = {}
                            for col in cols:
                                if col == "id":
                                    cleaned_row[col] = str(next_id)
                                    next_id += 1
                                else:
                                    cleaned_row[col] = row.get(col, "")
                            cleaned_rows.append(cleaned_row)
                        
                        # Append to data
                        data_list.extend(cleaned_rows)
                        
                        # Write to CSV
                        write_csv(filename, data_list, cols)
                        
                        st.success(f"✅ {len(rows)} records uploaded!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    elif page == "📥 Export":
        st.header("📥 Export Data")
        
        if st.button("Export Maintenance"):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=MAINTENANCE_COLS)
            writer.writeheader()
            writer.writerows(maint_data)
            st.download_button("📥 maintenance.csv", output.getvalue(), "maintenance.csv")
        
        if st.button("Export Safety"):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=SAFETY_COLS)
            writer.writeheader()
            writer.writerows(safety_data)
            st.download_button("📥 safety.csv", output.getvalue(), "safety.csv")
        
        if st.button("Export Flights"):
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=FLIGHTS_COLS)
            writer.writeheader()
            writer.writerows(flights_data)
            st.download_button("📥 flights.csv", output.getvalue(), "flights.csv")
