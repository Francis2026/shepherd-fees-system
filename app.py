import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import datetime
import uuid
import io
import hashlib
import plotly.express as px
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import base64
import time

# ========== CRITICAL: Initialize session state ONCE ==========
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.logged_in = False
    st.session_state.firebase_done = False
    st.session_state.login_loaded = False
    st.session_state.navigation_menu = "Dashboard"
    st.session_state.show_archived = False
    st.session_state.username = ""
    st.session_state.role = ""

# ------------------- Page Configuration -------------------
st.set_page_config(
    page_title="Shepherd Academy | Fees Management",
    layout="wide",
    page_icon=":school:",
    initial_sidebar_state="expanded"
)

# ------------------- Modern Color Scheme -------------------
COLORS = {
    "primary": "#1E3A5F",
    "secondary": "#2E5A8A",
    "accent": "#4A90E2",
    "success": "#28A745",
    "warning": "#FFC107",
    "danger": "#DC3545",
    "dark": "#1A1A2E",
    "light": "#F8F9FA",
    "gray": "#6C757D",
    "white": "#FFFFFF"
}

# ------------------- Modern CSS -------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem;
        margin-top: 0rem !important;
    }

    header {
        background: transparent !important;
        padding: 0rem !important;
        height: 0rem !important;
        min-height: 0rem !important;
    }

    header .stDecoration {
        display: none !important;
    }

    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        background-color: #1E3A5F !important;
        border-radius: 0 8px 8px 0 !important;
        padding: 8px 10px !important;
        margin-top: 20px !important;
    }

    [data-testid="stSidebarCollapseButton"] svg {
        fill: white !important;
    }

    .stApp {
        margin-top: 0rem;
        padding-top: 0rem;
    }

    .main > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    section.main > div {
        padding-top: 0rem !important;
    }

    .modern-card {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .modern-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }

    .stButton > button {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8A 100%);
        color: white;
        border-radius: 12px;
        border: none;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 0.9rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(30,58,95,0.3);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%);
        border-right: none;
    }

    [data-testid="stSidebar"] * {
        color: #E8E8E8 !important;
    }

    [data-testid="stSidebar"] .stSelectbox label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }

    [data-testid="stSidebar"] .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }

    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stNumberInput input {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #A8B56C !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #E8E8E8 !important;
    }

    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #E5E7EB;
        padding: 0.6rem 1rem;
    }

    .dataframe {
        border-radius: 16px !important;
        overflow: hidden;
    }
    .dataframe thead tr th {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8A 100%) !important;
        color: white !important;
        padding: 12px !important;
    }

    .streamlit-expanderHeader {
        background: #F8F9FA;
        border-radius: 12px;
        font-weight: 600;
    }

    .badge-success {
        background: #28A745;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-warning {
        background: #FFC107;
        color: #333;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-info {
        background: #17A2B8;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-secondary {
        background: #6C757D;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: #E8E8E8 !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #2E5A8A !important;
    }

    .stButton > button:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #F1F1F1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: #1E3A5F;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #2E5A8A;
    }

    .main-header {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 10px 20px;
        background: white;
        border-radius: 0 0 0 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        position: sticky;
        top: 0;
        z-index: 999;
    }

    .header-content {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .header-logo {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #A8B56C;
    }

    .header-text {
        text-align: right;
    }

    .header-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1E3A5F;
        margin: 0;
    }

    .header-subtitle {
        font-size: 0.7rem;
        color: #6C757D;
        margin: 0;
    }

    .main .block-container {
        padding-top: 0rem !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .stStatusWidget {display: none;}
    [data-testid="stToolbar"] {display: none;}
    a[href*="github"] {display: none !important;}
    .stAppViewerBadge {display: none !important;}
</style>
""", unsafe_allow_html=True)


# ==================== FIREBASE WITH CACHING (FIX FOR QUOTA) ====================

@st.cache_resource
def get_firebase_client():
    """Get Firebase client - cached to prevent multiple initializations"""
    if not firebase_admin._apps:
        try:
            firebase_creds = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
        except:
            if os.path.exists("firebase-key.json"):
                cred = credentials.Certificate("firebase-key.json")
                firebase_admin.initialize_app(cred)
            else:
                st.error("Firebase credentials not found.")
                st.stop()
    return firestore.client()


db = get_firebase_client()


@st.cache_data(ttl=300)
def get_all_users_cached():
    """Get all users - cached for 5 minutes"""
    try:
        users_ref = db.collection("users")
        users = {}
        for doc in users_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            users[doc.id] = data
        return users
    except:
        return {}


@st.cache_data(ttl=60)
def get_all_pupils_cached():
    """Get all active pupils - cached for 1 minute"""
    try:
        pupils_ref = db.collection("pupils").where("active", "==", True)
        pupils = []
        for doc in pupils_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            pupils.append(data)
        return pupils
    except:
        return []


@st.cache_data(ttl=60)
def get_all_pupils_including_archived_cached():
    """Get all pupils including archived - cached for 1 minute"""
    try:
        pupils_ref = db.collection("pupils")
        pupils = []
        for doc in pupils_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            pupils.append(data)
        return pupils
    except:
        return []


@st.cache_data(ttl=60)
def get_archived_pupils_cached():
    """Get archived pupils - cached for 1 minute"""
    try:
        pupils_ref = db.collection("pupils").where("archived", "==", True)
        pupils = []
        for doc in pupils_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            pupils.append(data)
        return pupils
    except:
        return []


@st.cache_data(ttl=60)
def get_pupils_by_class_cached(class_name, include_archived=False):
    """Get pupils by class - cached"""
    try:
        if include_archived:
            pupils_ref = db.collection("pupils").where("class", "==", class_name)
        else:
            pupils_ref = db.collection("pupils").where("class", "==", class_name).where("active", "==", True)
        pupils = []
        for doc in pupils_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            pupils.append(data)
        return pupils
    except:
        return []


@st.cache_data(ttl=60)
def get_previous_term_balance_cached(pupil_id, current_term, current_year):
    """Calculate balance from previous term - cached"""
    term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
    current_order = term_order.get(current_term, 1)

    if current_order == 1:
        prev_year = current_year - 1
        prev_term = "Term 3"
    elif current_order == 2:
        prev_term = "Term 1"
        prev_year = current_year
    else:
        prev_term = "Term 2"
        prev_year = current_year

    try:
        ledger_ref = db.collection("ledgers").document(pupil_id).collection(prev_term)
        payments = ledger_ref.where("year", "==", prev_year).stream()
        payments_list = list(payments)
        if payments_list:
            last_payment = payments_list[-1].to_dict()
            return last_payment.get("balance", 0)
        return 0
    except:
        return 0


@st.cache_data(ttl=60)
def get_ledger_cached(pupil_id, term, year):
    """Get ledger entries - cached"""
    try:
        ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
        all_docs = list(ledger_ref.stream())
        filtered_docs = []
        for doc in all_docs:
            data = doc.to_dict()
            doc_year = data.get("year")
            if doc_year is not None and int(doc_year) == int(year):
                data['id'] = doc.id
                filtered_docs.append(data)
        filtered_docs.sort(key=lambda x: x.get("date", datetime.datetime.min))
        return filtered_docs
    except:
        return []


@st.cache_data(ttl=60)
def get_pupil_details_cached(pupil_id):
    """Get pupil details - cached"""
    try:
        doc = db.collection("pupils").document(pupil_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None
    except:
        return None


# Logo Functions
def get_logo_base64():
    logo_files = ["images.jfif", "school_logo.jpg", "school_logo.png", "logo.jpg", "logo.png"]
    for logo_file in logo_files:
        if os.path.exists(logo_file):
            try:
                with open(logo_file, "rb") as img_file:
                    img_data = img_file.read()
                    if logo_file.endswith('.png'):
                        mime_type = "image/png"
                    else:
                        mime_type = "image/jpeg"
                    return base64.b64encode(img_data).decode(), mime_type
            except:
                continue
    return None, None


def display_main_header():
    logo_base64, mime_type = get_logo_base64()
    if logo_base64:
        st.markdown(f"""
        <div class="main-header">
            <div class="header-content">
                <div class="header-text">
                    <p class="header-title">SHEPHERD ACADEMY BUSIU</p>
                    <p class="header-subtitle">School Fees Management System</p>
                </div>
                <img src="data:{mime_type};base64,{logo_base64}" class="header-logo" height="80", width="80">
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="main-header">
            <div class="header-content">
                <div class="header-text">
                    <p class="header-title">SHEPHERD ACADEMY BUSIU</p>
                    <p class="header-subtitle">School Fees Management System</p>
                </div>
                <div style="width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #A8B56C, #6B7B3A); display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 1.5rem;">🏫</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# User Authentication
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    try:
        users = get_all_users_cached()
        if username in users:
            user_data = users[username]
            stored_password = user_data.get("password", "")
            if stored_password == hash_password(password):
                return user_data.get("role", "admin")
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None


def create_default_users():
    try:
        users_ref = db.collection("users")
        users_list = list(users_ref.stream())
        if len(users_list) == 0:
            bursar_data = {
                "username": "bursar",
                "password": hash_password("bursar123"),
                "role": "bursar",
                "full_name": "School Bursar",
                "created_at": datetime.datetime.now()
            }
            users_ref.document("bursar").set(bursar_data)
            admin_data = {
                "username": "admin",
                "password": hash_password("admin123"),
                "role": "admin",
                "full_name": "School Administrator",
                "created_at": datetime.datetime.now()
            }
            users_ref.document("admin").set(admin_data)
            get_all_users_cached.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Error creating users: {str(e)}")
        return False


# Helper Functions
def generate_receipt_number():
    return f"RCP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"


def generate_pdf_receipt(school_name, logo_path, receipt_num, date_str, child_name, amount, description, balance,
                         previous_balance, term_fees, signature_text, excess_amount=0):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    try:
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 50, height - 80, width=60, height=60, preserveAspectRatio=True)
        else:
            for logo_file in ["logo.png", "images.jfif"]:
                if os.path.exists(logo_file):
                    c.drawImage(logo_file, 50, height - 80, width=60, height=60, preserveAspectRatio=True)
                    break
    except:
        pass

    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.12, 0.23, 0.37)
    c.drawString(120, height - 60, school_name)
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(120, height - 80,
                 "P.O. Box 1400, Busiu - Uganda | Tel: +256779462142 (Director) / +256778615528 (Bursar)")
    c.line(50, height - 90, width - 50, height - 90)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 130, "OFFICIAL RECEIPT")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 160, f"Receipt No: {receipt_num}")
    c.drawString(50, height - 180, f"Date: {date_str}")

    y = height - 220
    c.drawString(50, y, f"Received with thanks from: {child_name}")
    y -= 25
    c.drawString(50, y, f"Amount: UGX {amount:,.0f}")
    y -= 25
    c.drawString(50, y, f"Being payment of: {description}")
    y -= 25
    c.drawString(50, y, f"Previous Balance: UGX {previous_balance:,.0f}")
    y -= 25
    c.drawString(50, y, f"Current Term Fees: UGX {term_fees:,.0f}")
    if excess_amount > 0:
        y -= 25
        c.drawString(50, y, f"Excess Payment: UGX {excess_amount:,.0f} (Carried forward)")
    y -= 25
    c.drawString(50, y, f"New Balance: UGX {balance:,.0f}")

    y -= 60
    c.line(50, y, 200, y)
    c.drawString(50, y - 10, signature_text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def export_to_excel(dataframes_dict, filename):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dataframes_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output


def export_summary_to_pdf(df, title, filename):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=30,
                                 textColor=colors.HexColor('#1E3A5F'))
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 12))

    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A5F')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


class FeesManager:
    def __init__(self):
        self.classes = ["Baby Class", "Middle Class", "Top Class", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
        self.terms = ["Term 1", "Term 2", "Term 3"]
        self.term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
        # REMOVED BURSARY - Only 3 categories now
        self.child_categories = ["Community Child", "Shepherd Child", "Staff Child"]

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
        return get_previous_term_balance_cached(pupil_id, current_term, current_year)

    def enroll_pupil(self, name, class_name, term_fees, child_category="Community Child", sponsor_reason=""):
        try:
            pupil_ref = db.collection("pupils").document()
            pupil_ref.set({
                "name": name,
                "class": class_name,
                "enrollment_date": datetime.datetime.now(),
                "term_fees": term_fees,
                "child_category": child_category,
                "sponsor_reason": sponsor_reason if child_category == "Shepherd Child" else "",
                "active": True,
                "archived": False,
                "leaving_date": None,
                "leaving_reason": None
            })
            # Clear caches after enrollment
            get_all_pupils_cached.clear()
            get_all_pupils_including_archived_cached.clear()
            get_pupils_by_class_cached.clear()
            return pupil_ref.id
        except Exception as e:
            st.error(f"Error enrolling pupil: {str(e)}")
            return None

    def archive_pupil(self, pupil_id, leaving_reason=""):
        try:
            db.collection("pupils").document(pupil_id).update({
                "active": False,
                "archived": True,
                "leaving_date": datetime.datetime.now(),
                "leaving_reason": leaving_reason,
                "archived_at": datetime.datetime.now()
            })
            # Clear caches
            get_all_pupils_cached.clear()
            get_all_pupils_including_archived_cached.clear()
            get_archived_pupils_cached.clear()
            get_pupils_by_class_cached.clear()
            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id):
        try:
            db.collection("pupils").document(pupil_id).update({
                "active": True,
                "archived": False,
                "restored_at": datetime.datetime.now()
            })
            # Clear caches
            get_all_pupils_cached.clear()
            get_all_pupils_including_archived_cached.clear()
            get_archived_pupils_cached.clear()
            get_pupils_by_class_cached.clear()
            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    def get_pupils(self, class_name, include_archived=False):
        return get_pupils_by_class_cached(class_name, include_archived)

    def get_all_pupils(self, include_archived=False):
        if include_archived:
            return get_all_pupils_including_archived_cached()
        return get_all_pupils_cached()

    def get_archived_pupils(self):
        return get_archived_pupils_cached()

    def get_ledger(self, pupil_id, term, year):
        return get_ledger_cached(pupil_id, term, year)

    def get_pupil_details(self, pupil_id):
        return get_pupil_details_cached(pupil_id)

    def update_pupil(self, pupil_id, name, class_name, term_fees, child_category="Community Child", sponsor_reason=""):
        try:
            update_data = {
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "child_category": child_category,
                "updated_at": datetime.datetime.now()
            }
            if child_category == "Shepherd Child":
                update_data["sponsor_reason"] = sponsor_reason
            else:
                update_data["sponsor_reason"] = ""

            db.collection("pupils").document(pupil_id).update(update_data)
            # Clear caches
            get_all_pupils_cached.clear()
            get_all_pupils_including_archived_cached.clear()
            get_pupils_by_class_cached.clear()
            get_pupil_details_cached.clear()
            return True
        except Exception as e:
            st.error(f"Error updating pupil: {str(e)}")
            return False

    def add_payment(self, pupil_id, term, year, amount, description):
        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            pupil = self.get_pupil_details(pupil_id)
            if not pupil:
                return None, "Pupil not found", None, None, 0

            term_fees = pupil.get("term_fees", 0)
            child_category = pupil.get("child_category", "Community Child")

            if child_category == "Shepherd Child":
                term_fees = 0

            year_int = int(year)
            previous_balance = self.get_previous_term_balance(pupil_id, term, year_int)

            payments = ledger_ref.where("year", "==", year_int).stream()
            total_paid_this_term = sum([p.to_dict().get("amount", 0) for p in payments])

            total_due = previous_balance + term_fees
            total_paid = total_paid_this_term + amount
            new_balance = total_due - total_paid

            excess_amount = 0
            if new_balance < 0:
                excess_amount = abs(new_balance)
                new_balance = 0

            transaction_id = str(uuid.uuid4())
            receipt_no = generate_receipt_number()

            ledger_ref.document(transaction_id).set({
                "date": datetime.datetime.now(),
                "amount": amount,
                "description": description,
                "balance": new_balance,
                "previous_balance": previous_balance,
                "term_fees": term_fees,
                "total_due": total_due,
                "year": year_int,
                "receipt_no": receipt_no,
                "excess_amount": excess_amount
            })

            # Clear relevant caches
            get_ledger_cached.clear()
            get_previous_term_balance_cached.clear()

            return transaction_id, new_balance, receipt_no, previous_balance, excess_amount
        except Exception as e:
            st.error(f"Error adding payment: {str(e)}")
            return None, str(e), None, None, 0

    def get_pupil_term_summary(self, pupil_id, term, year):
        pupil_data = self.get_pupil_details(pupil_id)
        if not pupil_data:
            return None, 0, 0, 0, 0, 0, "Community Child", "", False

        term_fees = pupil_data.get("term_fees", 0)
        child_category = pupil_data.get("child_category", "Community Child")
        sponsor_reason = pupil_data.get("sponsor_reason", "")
        is_archived = pupil_data.get("archived", False)

        if child_category == "Shepherd Child":
            term_fees = 0

        previous_balance = self.get_previous_term_balance(pupil_id, term, year)
        payments = db.collection("ledgers").document(pupil_id).collection(term).where("year", "==", year).stream()
        total_paid = sum([p.to_dict().get("amount", 0) for p in payments])

        total_due = previous_balance + term_fees
        balance = max(0, total_due - total_paid)
        credit_balance = previous_balance if previous_balance < 0 else 0

        return pupil_data, term_fees, total_paid, balance, previous_balance, credit_balance, child_category, sponsor_reason, is_archived

    def get_class_summary(self, class_name, term, year, include_archived=False):
        pupils = self.get_pupils(class_name, include_archived)
        summary = []
        cleared_list = []
        not_cleared_list = []
        archived_list = []

        for pupil in pupils:
            pupil_id = pupil.get('id')
            term_fees = pupil.get("term_fees", 0)
            child_category = pupil.get("child_category", "Community Child")
            sponsor_reason = pupil.get("sponsor_reason", "")
            is_archived = pupil.get("archived", False)

            if child_category == "Shepherd Child":
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = db.collection("ledgers").document(pupil_id).collection(term).where("year", "==", year).stream()
            total_paid = sum([p.to_dict().get("amount", 0) for p in payments])

            total_due = previous_balance + term_fees
            balance = max(0, total_due - total_paid)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if child_category == "Shepherd Child":
                    status = "Shepherd Child - Cleared"
                elif child_category == "Staff Child":
                    status = "Staff Child - Cleared"

            pupil_info = {
                "Name": pupil["name"],
                "Child Category": child_category,
                "Previous Balance (UGX)": previous_balance,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if child_category == "Shepherd Child" else "",
                "Leaving Date": pupil.get("leaving_date", "").strftime("%Y-%m-%d") if pupil.get("leaving_date") else "",
                "Leaving Reason": pupil.get("leaving_reason", "")
            }
            summary.append(pupil_info)

            if is_archived:
                archived_list.append(pupil_info)
            elif balance == 0 or child_category in ["Shepherd Child", "Staff Child"]:
                cleared_list.append(pupil_info)
            else:
                not_cleared_list.append(pupil_info)

        df_summary = pd.DataFrame(summary).reset_index(drop=True)
        df_cleared = pd.DataFrame(cleared_list).reset_index(drop=True)
        df_not_cleared = pd.DataFrame(not_cleared_list).reset_index(drop=True)
        df_archived = pd.DataFrame(archived_list).reset_index(drop=True)

        if not df_summary.empty:
            df_summary.insert(0, "No.", range(1, len(df_summary) + 1))
        if not df_cleared.empty:
            df_cleared.insert(0, "No.", range(1, len(df_cleared) + 1))
        if not df_not_cleared.empty:
            df_not_cleared.insert(0, "No.", range(1, len(df_not_cleared) + 1))
        if not df_archived.empty:
            df_archived.insert(0, "No.", range(1, len(df_archived) + 1))

        return df_summary, df_cleared, df_not_cleared, df_archived

    def get_school_wide_summary(self, term, year, include_archived=False):
        pupils = self.get_all_pupils(include_archived)
        all_summaries = []

        for pupil in pupils:
            pupil_id = pupil.get('id')
            term_fees = pupil.get("term_fees", 0)
            child_category = pupil.get("child_category", "Community Child")
            sponsor_reason = pupil.get("sponsor_reason", "")
            is_archived = pupil.get("archived", False)

            if child_category == "Shepherd Child":
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = db.collection("ledgers").document(pupil_id).collection(term).where("year", "==", year).stream()
            total_paid = sum([p.to_dict().get("amount", 0) for p in payments])

            total_due = previous_balance + term_fees
            balance = max(0, total_due - total_paid)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if child_category == "Shepherd Child":
                    status = "Shepherd Child - Cleared"
                elif child_category == "Staff Child":
                    status = "Staff Child - Cleared"

            all_summaries.append({
                "Class": pupil["class"],
                "Name": pupil["name"],
                "Child Category": child_category,
                "Previous Balance (UGX)": previous_balance,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if child_category == "Shepherd Child" else "",
                "Leaving Date": pupil.get("leaving_date", "").strftime("%Y-%m-%d") if pupil.get("leaving_date") else "",
                "Leaving Reason": pupil.get("leaving_reason", "")
            })

        df = pd.DataFrame(all_summaries).reset_index(drop=True)
        if not df.empty:
            df.insert(0, "No.", range(1, len(df) + 1))
        return df


# Login Page
def login_page():
    if not st.session_state.get("login_loaded", False):
        with st.spinner("Loading Shepherd Academy School Fees Management System..."):
            time.sleep(0.5)
        st.session_state.login_loaded = True

    col1, col2, col3 = st.columns([1, 1.3, 1])

    with col2:
        logo_base64, mime_type = get_logo_base64()

        if logo_base64:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: 0px;">
                <img src="data:{mime_type};base64,{logo_base64}" height="180" style="border-radius: 10px;">
                <div>
                    <h3 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h3>
                    <p style="color: #6C757D; margin: 2px 0 0 0; font-size: 0.8rem;">School Fees Management System</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: 0px;">
                <div style="background: linear-gradient(135deg, #1E3A5F, #2E5A8A); border-radius: 10px; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 2rem;">🏫</span>
                </div>
                <div>
                    <h3 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h3>
                    <p style="color: #6C757D; margin: 2px 0 0 0; font-size: 0.8rem;">School Fees Management System</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Create default users if needed
        create_default_users()

        with st.form(key="login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    role = authenticate_user(username, password)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.rerun()
                    else:
                        st.error("Invalid username or password")


# Main App
def main_app():
    display_main_header()

    with st.sidebar:
        role = st.session_state["role"]

        profile_image_path = "jane.jpg"
        if os.path.exists(profile_image_path):
            with open(profile_image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                <img src="data:image/jpeg;base64,{img_data}" 
                     style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #A8B56C; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #A8B56C, #6B7B3A); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
                    <span style="color: white; font-size: 2rem;">👤</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 5px;">
            <p style="font-weight: 600; font-size: 1rem; margin: 0; color: white;">Tukei Christine</p>
        </div>
        """, unsafe_allow_html=True)

        badge_class = "badge-success" if role == "bursar" else "badge-warning"
        st.markdown(f"<div style='text-align: center;'><span class='{badge_class}'>{role.upper()}</span></div>",
                    unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Navigation")

        if role == "bursar":
            nav_options = ["Dashboard", "Enroll Pupil", "Pupils & Ledgers", "Record Payment",
                           "Class Reports", "School Reports", "Manage Pupils", "Archived Pupils"]
        else:
            nav_options = ["Dashboard", "Pupils & Ledgers", "Class Reports", "School Reports"]

        selected_menu = st.radio(
            "Menu",
            nav_options,
            key="nav_radio",
            label_visibility="collapsed"
        )

        st.session_state.navigation_menu = selected_menu
        menu = selected_menu

        st.markdown("---")
        st.markdown("### Period")
        current_term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="global_term")
        current_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.datetime.now().year,
                                       step=1)

        st.markdown("---")

        if role == "bursar" and menu in ["Pupils & Ledgers", "Class Reports", "School Reports"]:
            st.session_state.show_archived = st.checkbox("Show Archived Pupils", value=st.session_state.show_archived)

        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            for key in ["logged_in", "username", "role", "navigation_menu", "show_archived"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    manager = FeesManager()

    # Dashboard
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #1E3A5F; margin-bottom: 1rem;'>Dashboard</h2>", unsafe_allow_html=True)

        all_pupils = manager.get_all_pupils(include_archived=False)
        total_pupils = len(all_pupils)
        total_archived = len(manager.get_archived_pupils())

        # Calculate totals
        total_expected = 0
        total_collected = 0
        total_balance = 0
        community_count = 0
        shepherd_count = 0
        staff_count = 0

        for pupil in all_pupils:
            child_category = pupil.get("child_category", "Community Child")
            term_fees = pupil.get("term_fees", 0)
            if child_category == "Shepherd Child":
                term_fees = 0

            # Count by category
            if child_category == "Community Child":
                community_count += 1
            elif child_category == "Shepherd Child":
                shepherd_count += 1
            elif child_category == "Staff Child":
                staff_count += 1

            total_expected += term_fees

            # Get payments for current term
            pupil_id = pupil.get('id')
            payments = db.collection("ledgers").document(pupil_id).collection(current_term).where("year", "==",
                                                                                                  current_year).stream()
            term_paid = sum([p.to_dict().get("amount", 0) for p in payments])
            total_collected += term_paid

            # Get previous balance
            previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
            total_due = max(0, previous_balance) + term_fees
            balance = max(0, total_due - term_paid)
            total_balance += balance

        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1.5rem;">{total_pupils}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Total Pupils</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1rem;">UGX {total_expected:,.0f}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Total Expected</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1rem;">UGX {total_collected:,.0f}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Total Collected</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #DC3545; margin-bottom: 0; font-size: 1rem;">UGX {total_balance:,.0f}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Not Collected</p>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1.5rem;">{collection_rate:.1f}%</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Collection Rate</p>
            </div>
            """, unsafe_allow_html=True)

        with col6:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1rem;">{staff_count}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Staff Children</p>
            </div>
            """, unsafe_allow_html=True)

        if collection_rate > 0:
            st.progress(collection_rate / 100)

        st.markdown("---")
        st.markdown("<h3>Child Category Summary</h3>", unsafe_allow_html=True)

        cat_col1, cat_col2, cat_col3 = st.columns(3)

        with cat_col1:
            st.markdown(f"""
            <div class="modern-card">
                <h4 style="color: #1E3A5F;">👨‍👩‍👧 Community</h4>
                <p><strong>Count:</strong> {community_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with cat_col2:
            st.markdown(f"""
            <div class="modern-card">
                <h4 style="color: #1E3A5F;">🙏 Shepherd</h4>
                <p><strong>Count:</strong> {shepherd_count}</p>
            </div>
            """, unsafe_allow_html=True)

        with cat_col3:
            st.markdown(f"""
            <div class="modern-card">
                <h4 style="color: #1E3A5F;">👩‍🏫 Staff</h4>
                <p><strong>Count:</strong> {staff_count}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<h3>Quick Actions</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Enroll New Pupil", use_container_width=True):
                st.session_state.navigation_menu = "Enroll Pupil"
                st.rerun()
        with col2:
            if st.button("Record Payment", use_container_width=True):
                st.session_state.navigation_menu = "Record Payment"
                st.rerun()

    # Enroll Pupil
    elif menu == "Enroll Pupil" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Enroll New Pupil</h1>", unsafe_allow_html=True)
        st.info("When you enroll a pupil, you set the fees for EACH TERM.")

        col1, col2 = st.columns(2)
        with col1:
            pupil_name = st.text_input("Full Name *", placeholder="Enter pupil's full name", key="enroll_name")
            pupil_class = st.selectbox("Class *", manager.classes, key="enroll_class")
        with col2:
            child_category = st.selectbox("Child Category *", manager.child_categories, key="enroll_child_category")

            # Show different help text based on category
            if child_category == "Shepherd Child":
                st.info("🙏 Shepherd Child: Fees will be set to UGX 0 automatically.")
                term_fees = 0
                sponsor_reason = st.text_input("Sponsor Reason", value="Shepherd Child", key="sponsor_reason")
            elif child_category == "Staff Child":
                st.info("👩‍🏫 Staff Child: Enter the fees amount (can be 0 if fully covered).")
                term_fees = st.number_input("Fees Per Term (UGX)", min_value=0, step=0, value=0, key="enroll_fees",
                                            placeholder="0")
                sponsor_reason = ""
            else:  # Community Child
                st.info("👨‍👩‍👧 Community Child: Enter the full fees amount.")
                term_fees = st.number_input("Fees Per Term (UGX)", min_value=0, step=0, value=500000, key="enroll_fees",
                                            placeholder="0")
                sponsor_reason = ""

        if st.button("Enroll Pupil", use_container_width=True):
            if pupil_name:
                if child_category == "Shepherd Child":
                    sponsor_reason_val = sponsor_reason if 'sponsor_reason' in locals() else "Shepherd Child"
                    actual_fees = 0
                elif child_category == "Staff Child":
                    sponsor_reason_val = ""
                    actual_fees = term_fees
                else:
                    sponsor_reason_val = ""
                    actual_fees = term_fees

                pupil_id = manager.enroll_pupil(pupil_name, pupil_class, actual_fees, child_category,
                                                sponsor_reason_val)
                if pupil_id:
                    if child_category == "Shepherd Child":
                        st.success(f"✅ {pupil_name} has been successfully enrolled as a SHEPHERD CHILD!")
                    elif child_category == "Staff Child":
                        st.success(f"✅ {pupil_name} has been successfully enrolled as a STAFF CHILD!")
                    else:
                        st.success(f"✅ {pupil_name} has been successfully enrolled as a COMMUNITY CHILD!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Please fill all required fields")

    # Pupils & Ledgers
    elif menu == "Pupils & Ledgers":
        st.markdown("<h1 style='color: #1E3A5F;'>Pupils & Ledgers</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(f"Showing data for **{current_term}, {current_year}** (INCLUDING ARCHIVED PUPILS)")
        else:
            st.info(f"Showing data for **{current_term}, {current_year}** (Active pupils only)")

        col_class, col_search = st.columns([1, 2])
        with col_class:
            selected_class = st.selectbox("Select Class", manager.classes, key="ledger_class")
        with col_search:
            search_term = st.text_input("Search Pupil", placeholder="Type name to search...")

        pupils = manager.get_pupils(selected_class, include_archived=st.session_state.show_archived)
        if search_term:
            pupils = [p for p in pupils if search_term.lower() in p.get("name", "").lower()]

        if not pupils:
            st.info(f"No pupils found in {selected_class}")
        else:
            st.markdown(f"### Found {len(pupils)} pupil(s) in {selected_class}")

            for pupil in pupils:
                pupil_id = pupil.get('id')
                is_archived = pupil.get("archived", False)
                term_fees = pupil.get("term_fees", 0)
                child_category = pupil.get("child_category", "Community Child")
                sponsor_reason = pupil.get("sponsor_reason", "")

                previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                ledger_entries = manager.get_ledger(pupil_id, current_term, current_year)
                total_paid_this_term = sum([p.get("amount", 0) for p in ledger_entries])

                if previous_balance < 0:
                    total_due = term_fees
                    show_credit = True
                    show_carry_over = False
                    carry_over_amount = abs(previous_balance)
                elif previous_balance > 0:
                    total_due = previous_balance + term_fees
                    show_credit = False
                    show_carry_over = True
                    carry_over_amount = previous_balance
                else:
                    total_due = term_fees
                    show_credit = False
                    show_carry_over = False
                    carry_over_amount = 0

                current_balance = max(0, total_due - total_paid_this_term)

                all_transactions = []

                if show_carry_over:
                    term_order = manager.term_order[current_term]
                    if term_order == 1:
                        source_term = f"Term 3, {current_year - 1}"
                    elif term_order == 2:
                        source_term = f"Term 1, {current_year}"
                    else:
                        source_term = f"Term 2, {current_year}"

                    all_transactions.append({
                        "S/No": 0,
                        "Date": f"Balance from {source_term}",
                        "Amount Paid": "UGX 0",
                        "Description": f"Carry-over balance",
                        "Balance After": f"UGX {carry_over_amount:,.0f}",
                        "Receipt No": "N/A"
                    })
                elif show_credit:
                    term_order = manager.term_order[current_term]
                    if term_order == 1:
                        source_term = f"Term 3, {current_year - 1}"
                    elif term_order == 2:
                        source_term = f"Term 1, {current_year}"
                    else:
                        source_term = f"Term 2, {current_year}"

                    all_transactions.append({
                        "S/No": 0,
                        "Date": f"Credit from {source_term}",
                        "Amount Paid": "UGX 0",
                        "Description": f"Credit balance carried forward",
                        "Balance After": f"-UGX {carry_over_amount:,.0f}",
                        "Receipt No": "N/A"
                    })

                for idx, entry in enumerate(ledger_entries, 1):
                    all_transactions.append({
                        "S/No": idx,
                        "Date": entry.get("date").strftime("%Y-%m-%d %H:%M:%S") if entry.get("date") else "",
                        "Amount Paid": f"UGX {entry.get('amount', 0):,.0f}",
                        "Description": entry.get("description", "Payment"),
                        "Balance After": f"UGX {entry.get('balance', 0):,.0f}",
                        "Receipt No": entry.get("receipt_no", "")
                    })

                category_icon = {
                    "Community Child": "👨‍👩‍👧",
                    "Shepherd Child": "🙏",
                    "Staff Child": "👩‍🏫"
                }.get(child_category, "📌")

                if is_archived:
                    expander_title = f"📌 {category_icon} {pupil['name']} — [ARCHIVED - LEFT SCHOOL]"
                elif child_category == "Shepherd Child":
                    expander_title = f"📌 {category_icon} {pupil['name']} — 🎓 SHEPHERD CHILD (No fees)"
                elif child_category == "Staff Child":
                    expander_title = f"📌 {category_icon} {pupil['name']} — 👩‍🏫 STAFF CHILD - Fees: UGX {term_fees:,.0f}"
                else:
                    if show_credit:
                        expander_title = f"📌 {category_icon} {pupil['name']} — 💳 Credit: UGX {carry_over_amount:,.0f} | Term: UGX {term_fees:,.0f} | Balance: UGX {current_balance:,.0f}"
                    elif show_carry_over:
                        expander_title = f"📌 {category_icon} {pupil['name']} — ⚠️ Carry-over: UGX {carry_over_amount:,.0f} | Term: UGX {term_fees:,.0f} | Balance: UGX {current_balance:,.0f}"
                    else:
                        expander_title = f"📌 {category_icon} {pupil['name']} — Term: UGX {term_fees:,.0f} | Paid: UGX {total_paid_this_term:,.0f} | Balance: UGX {current_balance:,.0f}"

                with st.expander(expander_title):
                    if is_archived:
                        st.warning(f"🏁 **This pupil has left the school**")
                        leaving_date = pupil.get('leaving_date')
                        if leaving_date and isinstance(leaving_date, datetime.datetime):
                            st.info(f"Left on: {leaving_date.strftime('%Y-%m-%d')}")
                        st.info(f"Reason: {pupil.get('leaving_reason', 'Not specified')}")

                    if child_category == "Shepherd Child":
                        st.success(f"🎓 **Shepherd Child (Sponsored)** - Reason: {sponsor_reason}")
                    elif child_category == "Staff Child":
                        st.info(f"👩‍🏫 **Staff Child**")

                    if show_carry_over:
                        st.warning(f"⚠️ **Balance brought forward: UGX {carry_over_amount:,.0f}**")
                    elif show_credit:
                        st.success(f"✅ **Credit brought forward: UGX {carry_over_amount:,.0f}**")

                    if all_transactions:
                        df = pd.DataFrame(all_transactions)
                        st.dataframe(df, use_container_width=True)

                        if ledger_entries:
                            st.markdown("---")
                            st.markdown("### 📄 Payment Receipts")

                            for i in range(0, len(ledger_entries), 3):
                                cols = st.columns(3)
                                for j, entry in enumerate(ledger_entries[i:i + 3]):
                                    with cols[j]:
                                        if st.button(f"🖨️ Receipt {entry.get('receipt_no', '')[-12:]}",
                                                     key=f"print_{entry.get('id', '')}"):
                                            pdf_buffer = generate_pdf_receipt(
                                                school_name="Shepherd Academy Busiu",
                                                logo_path="logo.png" if os.path.exists("logo.png") else "",
                                                receipt_num=entry.get('receipt_no', ''),
                                                date_str=entry.get('date').strftime("%Y-%m-%d %H:%M:%S") if entry.get(
                                                    'date') else "",
                                                child_name=pupil['name'],
                                                amount=entry.get('amount', 0),
                                                description=entry.get('description', ''),
                                                balance=entry.get('balance', 0),
                                                previous_balance=entry.get('previous_balance', 0),
                                                term_fees=term_fees,
                                                signature_text="Bursar's Signature",
                                                excess_amount=entry.get('excess_amount', 0)
                                            )
                                            st.download_button("📥 PDF", pdf_buffer,
                                                               f"Receipt_{entry.get('receipt_no', '')}.pdf",
                                                               "application/pdf")

                        csv = df.to_csv(index=False).encode()
                        st.download_button("📥 Download Ledger (CSV)", csv, f"{pupil['name']}_ledger.csv", "text/csv")

                    else:
                        st.info(f"No payments recorded yet for {current_term}, {current_year}")

                    if role == "bursar" and child_category != "Shepherd Child" and not is_archived:
                        st.markdown("---")
                        if st.button(f"💰 Record Payment for {pupil['name']}", key=f"pay_{pupil_id}",
                                     use_container_width=True):
                            st.session_state.navigation_menu = "Record Payment"
                            st.session_state.quick_pay_pupil = pupil_id
                            st.session_state.quick_pay_name = pupil['name']
                            st.rerun()

    # Record Payment
    elif menu == "Record Payment" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Record Payment</h1>", unsafe_allow_html=True)
        st.info(f"Recording payment for **{current_term}, {current_year}**")

        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.warning("No active pupils found. Please enroll pupils first.")
        else:
            st.markdown("### 🔍 Filter Pupils")
            col_filter1, col_filter2 = st.columns([1, 2])

            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_payment_class")

            with col_filter2:
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_payment_pupil")

            pupil_dicts = [p for p in all_pupils]

            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]

            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning(f"No pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(pupil_dicts)} pupil(s)")

                pupil_options = {f"{p['name']} ({p['class']})": p['id'] for p in pupil_dicts}

                if "quick_pay_pupil" in st.session_state:
                    pupil_id = st.session_state.quick_pay_pupil
                    pupil_name = st.session_state.quick_pay_name
                    st.success(f"Selected pupil: **{pupil_name}**")
                    selected_pupil = None
                    for p in pupil_dicts:
                        if p['id'] == pupil_id:
                            selected_pupil = p
                            break
                    if not selected_pupil:
                        st.error("Selected pupil not found in current filter. Please clear filters.")
                        del st.session_state.quick_pay_pupil
                        del st.session_state.quick_pay_name
                        st.rerun()
                else:
                    selected = st.selectbox("Select Pupil", list(pupil_options.keys()), key="payment_pupil")
                    pupil_id = pupil_options[selected]
                    pupil_name = selected.split(" (")[0]
                    selected_pupil = next((p for p in pupil_dicts if p['id'] == pupil_id), None)

                if selected_pupil:
                    pupil_data = selected_pupil
                    term_fees = pupil_data.get("term_fees", 0)
                    child_category = pupil_data.get("child_category", "Community Child")
                    is_archived = pupil_data.get("archived", False)

                    if is_archived:
                        st.error("This pupil has left the school. Cannot record payments for archived pupils.")
                    elif child_category == "Shepherd Child":
                        st.info("This is a Shepherd Child. No payment is required as fees are UGX 0.")
                    else:
                        previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                        payments = db.collection("ledgers").document(pupil_id).collection(current_term).where(
                            "year", "==", current_year).stream()
                        total_paid_this_term = sum([p.to_dict().get("amount", 0) for p in payments])

                        total_due = max(0, previous_balance) + term_fees
                        current_balance = max(0, total_due - total_paid_this_term)

                        st.markdown("### Pupil Information")
                        col1, col2, col3, col4, col5 = st.columns(5)

                        with col1:
                            st.metric("Pupil Name", pupil_name)
                        with col2:
                            st.metric("Class", pupil_data['class'])
                        with col3:
                            st.metric("Category", child_category)
                        with col4:
                            st.metric("Term Fees", f"UGX {term_fees:,.0f}")
                        with col5:
                            st.metric("Due This Term", f"UGX {current_balance:,.0f}")

                        if previous_balance < 0:
                            st.success(f"✅ **Credit Balance from previous term: UGX {abs(previous_balance):,.0f}**")
                        elif previous_balance > 0:
                            st.warning(f"⚠️ **Balance carried forward: UGX {previous_balance:,.0f}**")

                        st.markdown("---")

                        col1, col2 = st.columns(2)
                        with col1:
                            amount_paid = st.number_input("Amount (UGX)", min_value=0, step=0, value=0,
                                                          key="payment_amount", placeholder="0")
                        with col2:
                            description = st.text_input("Description", "Term Fees Payment",
                                                        key="payment_description")

                        if st.button("💸 Process Payment & Generate Receipt", use_container_width=True):
                            if amount_paid <= 0:
                                st.error("Amount must be greater than zero")
                            else:
                                trans_id, new_balance, receipt_no, prev_bal, excess_amount = manager.add_payment(
                                    pupil_id, current_term, current_year, amount_paid, description)
                                if trans_id:
                                    if excess_amount > 0:
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded successfully!")
                                        st.info(
                                            f"💰 Excess payment of UGX {excess_amount:,.0f} has been carried forward as credit!")
                                    else:
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded successfully!")
                                    st.info(f"New balance: UGX {new_balance:,.0f}")

                                    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    pdf_buffer = generate_pdf_receipt(
                                        school_name="Shepherd Academy Busiu",
                                        logo_path="images.jfif" if os.path.exists("images.jfif") else "",
                                        receipt_num=receipt_no,
                                        date_str=date_str,
                                        child_name=pupil_name,
                                        amount=amount_paid,
                                        description=f"{description} - {current_term} {current_year}",
                                        balance=new_balance,
                                        previous_balance=prev_bal,
                                        term_fees=term_fees,
                                        signature_text="Bursar's Signature",
                                        excess_amount=excess_amount
                                    )
                                    st.download_button("🖨️ Download Receipt (PDF)", pdf_buffer,
                                                       f"Receipt_{receipt_no}.pdf", "application/pdf")
                                    st.balloons()

                                    if "quick_pay_pupil" in st.session_state:
                                        del st.session_state.quick_pay_pupil
                                        del st.session_state.quick_pay_name
                                    time.sleep(1)
                                    st.rerun()

    # Class Reports
    elif menu == "Class Reports":
        st.markdown("<h1 style='color: #1E3A5F;'>Class Fee Reports</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(f"Showing data for **{current_term}, {current_year}** (INCLUDING ARCHIVED PUPILS)")
        else:
            st.info(f"Showing data for **{current_term}, {current_year}**")

        col1, col2 = st.columns(2)
        with col1:
            selected_class = st.selectbox("Select Class", manager.classes, key="summary_class")
        with col2:
            report_type = st.radio("View", ["All Pupils", "Cleared Only", "With Balance", "Archived Only"],
                                   horizontal=True)

        if st.button("Generate Report", use_container_width=True):
            df_full, df_cleared, df_not_cleared, df_archived = manager.get_class_summary(selected_class, current_term,
                                                                                         current_year,
                                                                                         include_archived=st.session_state.show_archived)

            if report_type == "All Pupils":
                df_to_show = df_full
                title = f"{selected_class} - Full Summary {current_term} {current_year}"
            elif report_type == "Cleared Only":
                df_to_show = df_cleared
                title = f"{selected_class} - Cleared Pupils"
            elif report_type == "With Balance":
                df_to_show = df_not_cleared
                title = f"{selected_class} - Pupils with Balances"
            else:
                df_to_show = df_archived
                title = f"{selected_class} - Archived Pupils (Left School)"

            if not df_to_show.empty:
                st.dataframe(df_to_show, use_container_width=True)

                if report_type != "Archived Only" and not df_full.empty:
                    # Exclude Shepherd Child from chart
                    chart_data = df_full[~df_full["Child Category"].isin(["Shepherd Child"])]
                    if not chart_data.empty:
                        fig = px.bar(chart_data, x="Name", y=["Total Paid (UGX)", "Balance (UGX)"],
                                     title=f"Fee Overview - {selected_class} ({current_term} {current_year})",
                                     barmode="group", color_discrete_sequence=['#28A745', '#DC3545'])
                        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
                        st.plotly_chart(fig, use_container_width=True)

                    total_expected = df_full[~df_full["Child Category"].isin(["Shepherd Child"])][
                        "Total Due (UGX)"].sum()
                    total_paid = df_full[~df_full["Child Category"].isin(["Shepherd Child"])]["Total Paid (UGX)"].sum()
                    total_balance = df_full[~df_full["Child Category"].isin(["Shepherd Child"])]["Balance (UGX)"].sum()
                    cleared_count = len(df_cleared)
                    not_cleared_count = len(df_not_cleared)
                    archived_count = len(df_archived)

                    community_count = len(df_full[df_full["Child Category"] == "Community Child"])
                    shepherd_count = len(df_full[df_full["Child Category"] == "Shepherd Child"])
                    staff_count = len(df_full[df_full["Child Category"] == "Staff Child"])

                    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

                    with col1:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Total Due</h4>
                            <p style="color: #2E5A8A; margin: 3px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_expected:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Total Paid</h4>
                            <p style="color: #28A745; margin: 3px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_paid:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Total Balance</h4>
                            <p style="color: #DC3545; margin: 3px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_balance:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col4:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Cleared</h4>
                            <p style="color: #28A745; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{cleared_count}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col5:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">With Balance</h4>
                            <p style="color: #DC3545; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{not_cleared_count}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col6:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Community</h4>
                            <p style="color: #1E3A5F; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{community_count}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col7:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Staff/Shepherd</h4>
                            <p style="color: #6C757D; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{staff_count + shepherd_count}</p>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                st.subheader("Export Options")
                col1, col2, col3 = st.columns(3)
                with col1:
                    csv = df_to_show.to_csv(index=False).encode()
                    st.download_button("📊 CSV", csv, f"{selected_class}_{current_term}_{current_year}_report.csv",
                                       "text/csv")
                with col2:
                    excel_data = {"Full Summary": df_full, "Cleared": df_cleared, "With Balance": df_not_cleared,
                                  "Archived": df_archived}
                    st.download_button("📘 Excel", export_to_excel(excel_data, "report.xlsx"),
                                       f"{selected_class}_{current_term}_{current_year}_report.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                with col3:
                    pdf_buffer = export_summary_to_pdf(df_to_show, title, "report.pdf")
                    st.download_button("📄 PDF", pdf_buffer,
                                       f"{selected_class}_{current_term}_{current_year}_report.pdf", "application/pdf")

    # School Reports
    elif menu == "School Reports":
        st.markdown("<h1 style='color: #1E3A5F;'>School-Wide Reports</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(f"Showing data for **{current_term}, {current_year}** (INCLUDING ARCHIVED PUPILS)")
        else:
            st.info(f"Showing data for **{current_term}, {current_year}**")

        st.markdown("### Filter Options")
        col_filter1, col_filter2, col_filter3 = st.columns(3)

        with col_filter1:
            filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes, key="filter_class")
        with col_filter2:
            filter_status = st.selectbox("Filter by Status", ["All", "Cleared", "Not Cleared", "Sponsored", "Archived"],
                                         key="filter_status")
        with col_filter3:
            filter_category = st.selectbox("Filter by Child Category", ["All"] + manager.child_categories,
                                           key="filter_category")
            columns_to_export = st.multiselect("Columns to Export",
                                               ["Class", "Name", "Child Category", "Previous Balance (UGX)",
                                                "Term Fees (UGX)",
                                                "Total Due (UGX)", "Total Paid (UGX)", "Balance (UGX)", "Status",
                                                "Sponsor Reason", "Leaving Date", "Leaving Reason"],
                                               default=["Class", "Name", "Child Category", "Total Due (UGX)",
                                                        "Total Paid (UGX)",
                                                        "Balance (UGX)", "Status"])

        if st.button("Generate School Summary", key="school_summary"):
            df_school = manager.get_school_wide_summary(current_term, current_year,
                                                        include_archived=st.session_state.show_archived)

            if filter_class != "All Classes":
                df_school = df_school[df_school["Class"] == filter_class]
            if filter_status != "All":
                if filter_status == "Sponsored":
                    df_school = df_school[df_school["Status"].str.contains("Sponsored", na=False)]
                elif filter_status == "Archived":
                    df_school = df_school[df_school["Status"] == "Archived (Left School)"]
                else:
                    df_school = df_school[df_school["Status"] == filter_status]
            if filter_category != "All":
                df_school = df_school[df_school["Child Category"] == filter_category]

            if not df_school.empty:
                display_columns = [col for col in columns_to_export if col in df_school.columns]
                if display_columns:
                    st.dataframe(df_school[display_columns], use_container_width=True)
                else:
                    st.dataframe(df_school, use_container_width=True)

                paying_pupils = df_school[~df_school["Child Category"].isin(["Shepherd Child"])]

                total_expected = paying_pupils["Total Due (UGX)"].sum() if not paying_pupils.empty else 0
                total_paid = paying_pupils["Total Paid (UGX)"].sum() if not paying_pupils.empty else 0
                total_balance = paying_pupils["Balance (UGX)"].sum() if not paying_pupils.empty else 0

                cleared = len(df_school[(df_school["Balance (UGX)"] == 0) &
                                        (~df_school["Status"].str.contains("Sponsored|Archived", na=False)) &
                                        (~df_school["Child Category"].isin(["Shepherd Child"]))])
                sponsored = len(df_school[df_school["Status"].str.contains("Sponsored", na=False)])
                not_cleared = len(df_school[(df_school["Balance (UGX)"] > 0) &
                                            (~df_school["Status"].str.contains("Sponsored|Archived", na=False)) &
                                            (~df_school["Child Category"].isin(["Shepherd Child"]))])
                archived = len(df_school[df_school["Status"] == "Archived (Left School)"])

                community_count = len(df_school[df_school["Child Category"] == "Community Child"])
                shepherd_count = len(df_school[df_school["Child Category"] == "Shepherd Child"])
                staff_count = len(df_school[df_school["Child Category"] == "Staff Child"])

                st.markdown("### Summary Statistics")
                col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

                with col1:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Total Due</h4>
                        <p style="color: #2E5A8A; margin: 3px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_expected:,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Total Collected</h4>
                        <p style="color: #28A745; margin: 3px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_paid:,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Total Balance</h4>
                        <p style="color: #DC3545; margin: 3px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_balance:,.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Cleared</h4>
                        <p style="color: #28A745; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{cleared}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col5:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">With Balance</h4>
                        <p style="color: #DC3545; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{not_cleared}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col6:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Community</h4>
                        <p style="color: #1E3A5F; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{community_count}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col7:
                    st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Staff/Shepherd</h4>
                        <p style="color: #6C757D; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{staff_count + shepherd_count}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.info(
                    f"🎓 Shepherd Children: {shepherd_count} | 👩‍🏫 Staff: {staff_count} | 👨‍👩‍👧 Community: {community_count}")

                if total_expected > 0:
                    collection_rate = (total_paid / total_expected * 100)
                    st.progress(collection_rate / 100)
                    st.metric("Collection Rate", f"{collection_rate:.1f}%")

                st.markdown("---")
                st.subheader("Export Options")

                export_df = df_school[columns_to_export] if all(
                    col in df_school.columns for col in columns_to_export) else df_school

                col1, col2 = st.columns(2)
                with col1:
                    csv = export_df.to_csv(index=False).encode()
                    st.download_button("📊 Download Report (CSV)", csv,
                                       f"school_wide_{current_term}_{current_year}.csv", "text/csv")
                with col2:
                    excel_data = {"School Summary": export_df}
                    st.download_button("📘 Download Report (Excel)", export_to_excel(excel_data, "report.xlsx"),
                                       f"school_wide_{current_term}_{current_year}.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.warning("No data available for the selected filters")

    # Manage Pupils
    elif menu == "Manage Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Manage Pupils</h1>", unsafe_allow_html=True)

        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.info("No active pupils found")
        else:
            st.markdown("### 🔍 Filter Pupils")
            col_filter1, col_filter2 = st.columns([1, 2])

            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_manage_class")

            with col_filter2:
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_pupil")

            filtered_pupils = all_pupils
            pupil_dicts = []

            for p in filtered_pupils:
                pupil_dict = p
                pupil_dicts.append(pupil_dict)

            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]

            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning(f"No pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(pupil_dicts)} pupil(s)")

                for idx, pupil in enumerate(pupil_dicts):
                    child_category = pupil.get("child_category", "Community Child")
                    category_icon = {
                        "Community Child": "👨‍👩‍👧",
                        "Shepherd Child": "🙏",
                        "Staff Child": "👩‍🏫"
                    }.get(child_category, "📌")

                    with st.expander(f"📌 {category_icon} {pupil['name']} - {pupil['class']} ({child_category})"):

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            **Current Information:**
                            - **Name:** {pupil['name']}
                            - **Class:** {pupil['class']}
                            - **Child Category:** {child_category}
                            - **Term Fees:** UGX {pupil.get('term_fees', 0):,.0f}
                            - **Sponsor Reason:** {pupil.get('sponsor_reason', 'N/A')}
                            """)

                        with col2:
                            st.markdown("**Payment History Summary:**")
                            total_paid_all = 0
                            for term in ["Term 1", "Term 2", "Term 3"]:
                                payments = db.collection("ledgers").document(pupil['id']).collection(term).stream()
                                term_paid = sum([p.to_dict().get("amount", 0) for p in payments])
                                total_paid_all += term_paid
                                if term_paid > 0:
                                    st.write(f"- {term}: UGX {term_paid:,.0f}")
                            st.write(f"**Total Paid (All Time):** UGX {total_paid_all:,.0f}")

                        st.markdown("---")

                        st.markdown("### ✏️ Edit Pupil Details")
                        with st.form(key=f"edit_form_{pupil['id']}"):
                            new_name = st.text_input("Name", pupil['name'], key=f"name_{pupil['id']}")
                            new_class = st.selectbox("Class", manager.classes,
                                                     index=manager.classes.index(pupil['class']) if pupil[
                                                                                                        'class'] in manager.classes else 0,
                                                     key=f"class_{pupil['id']}")

                            new_child_category = st.selectbox("Child Category", manager.child_categories,
                                                              index=manager.child_categories.index(
                                                                  child_category) if child_category in manager.child_categories else 0,
                                                              key=f"child_category_{pupil['id']}")

                            if new_child_category == "Shepherd Child":
                                new_fees = 0
                                sponsor_reason_edit = st.text_input("Sponsor Reason",
                                                                    value=pupil.get('sponsor_reason', "Shepherd Child"),
                                                                    key=f"reason_{pupil['id']}")
                                st.info("🙏 Shepherd Child: Fees will be set to UGX 0 automatically.")
                            elif new_child_category == "Staff Child":
                                new_fees = st.number_input("Term Fees (UGX)", value=int(pupil.get('term_fees', 0)),
                                                           step=50000, key=f"fees_{pupil['id']}")
                                st.info("👩‍🏫 Staff Child: Enter the fees amount (can be 0 if fully covered).")
                            else:
                                new_fees = st.number_input("Term Fees (UGX)", value=int(pupil.get('term_fees', 0)),
                                                           step=50000, key=f"fees_{pupil['id']}")
                                st.info("👨‍👩‍👧 Community Child: Enter the full fees amount.")

                            col_edit, col_archive = st.columns(2)

                            with col_edit:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    if new_child_category == "Shepherd Child":
                                        sponsor_val = sponsor_reason_edit if 'sponsor_reason_edit' in locals() else "Shepherd Child"
                                        actual_fees = 0
                                    else:
                                        sponsor_val = ""
                                        actual_fees = new_fees
                                    manager.update_pupil(pupil['id'], new_name, new_class, actual_fees,
                                                         new_child_category, sponsor_val)
                                    st.success("✅ Updated successfully!")
                                    st.rerun()

                            with col_archive:
                                st.markdown("### 📦 Archive Pupil")
                                leaving_reason = st.text_area("Reason for leaving",
                                                              placeholder="e.g., Transferred to another school, Completed education, etc.",
                                                              key=f"leaving_{pupil['id']}")
                                if st.form_submit_button("Archive Pupil (Leave School)", use_container_width=True):
                                    if leaving_reason:
                                        if manager.archive_pupil(pupil['id'], leaving_reason):
                                            st.warning(f"✅ {pupil['name']} has been archived.")
                                            st.info(
                                                "They will no longer appear in active lists but historical data remains.")
                                            st.rerun()
                                    else:
                                        st.error("Please provide a reason for leaving")

    # Archived Pupils
    elif menu == "Archived Pupils":
        st.markdown("<h1 style='color: #1E3A5F;'>Archived Pupils (Left School)</h1>", unsafe_allow_html=True)
        st.info(
            "These pupils have left the school. Their historical payment records are preserved for reporting purposes.")

        archived_pupils = manager.get_archived_pupils()

        if not archived_pupils:
            st.info("No archived pupils found.")
        else:
            st.markdown("### 🔍 Filter Archived Pupils")
            col_filter1, col_filter2 = st.columns([1, 2])

            with col_filter1:
                archived_classes = list(set([p.get("class", "") for p in archived_pupils]))
                archived_classes.sort()
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + archived_classes,
                                            key="filter_archived_class")

            with col_filter2:
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_archived_pupil")

            filtered_archived = archived_pupils
            filtered_list = []

            for p in filtered_archived:
                pupil_dict = p

                if filter_class != "All Classes" and pupil_dict.get("class") != filter_class:
                    continue

                if search_term and search_term.lower() not in pupil_dict.get("name", "").lower():
                    continue

                filtered_list.append(pupil_dict)

            if not filtered_list:
                st.warning(f"No archived pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(filtered_list)} archived pupil(s)")

                for pupil in filtered_list:
                    pupil_id = pupil['id']
                    child_category = pupil.get("child_category", "Community Child")
                    category_icon = {
                        "Community Child": "👨‍👩‍👧",
                        "Shepherd Child": "🙏",
                        "Staff Child": "👩‍🏫"
                    }.get(child_category, "📌")

                    with st.expander(
                            f"📌 {category_icon} {pupil['name']} - {pupil['class']} ({child_category}) (Left on {pupil.get('leaving_date', '').strftime('%Y-%m-%d') if pupil.get('leaving_date') else 'Unknown date'})"):

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            **Pupil Information:**
                            - **Name:** {pupil['name']}
                            - **Class:** {pupil['class']}
                            - **Child Category:** {child_category}
                            - **Original Term Fees:** UGX {pupil.get('term_fees', 0):,.0f}
                            - **Leaving Date:** {pupil.get('leaving_date', '').strftime('%Y-%m-%d') if pupil.get('leaving_date') else 'N/A'}
                            - **Leaving Reason:** {pupil.get('leaving_reason', 'Not specified')}
                            """)

                        with col2:
                            st.markdown("**Payment Summary:**")
                            total_paid_all = 0
                            for term in ["Term 1", "Term 2", "Term 3"]:
                                payments = db.collection("ledgers").document(pupil_id).collection(term).stream()
                                term_paid = sum([p.to_dict().get("amount", 0) for p in payments])
                                total_paid_all += term_paid
                                if term_paid > 0:
                                    st.write(f"- {term}: UGX {term_paid:,.0f}")

                            st.write(f"**Total Paid (All Time):** UGX {total_paid_all:,.0f}")

                            total_expected = pupil.get('term_fees', 0) * 3
                            if total_paid_all < total_expected:
                                st.warning(f"⚠️ Outstanding balance: UGX {total_expected - total_paid_all:,.0f}")
                            elif total_paid_all > total_expected:
                                st.success(f"✅ Excess payment: UGX {total_paid_all - total_expected:,.0f}")

                        if role == "bursar":
                            if st.button(f"🔄 Restore Pupil", key=f"restore_{pupil_id}"):
                                if manager.restore_pupil(pupil_id):
                                    st.success(f"✅ {pupil['name']} has been restored to active pupils!")
                                    st.rerun()


def main():
    if not st.session_state.get("logged_in", False):
        login_page()
    else:
        main_app()


if __name__ == "__main__":
    main()