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
from datetime import timedelta
import json

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
    "white": "#FFFFFF",
    "staff": "#17A2B8",
    "shepherd": "#20B2AA",
    "community": "#6C757D"
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
        padding: 1rem;
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
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 0.85rem;
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

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }

    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div,
    [data-testid="stSidebar"] .stNumberInput input {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #A8B56C !important;
        font-size: 1rem !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #E8E8E8 !important;
    }

    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #E5E7EB;
        padding: 0.5rem 1rem;
    }

    .dataframe {
        border-radius: 16px !important;
        overflow: hidden;
    }
    .dataframe thead tr th {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8A 100%) !important;
        color: white !important;
        padding: 10px !important;
        font-size: 0.8rem !important;
    }

    .streamlit-expanderHeader {
        background: #F8F9FA;
        border-radius: 12px;
        font-weight: 600;
    }

    .badge-success, .badge-warning, .badge-info, .badge-secondary,
    .badge-staff, .badge-shepherd, .badge-community {
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-success { background: #28A745; color: white; }
    .badge-warning { background: #FFC107; color: #333; }
    .badge-info { background: #17A2B8; color: white; }
    .badge-secondary { background: #6C757D; color: white; }
    .badge-staff { background: #17A2B8; color: white; }
    .badge-shepherd { background: #20B2AA; color: white; }
    .badge-community { background: #6C757D; color: white; }

    [data-testid="stSidebar"] .stRadio label {
        color: #E8E8E8 !important;
        font-size: 0.85rem !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #2E5A8A !important;
    }

    .stButton > button:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: #F1F1F1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: #1E3A5F;
        border-radius: 10px;
    }

    .main-header {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 8px 20px;
        background: white;
        border-radius: 0 0 0 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
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
        width: 45px;
        height: 45px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #A8B56C;
    }

    .header-text {
        text-align: right;
    }

    .header-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1E3A5F;
        margin: 0;
    }

    .header-subtitle {
        font-size: 0.65rem;
        color: #6C757D;
        margin: 0;
    }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin: 0;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #6C757D;
        margin: 0;
        font-weight: 600;
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


# ==================== ENHANCED CACHE SYSTEM ====================
class SmartCache:
    """Enhanced cache with different TTLs for different data types"""

    def __init__(self):
        self.cache = {}
        self.ttl_config = {
            "pupils": 1200,  # 20 minutes - pupil data rarely changes
            "ledger": 300,  # 5 minutes - payments can happen frequently
            "stats": 600,  # 10 minutes - dashboard stats
            "summary": 900,  # 15 minutes - reports
            "balance": 60,  # 1 minute - critical for payment accuracy
            "classes": 3600,  # 60 minutes - class lists
        }

    def get(self, key, data_type="pupils"):
        """Get cached data if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            ttl = self.ttl_config.get(data_type, 300)
            if datetime.datetime.now() - timestamp < timedelta(seconds=ttl):
                return data
            else:
                # Expired, remove it
                del self.cache[key]
        return None

    def set(self, key, data, data_type="pupils"):
        """Store data in cache"""
        self.cache[key] = (data, datetime.datetime.now())

    def invalidate(self, key=None, data_type=None):
        """Clear cache for a specific key, data type, or all"""
        if key:
            self.cache.pop(key, None)
        elif data_type:
            # Invalidate all keys of a certain type (by prefix)
            keys_to_remove = [k for k in self.cache if k.startswith(data_type)]
            for k in keys_to_remove:
                self.cache.pop(k, None)
        else:
            self.cache.clear()

    def clear_all(self):
        """Clear entire cache"""
        self.cache.clear()


# Initialize cache
cache = SmartCache()


# ==================== FIREBASE INITIALIZATION ====================
def init_firebase():
    if st.session_state.get("firebase_done", False):
        return firestore.client()

    if not firebase_admin._apps:
        try:
            firebase_creds = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            st.session_state.firebase_done = True
        except:
            if os.path.exists("firebase-key.json"):
                cred = credentials.Certificate("firebase-key.json")
                firebase_admin.initialize_app(cred)
                st.session_state.firebase_done = True
            else:
                st.error("Firebase credentials not found.")
                st.stop()
    return firestore.client()


db = init_firebase()


# ==================== HELPER FUNCTIONS ====================
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
                <img src="data:{mime_type};base64,{logo_base64}" class="header-logo" height="45" width="45">
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
                <div style="width: 45px; height: 45px; border-radius: 50%; background: linear-gradient(135deg, #A8B56C, #6B7B3A); display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 1.3rem;">🏫</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


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


def firestore_to_serializable(docs):
    """Convert Firestore documents to serializable dicts"""
    result = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                data[key] = value.isoformat()
        result.append(data)
    return result


# ==================== CLASS PROGRESSION ====================
CLASS_PROGRESSION = {
    "Baby Class": "Middle Class",
    "Middle Class": "Top Class",
    "Top Class": "P1",
    "P1": "P2",
    "P2": "P3",
    "P3": "P4",
    "P4": "P5",
    "P5": "P6",
    "P6": "P7",
    "P7": None  # Completed primary
}

TERM_ORDER = ["Term 1", "Term 2", "Term 3"]


# ==================== FEES MANAGER ====================
class FeesManager:
    def __init__(self):
        self.classes = list(CLASS_PROGRESSION.keys())
        self.terms = ["Term 1", "Term 2", "Term 3"]
        self.term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
        self.pupil_types = ["Community Child", "Staff Child", "Shepherd Child"]

    def get_next_class(self, current_class):
        """Get the next class for promotion"""
        return CLASS_PROGRESSION.get(current_class, current_class)

    def get_all_pupils(self, include_archived=False):
        """Get all pupils with caching"""
        cache_key = f"pupils_all_{include_archived}"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        try:
            if include_archived:
                docs = list(db.collection("pupils").stream())
            else:
                docs = list(db.collection("pupils").where("active", "==", True).stream())
            result = firestore_to_serializable(docs)
            cache.set(cache_key, result, "pupils")
            return result
        except Exception as e:
            st.error(f"Error fetching pupils: {str(e)}")
            return []

    def get_archived_pupils(self):
        """Get archived pupils with caching"""
        cache_key = "pupils_archived"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        try:
            docs = list(db.collection("pupils").where("archived", "==", True).stream())
            result = firestore_to_serializable(docs)
            cache.set(cache_key, result, "pupils")
            return result
        except Exception as e:
            return []

    def get_pupils_by_class(self, class_name, include_archived=False):
        """Get pupils by class"""
        all_pupils = self.get_all_pupils(include_archived)
        return [p for p in all_pupils if p.get("class") == class_name]

    def get_pupils_for_term(self, class_name, term, year, include_archived=False):
        """Only show pupils who are ENROLLED in this specific term"""
        all_pupils = self.get_pupils_by_class(class_name, include_archived)
        term_key = f"{year}_{term}"

        filtered = []
        for pupil in all_pupils:
            if pupil.get("archived", False) and not include_archived:
                continue

            # Check if pupil is enrolled in this term
            enrollments = pupil.get("term_enrollments", {})
            is_enrolled = enrollments.get(term_key, {}).get("active", False)

            # Also check if this is the enrollment term (for newly enrolled pupils)
            is_initial_enrollment = (pupil.get("enrollment_term") == term and
                                     pupil.get("enrollment_year") == year)

            if is_enrolled or is_initial_enrollment:
                if pupil.get("class") == class_name or class_name == "All Classes":
                    filtered.append(pupil)

        return filtered

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
        """Get balance/credit from previous term (excess carries forward)"""
        term_order = self.term_order
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

        ledger_entries = self.get_ledger(pupil_id, prev_term, prev_year)
        if ledger_entries:
            last_entry = ledger_entries[-1]
            balance = last_entry.get("balance", 0)
            excess = last_entry.get("excess_amount", 0)

            # If balance is 0 but there's excess, return negative excess (credit)
            if balance == 0 and excess > 0:
                return -excess
            return balance
        return 0

    def get_ledger(self, pupil_id, term, year):
        """Get ledger entries with caching"""
        cache_key = f"ledger_{pupil_id}_{term}_{year}"
        cached = cache.get(cache_key, "ledger")
        if cached is not None:
            return cached

        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            all_docs = list(ledger_ref.stream())
            filtered_docs = []
            for doc in all_docs:
                data = doc.to_dict()
                doc_year = data.get("year")
                if doc_year is not None and int(doc_year) == int(year):
                    filtered_docs.append(doc)
            filtered_docs.sort(key=lambda x: x.to_dict().get("date", datetime.datetime.min))

            result = firestore_to_serializable(filtered_docs)
            cache.set(cache_key, result, "ledger")
            return result
        except Exception as e:
            st.error(f"Error fetching ledger: {str(e)}")
            return []

    def enroll_pupil(self, name, class_name, term_fees, pupil_type, current_term, current_year):
        """Enroll a new pupil with current term/year"""
        try:
            pupil_ref = db.collection("pupils").document()

            if pupil_type == "Shepherd Child":
                is_sponsored = True
                sponsor_reason = "Shepherd Child"
                term_fees = 0
            elif pupil_type == "Staff Child":
                is_sponsored = False
                sponsor_reason = "Staff Child"
            else:
                is_sponsored = False
                sponsor_reason = ""

            term_key = f"{current_year}_{current_term}"
            term_enrollments = {
                term_key: {
                    "active": True,
                    "class": class_name,
                    "enrolled_at": datetime.datetime.now().isoformat(),
                    "term_fees": term_fees,
                    "pupil_type": pupil_type
                }
            }

            pupil_ref.set({
                "name": name,
                "class": class_name,
                "enrollment_date": datetime.datetime.now().isoformat(),
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "active": True,
                "archived": False,
                "leaving_date": None,
                "leaving_reason": None,
                "enrollment_term": current_term,
                "enrollment_year": current_year,
                "current_term": current_term,
                "current_year": current_year,
                "active_since_term": current_term,
                "active_since_year": current_year,
                "term_enrollments": term_enrollments
            })

            # Invalidate caches
            cache.invalidate(data_type="pupils")
            cache.invalidate(data_type="stats")
            return pupil_ref.id
        except Exception as e:
            st.error(f"Error enrolling pupil: {str(e)}")
            return None

    def get_pupil_details(self, pupil_id):
        """Get pupil details"""
        cache_key = f"pupil_{pupil_id}"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        try:
            doc = db.collection("pupils").document(pupil_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                cache.set(cache_key, data, "pupils")
                return data
            return None
        except Exception as e:
            return None

    def update_pupil(self, pupil_id, name, class_name, term_fees, pupil_type):
        """Update pupil details"""
        try:
            if pupil_type == "Shepherd Child":
                is_sponsored = True
                sponsor_reason = "Shepherd Child"
                term_fees = 0
            elif pupil_type == "Staff Child":
                is_sponsored = False
                sponsor_reason = "Staff Child"
            else:
                is_sponsored = False
                sponsor_reason = ""

            db.collection("pupils").document(pupil_id).update({
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "updated_at": datetime.datetime.now().isoformat()
            })

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error updating pupil: {str(e)}")
            return False

    def update_pupil_class(self, pupil_id, new_class):
        """Update pupil's class (for promotion)"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "class": new_class,
                "last_promoted_at": datetime.datetime.now().isoformat()
            })
            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            return False

    def update_pupil_term_status(self, pupil_id, term, year):
        """Update pupil's current term tracking"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "current_term": term,
                "current_year": year,
                "last_advanced_at": datetime.datetime.now().isoformat()
            })
            return True
        except Exception as e:
            return False

    def archive_pupil(self, pupil_id, leaving_reason=""):
        """Archive a pupil"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "active": False,
                "archived": True,
                "leaving_date": datetime.datetime.now().isoformat(),
                "leaving_reason": leaving_reason,
                "archived_at": datetime.datetime.now().isoformat()
            })
            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id, return_term, return_year):
        """Restore an archived pupil to a specific term"""
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

            term_key = f"{return_year}_{return_term}"
            enrollments = pupil_data.get("term_enrollments", {})

            enrollments[term_key] = {
                "active": True,
                "class": pupil_data.get("class"),
                "enrolled_at": datetime.datetime.now().isoformat(),
                "term_fees": pupil_data.get("term_fees", 0),
                "pupil_type": pupil_data.get("pupil_type", "Community Child"),
                "restored": True
            }

            db.collection("pupils").document(pupil_id).update({
                "active": True,
                "archived": False,
                "restored_at": datetime.datetime.now().isoformat(),
                "restored_term": return_term,
                "restored_year": return_year,
                "active_since_term": return_term,
                "active_since_year": return_year,
                "current_term": return_term,
                "current_year": return_year,
                "term_enrollments": enrollments
            })

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    # ==================== NEW TERM ENROLLMENT METHODS ====================

    def enroll_pupil_into_term(self, pupil_id, term, year):
        """Enroll a pupil into a specific term"""
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

            term_key = f"{year}_{term}"
            enrollments = pupil_data.get("term_enrollments", {})

            enrollments[term_key] = {
                "active": True,
                "class": pupil_data.get("class"),
                "enrolled_at": datetime.datetime.now().isoformat(),
                "term_fees": pupil_data.get("term_fees", 0),
                "pupil_type": pupil_data.get("pupil_type", "Community Child")
            }

            db.collection("pupils").document(pupil_id).update({
                "term_enrollments": enrollments,
                "current_term": term,
                "current_year": year,
                f"enrolled_in_{term}_{year}": True
            })

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error enrolling pupil into term: {str(e)}")
            return False

    def is_enrolled_in_term(self, pupil_id, term, year):
        """Check if pupil is enrolled in a specific term"""
        pupil_data = self.get_pupil_details(pupil_id)
        if not pupil_data:
            return False

        term_key = f"{year}_{term}"
        enrollments = pupil_data.get("term_enrollments", {})
        return enrollments.get(term_key, {}).get("active", False)

    # ==================== END NEW METHODS ====================

    def add_payment(self, pupil_id, term, year, amount, description):
        """Add a payment with excess handling (excess carries forward as credit)"""
        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            pupil = self.get_pupil_details(pupil_id)
            if not pupil:
                return None, "Pupil not found", None, None, 0

            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)

            if is_sponsored:
                term_fees = 0

            year_int = int(year)
            previous_balance = self.get_previous_term_balance(pupil_id, term, year_int)
            existing_payments = self.get_ledger(pupil_id, term, year_int)
            total_paid_this_term = sum([p.get("amount", 0) for p in existing_payments])

            # Calculate total due (if previous balance is negative, it's a credit)
            effective_previous = max(0, previous_balance) if previous_balance > 0 else 0
            credit_amount = abs(previous_balance) if previous_balance < 0 else 0

            total_due = effective_previous + term_fees
            total_paid = total_paid_this_term + amount

            # Apply credit first
            if credit_amount > 0:
                total_paid_with_credit = total_paid + credit_amount
                if total_paid_with_credit >= total_due:
                    new_balance = 0
                    excess_amount = total_paid_with_credit - total_due
                else:
                    new_balance = total_due - total_paid_with_credit
                    excess_amount = 0
            else:
                if total_paid > total_due:
                    excess_amount = total_paid - total_due
                    new_balance = 0
                else:
                    excess_amount = 0
                    new_balance = total_due - total_paid

            transaction_id = str(uuid.uuid4())
            receipt_no = generate_receipt_number()

            ledger_ref.document(transaction_id).set({
                "date": datetime.datetime.now().isoformat(),
                "amount": amount,
                "description": description,
                "balance": new_balance,
                "previous_balance": previous_balance,
                "term_fees": term_fees,
                "total_due": total_due,
                "year": year_int,
                "receipt_no": receipt_no,
                "excess_amount": excess_amount,
                "credit_applied": credit_amount
            })

            # Invalidate caches
            cache.invalidate(f"ledger_{pupil_id}_{term}_{year_int}", "ledger")
            cache.invalidate(data_type="stats")
            cache.invalidate(data_type="summary")

            return transaction_id, new_balance, receipt_no, previous_balance, excess_amount
        except Exception as e:
            st.error(f"Error adding payment: {str(e)}")
            return None, str(e), None, None, 0

    def get_pupil_term_summary(self, pupil_id, term, year):
        """Get pupil term summary"""
        pupil_data = self.get_pupil_details(pupil_id)
        if not pupil_data:
            return None, 0, 0, 0, 0, 0, False, "", False, "Community Child", 0

        term_fees = pupil_data.get("term_fees", 0)
        is_sponsored = pupil_data.get("is_sponsored", False)
        sponsor_reason = pupil_data.get("sponsor_reason", "")
        is_archived = pupil_data.get("archived", False)
        pupil_type = pupil_data.get("pupil_type", "Community Child")

        if is_sponsored:
            term_fees = 0

        previous_balance = self.get_previous_term_balance(pupil_id, term, year)
        payments = self.get_ledger(pupil_id, term, year)
        total_paid = sum([p.get("amount", 0) for p in payments])

        credit_amount = abs(previous_balance) if previous_balance < 0 else 0
        effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

        total_due = effective_previous + term_fees
        balance = max(0, total_due - total_paid - credit_amount)

        return (pupil_data, term_fees, total_paid, balance, previous_balance,
                credit_amount, is_sponsored, sponsor_reason, is_archived, pupil_type, effective_previous)

    def get_class_summary(self, class_name, term, year, include_archived=False):
        """Get class summary as DataFrames"""
        pupils = self.get_pupils_for_term(class_name, term, year, include_archived)
        summary = []
        cleared_list = []
        not_cleared_list = []
        archived_list = []

        for pupil in pupils:
            pupil_id = pupil.get('id')
            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)
            sponsor_reason = pupil.get("sponsor_reason", "")
            is_archived = pupil.get("archived", False)
            pupil_type = pupil.get("pupil_type", "Community Child")

            if is_sponsored:
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = self.get_ledger(pupil_id, term, year)
            total_paid = sum([p.get("amount", 0) for p in payments])

            credit_amount = abs(previous_balance) if previous_balance < 0 else 0
            effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

            total_due = effective_previous + term_fees
            balance = max(0, total_due - total_paid - credit_amount)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if is_sponsored:
                    status = f"Sponsored - {sponsor_reason}"

            pupil_info = {
                "Name": pupil["name"],
                "Pupil Type": pupil_type,
                "Enrolled": f"{pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', year)}",
                "Previous Bal (UGX)": previous_balance,
                "Credit (UGX)": credit_amount if credit_amount > 0 else 0,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if is_sponsored else "",
            }
            summary.append(pupil_info)

            if is_archived:
                archived_list.append(pupil_info)
            elif balance == 0 or is_sponsored:
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
        """Get school-wide summary as DataFrames"""
        cache_key = f"summary_{term}_{year}_{include_archived}"
        cached_result = cache.get(cache_key, "summary")
        if cached_result is not None:
            return cached_result

        all_pupils = self.get_all_pupils(include_archived)
        all_summaries = []
        staff_summaries = []
        shepherd_summaries = []
        community_summaries = []

        for pupil in all_pupils:
            pupil_id = pupil.get('id')
            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)
            sponsor_reason = pupil.get("sponsor_reason", "")
            is_archived = pupil.get("archived", False)
            pupil_type = pupil.get("pupil_type", "Community Child")

            if is_sponsored:
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = self.get_ledger(pupil_id, term, year)
            total_paid = sum([p.get("amount", 0) for p in payments])

            credit_amount = abs(previous_balance) if previous_balance < 0 else 0
            effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

            total_due = effective_previous + term_fees
            balance = max(0, total_due - total_paid - credit_amount)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if is_sponsored:
                    status = f"Sponsored - {sponsor_reason}"

            record = {
                "Class": pupil["class"],
                "Name": pupil["name"],
                "Pupil Type": pupil_type,
                "Enrolled": f"{pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', year)}",
                "Credit (UGX)": credit_amount if credit_amount > 0 else 0,
                "Term Fees (UGX)": term_fees,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
            }
            all_summaries.append(record)

            if pupil_type == "Staff Child" and not is_archived:
                staff_summaries.append(record)
            elif pupil_type == "Shepherd Child" and not is_archived:
                shepherd_summaries.append(record)
            elif pupil_type == "Community Child" and not is_archived:
                community_summaries.append(record)

        df_all = pd.DataFrame(all_summaries).reset_index(drop=True)
        df_staff = pd.DataFrame(staff_summaries).reset_index(drop=True)
        df_shepherd = pd.DataFrame(shepherd_summaries).reset_index(drop=True)
        df_community = pd.DataFrame(community_summaries).reset_index(drop=True)

        if not df_all.empty:
            df_all.insert(0, "No.", range(1, len(df_all) + 1))

        result = (df_all, df_staff, df_shepherd, df_community)
        cache.set(cache_key, result, "summary")
        return result

    def get_dashboard_stats(self, term, year):
        """Get dashboard statistics with caching"""
        cache_key = f"stats_{term}_{year}"
        cached = cache.get(cache_key, "stats")
        if cached is not None:
            return cached

        all_pupils = self.get_all_pupils(include_archived=False)

        stats = {
            "total_pupils": len(all_pupils),
            "staff_children": 0,
            "shepherd_children": 0,
            "community_children": 0,
            "total_expected": 0,
            "total_collected": 0,
            "total_balance": 0,
            "collection_rate": 0
        }

        for pupil in all_pupils:
            pupil_type = pupil.get("pupil_type", "Community Child")
            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)

            if is_sponsored:
                term_fees = 0

            if pupil_type == "Staff Child":
                stats["staff_children"] += 1
            elif pupil_type == "Shepherd Child":
                stats["shepherd_children"] += 1
            else:
                stats["community_children"] += 1

            stats["total_expected"] += term_fees

            pupil_id = pupil.get('id')
            payments = self.get_ledger(pupil_id, term, year)
            total_paid = sum([p.get("amount", 0) for p in payments])
            stats["total_collected"] += total_paid

        stats["total_balance"] = stats["total_expected"] - stats["total_collected"]
        if stats["total_expected"] > 0:
            stats["collection_rate"] = (stats["total_collected"] / stats["total_expected"]) * 100

        cache.set(cache_key, stats, "stats")
        return stats


# ==================== LOGIN PAGE ====================
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
                <img src="data:{mime_type};base64,{logo_base64}" height="150" style="border-radius: 10px;">
                <div>
                    <h3 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h3>
                    <p style="color: #6C757D; margin: 2px 0 0 0; font-size: 0.8rem;">School Fees Management System</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: 0px;">
                <div style="background: linear-gradient(135deg, #1E3A5F, #2E5A8A); border-radius: 10px; width: 70px; height: 70px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 1.8rem;">🏫</span>
                </div>
                <div>
                    <h3 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h3>
                    <p style="color: #6C757D; margin: 2px 0 0 0; font-size: 0.8rem;">School Fees Management System</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Create default users if none exist
        try:
            users_ref = db.collection("users")
            if len(list(users_ref.stream())) == 0:
                users_ref.document("bursar").set({
                    "username": "bursar",
                    "password": hash_password("bursar123"),
                    "role": "bursar",
                    "full_name": "School Bursar",
                    "created_at": datetime.datetime.now()
                })
                users_ref.document("admin").set({
                    "username": "admin",
                    "password": hash_password("admin123"),
                    "role": "admin",
                    "full_name": "School Administrator",
                    "created_at": datetime.datetime.now()
                })
        except:
            pass

        with st.form(key="login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    try:
                        users_ref = db.collection("users")
                        user_doc = users_ref.document(username).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            if user_data.get("password") == hash_password(password):
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.role = user_data.get("role", "admin")
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                        else:
                            st.error("Invalid username or password")
                    except Exception as e:
                        st.error(f"Authentication error: {str(e)}")


# ==================== MAIN APP ====================
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
from datetime import timedelta
import json

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
    "white": "#FFFFFF",
    "staff": "#17A2B8",
    "shepherd": "#20B2AA",
    "community": "#6C757D"
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
        padding: 1rem;
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
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
        font-size: 0.85rem;
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

    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }

    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div,
    [data-testid="stSidebar"] .stNumberInput input {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #A8B56C !important;
        font-size: 1rem !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #E8E8E8 !important;
    }

    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #E5E7EB;
        padding: 0.5rem 1rem;
    }

    .dataframe {
        border-radius: 16px !important;
        overflow: hidden;
    }
    .dataframe thead tr th {
        background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8A 100%) !important;
        color: white !important;
        padding: 10px !important;
        font-size: 0.8rem !important;
    }

    .streamlit-expanderHeader {
        background: #F8F9FA;
        border-radius: 12px;
        font-weight: 600;
    }

    .badge-success, .badge-warning, .badge-info, .badge-secondary,
    .badge-staff, .badge-shepherd, .badge-community {
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-success { background: #28A745; color: white; }
    .badge-warning { background: #FFC107; color: #333; }
    .badge-info { background: #17A2B8; color: white; }
    .badge-secondary { background: #6C757D; color: white; }
    .badge-staff { background: #17A2B8; color: white; }
    .badge-shepherd { background: #20B2AA; color: white; }
    .badge-community { background: #6C757D; color: white; }

    [data-testid="stSidebar"] .stRadio label {
        color: #E8E8E8 !important;
        font-size: 0.85rem !important;
    }

    [data-testid="stSidebar"] hr {
        border-color: #2E5A8A !important;
    }

    .stButton > button:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: #F1F1F1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: #1E3A5F;
        border-radius: 10px;
    }

    .main-header {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding: 8px 20px;
        background: white;
        border-radius: 0 0 0 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
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
        width: 45px;
        height: 45px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #A8B56C;
    }

    .header-text {
        text-align: right;
    }

    .header-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1E3A5F;
        margin: 0;
    }

    .header-subtitle {
        font-size: 0.65rem;
        color: #6C757D;
        margin: 0;
    }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 0.75rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin: 0;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #6C757D;
        margin: 0;
        font-weight: 600;
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


# ==================== ENHANCED CACHE SYSTEM ====================
class SmartCache:
    """Enhanced cache with different TTLs for different data types"""

    def __init__(self):
        self.cache = {}
        self.ttl_config = {
            "pupils": 1200,  # 20 minutes - pupil data rarely changes
            "ledger": 300,  # 5 minutes - payments can happen frequently
            "stats": 600,  # 10 minutes - dashboard stats
            "summary": 900,  # 15 minutes - reports
            "balance": 60,  # 1 minute - critical for payment accuracy
            "classes": 3600,  # 60 minutes - class lists
        }

    def get(self, key, data_type="pupils"):
        """Get cached data if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            ttl = self.ttl_config.get(data_type, 300)
            if datetime.datetime.now() - timestamp < timedelta(seconds=ttl):
                return data
            else:
                # Expired, remove it
                del self.cache[key]
        return None

    def set(self, key, data, data_type="pupils"):
        """Store data in cache"""
        self.cache[key] = (data, datetime.datetime.now())

    def invalidate(self, key=None, data_type=None):
        """Clear cache for a specific key, data type, or all"""
        if key:
            self.cache.pop(key, None)
        elif data_type:
            # Invalidate all keys of a certain type (by prefix)
            keys_to_remove = [k for k in self.cache if k.startswith(data_type)]
            for k in keys_to_remove:
                self.cache.pop(k, None)
        else:
            self.cache.clear()

    def clear_all(self):
        """Clear entire cache"""
        self.cache.clear()


# Initialize cache
cache = SmartCache()


# ==================== FIREBASE INITIALIZATION ====================
def init_firebase():
    if st.session_state.get("firebase_done", False):
        return firestore.client()

    if not firebase_admin._apps:
        try:
            firebase_creds = dict(st.secrets["firebase"])
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            st.session_state.firebase_done = True
        except:
            if os.path.exists("firebase-key.json"):
                cred = credentials.Certificate("firebase-key.json")
                firebase_admin.initialize_app(cred)
                st.session_state.firebase_done = True
            else:
                st.error("Firebase credentials not found.")
                st.stop()
    return firestore.client()


db = init_firebase()


# ==================== HELPER FUNCTIONS ====================
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
                <img src="data:{mime_type};base64,{logo_base64}" class="header-logo" height="45" width="45">
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
                <div style="width: 45px; height: 45px; border-radius: 50%; background: linear-gradient(135deg, #A8B56C, #6B7B3A); display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 1.3rem;">🏫</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


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


def firestore_to_serializable(docs):
    """Convert Firestore documents to serializable dicts"""
    result = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                data[key] = value.isoformat()
        result.append(data)
    return result


# ==================== CLASS PROGRESSION ====================
CLASS_PROGRESSION = {
    "Baby Class": "Middle Class",
    "Middle Class": "Top Class",
    "Top Class": "P1",
    "P1": "P2",
    "P2": "P3",
    "P3": "P4",
    "P4": "P5",
    "P5": "P6",
    "P6": "P7",
    "P7": None  # Completed primary
}

TERM_ORDER = ["Term 1", "Term 2", "Term 3"]


# ==================== FEES MANAGER ====================
class FeesManager:
    def __init__(self):
        self.classes = list(CLASS_PROGRESSION.keys())
        self.terms = ["Term 1", "Term 2", "Term 3"]
        self.term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
        self.pupil_types = ["Community Child", "Staff Child", "Shepherd Child"]

    def get_next_class(self, current_class):
        """Get the next class for promotion"""
        return CLASS_PROGRESSION.get(current_class, current_class)

    def get_all_pupils(self, include_archived=False):
        """Get all pupils with caching"""
        cache_key = f"pupils_all_{include_archived}"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        try:
            if include_archived:
                docs = list(db.collection("pupils").stream())
            else:
                docs = list(db.collection("pupils").where("active", "==", True).stream())
            result = firestore_to_serializable(docs)
            cache.set(cache_key, result, "pupils")
            return result
        except Exception as e:
            st.error(f"Error fetching pupils: {str(e)}")
            return []

    def get_archived_pupils(self):
        """Get archived pupils with caching"""
        cache_key = "pupils_archived"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        try:
            docs = list(db.collection("pupils").where("archived", "==", True).stream())
            result = firestore_to_serializable(docs)
            cache.set(cache_key, result, "pupils")
            return result
        except Exception as e:
            return []

    def get_pupils_by_class(self, class_name, include_archived=False):
        """Get pupils by class"""
        all_pupils = self.get_all_pupils(include_archived)
        return [p for p in all_pupils if p.get("class") == class_name]

    def get_pupils_for_term(self, class_name, term, year, include_archived=False):
        """Only show pupils who are ENROLLED in this specific term"""
        all_pupils = self.get_pupils_by_class(class_name, include_archived)
        term_key = f"{year}_{term}"

        filtered = []
        for pupil in all_pupils:
            if pupil.get("archived", False) and not include_archived:
                continue

            # Check if pupil is enrolled in this term
            enrollments = pupil.get("term_enrollments", {})
            is_enrolled = enrollments.get(term_key, {}).get("active", False)

            # Also check if this is the enrollment term (for newly enrolled pupils)
            is_initial_enrollment = (pupil.get("enrollment_term") == term and
                                     pupil.get("enrollment_year") == year)

            if is_enrolled or is_initial_enrollment:
                if pupil.get("class") == class_name or class_name == "All Classes":
                    filtered.append(pupil)

        return filtered

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
        """Get balance/credit from previous term (excess carries forward)"""
        term_order = self.term_order
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

        ledger_entries = self.get_ledger(pupil_id, prev_term, prev_year)
        if ledger_entries:
            last_entry = ledger_entries[-1]
            balance = last_entry.get("balance", 0)
            excess = last_entry.get("excess_amount", 0)

            # If balance is 0 but there's excess, return negative excess (credit)
            if balance == 0 and excess > 0:
                return -excess
            return balance
        return 0

    def get_ledger(self, pupil_id, term, year):
        """Get ledger entries with caching"""
        cache_key = f"ledger_{pupil_id}_{term}_{year}"
        cached = cache.get(cache_key, "ledger")
        if cached is not None:
            return cached

        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            all_docs = list(ledger_ref.stream())
            filtered_docs = []
            for doc in all_docs:
                data = doc.to_dict()
                doc_year = data.get("year")
                if doc_year is not None and int(doc_year) == int(year):
                    filtered_docs.append(doc)
            filtered_docs.sort(key=lambda x: x.to_dict().get("date", datetime.datetime.min))

            result = firestore_to_serializable(filtered_docs)
            cache.set(cache_key, result, "ledger")
            return result
        except Exception as e:
            st.error(f"Error fetching ledger: {str(e)}")
            return []

    def enroll_pupil(self, name, class_name, term_fees, pupil_type, current_term, current_year):
        """Enroll a new pupil with current term/year"""
        try:
            pupil_ref = db.collection("pupils").document()

            if pupil_type == "Shepherd Child":
                is_sponsored = True
                sponsor_reason = "Shepherd Child"
                term_fees = 0
            elif pupil_type == "Staff Child":
                is_sponsored = False
                sponsor_reason = "Staff Child"
            else:
                is_sponsored = False
                sponsor_reason = ""

            term_key = f"{current_year}_{current_term}"
            term_enrollments = {
                term_key: {
                    "active": True,
                    "class": class_name,
                    "enrolled_at": datetime.datetime.now().isoformat(),
                    "term_fees": term_fees,
                    "pupil_type": pupil_type
                }
            }

            pupil_ref.set({
                "name": name,
                "class": class_name,
                "enrollment_date": datetime.datetime.now().isoformat(),
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "active": True,
                "archived": False,
                "leaving_date": None,
                "leaving_reason": None,
                "enrollment_term": current_term,
                "enrollment_year": current_year,
                "current_term": current_term,
                "current_year": current_year,
                "active_since_term": current_term,
                "active_since_year": current_year,
                "term_enrollments": term_enrollments
            })

            # Invalidate caches
            cache.invalidate(data_type="pupils")
            cache.invalidate(data_type="stats")
            return pupil_ref.id
        except Exception as e:
            st.error(f"Error enrolling pupil: {str(e)}")
            return None

    def get_pupil_details(self, pupil_id):
        """Get pupil details"""
        cache_key = f"pupil_{pupil_id}"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        try:
            doc = db.collection("pupils").document(pupil_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                cache.set(cache_key, data, "pupils")
                return data
            return None
        except Exception as e:
            return None

    def update_pupil(self, pupil_id, name, class_name, term_fees, pupil_type):
        """Update pupil details"""
        try:
            if pupil_type == "Shepherd Child":
                is_sponsored = True
                sponsor_reason = "Shepherd Child"
                term_fees = 0
            elif pupil_type == "Staff Child":
                is_sponsored = False
                sponsor_reason = "Staff Child"
            else:
                is_sponsored = False
                sponsor_reason = ""

            db.collection("pupils").document(pupil_id).update({
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "updated_at": datetime.datetime.now().isoformat()
            })

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error updating pupil: {str(e)}")
            return False

    def update_pupil_class(self, pupil_id, new_class):
        """Update pupil's class (for promotion)"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "class": new_class,
                "last_promoted_at": datetime.datetime.now().isoformat()
            })
            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            return False

    def update_pupil_term_status(self, pupil_id, term, year):
        """Update pupil's current term tracking"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "current_term": term,
                "current_year": year,
                "last_advanced_at": datetime.datetime.now().isoformat()
            })
            return True
        except Exception as e:
            return False

    def archive_pupil(self, pupil_id, leaving_reason=""):
        """Archive a pupil"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "active": False,
                "archived": True,
                "leaving_date": datetime.datetime.now().isoformat(),
                "leaving_reason": leaving_reason,
                "archived_at": datetime.datetime.now().isoformat()
            })
            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id, return_term, return_year):
        """Restore an archived pupil to a specific term"""
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

            term_key = f"{return_year}_{return_term}"
            enrollments = pupil_data.get("term_enrollments", {})

            enrollments[term_key] = {
                "active": True,
                "class": pupil_data.get("class"),
                "enrolled_at": datetime.datetime.now().isoformat(),
                "term_fees": pupil_data.get("term_fees", 0),
                "pupil_type": pupil_data.get("pupil_type", "Community Child"),
                "restored": True
            }

            db.collection("pupils").document(pupil_id).update({
                "active": True,
                "archived": False,
                "restored_at": datetime.datetime.now().isoformat(),
                "restored_term": return_term,
                "restored_year": return_year,
                "active_since_term": return_term,
                "active_since_year": return_year,
                "current_term": return_term,
                "current_year": return_year,
                "term_enrollments": enrollments
            })

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    # ==================== NEW TERM ENROLLMENT METHODS ====================

    def enroll_pupil_into_term(self, pupil_id, term, year):
        """Enroll a pupil into a specific term"""
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

            term_key = f"{year}_{term}"
            enrollments = pupil_data.get("term_enrollments", {})

            enrollments[term_key] = {
                "active": True,
                "class": pupil_data.get("class"),
                "enrolled_at": datetime.datetime.now().isoformat(),
                "term_fees": pupil_data.get("term_fees", 0),
                "pupil_type": pupil_data.get("pupil_type", "Community Child")
            }

            db.collection("pupils").document(pupil_id).update({
                "term_enrollments": enrollments,
                "current_term": term,
                "current_year": year,
                f"enrolled_in_{term}_{year}": True
            })

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error enrolling pupil into term: {str(e)}")
            return False

    def is_enrolled_in_term(self, pupil_id, term, year):
        """Check if pupil is enrolled in a specific term"""
        pupil_data = self.get_pupil_details(pupil_id)
        if not pupil_data:
            return False

        term_key = f"{year}_{term}"
        enrollments = pupil_data.get("term_enrollments", {})
        return enrollments.get(term_key, {}).get("active", False)

    # ==================== END NEW METHODS ====================

    def add_payment(self, pupil_id, term, year, amount, description):
        """Add a payment with excess handling (excess carries forward as credit)"""
        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            pupil = self.get_pupil_details(pupil_id)
            if not pupil:
                return None, "Pupil not found", None, None, 0

            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)

            if is_sponsored:
                term_fees = 0

            year_int = int(year)
            previous_balance = self.get_previous_term_balance(pupil_id, term, year_int)
            existing_payments = self.get_ledger(pupil_id, term, year_int)
            total_paid_this_term = sum([p.get("amount", 0) for p in existing_payments])

            # Calculate total due (if previous balance is negative, it's a credit)
            effective_previous = max(0, previous_balance) if previous_balance > 0 else 0
            credit_amount = abs(previous_balance) if previous_balance < 0 else 0

            total_due = effective_previous + term_fees
            total_paid = total_paid_this_term + amount

            # Apply credit first
            if credit_amount > 0:
                total_paid_with_credit = total_paid + credit_amount
                if total_paid_with_credit >= total_due:
                    new_balance = 0
                    excess_amount = total_paid_with_credit - total_due
                else:
                    new_balance = total_due - total_paid_with_credit
                    excess_amount = 0
            else:
                if total_paid > total_due:
                    excess_amount = total_paid - total_due
                    new_balance = 0
                else:
                    excess_amount = 0
                    new_balance = total_due - total_paid

            transaction_id = str(uuid.uuid4())
            receipt_no = generate_receipt_number()

            ledger_ref.document(transaction_id).set({
                "date": datetime.datetime.now().isoformat(),
                "amount": amount,
                "description": description,
                "balance": new_balance,
                "previous_balance": previous_balance,
                "term_fees": term_fees,
                "total_due": total_due,
                "year": year_int,
                "receipt_no": receipt_no,
                "excess_amount": excess_amount,
                "credit_applied": credit_amount
            })

            # Invalidate caches
            cache.invalidate(f"ledger_{pupil_id}_{term}_{year_int}", "ledger")
            cache.invalidate(data_type="stats")
            cache.invalidate(data_type="summary")

            return transaction_id, new_balance, receipt_no, previous_balance, excess_amount
        except Exception as e:
            st.error(f"Error adding payment: {str(e)}")
            return None, str(e), None, None, 0

    def get_pupil_term_summary(self, pupil_id, term, year):
        """Get pupil term summary"""
        pupil_data = self.get_pupil_details(pupil_id)
        if not pupil_data:
            return None, 0, 0, 0, 0, 0, False, "", False, "Community Child", 0

        term_fees = pupil_data.get("term_fees", 0)
        is_sponsored = pupil_data.get("is_sponsored", False)
        sponsor_reason = pupil_data.get("sponsor_reason", "")
        is_archived = pupil_data.get("archived", False)
        pupil_type = pupil_data.get("pupil_type", "Community Child")

        if is_sponsored:
            term_fees = 0

        previous_balance = self.get_previous_term_balance(pupil_id, term, year)
        payments = self.get_ledger(pupil_id, term, year)
        total_paid = sum([p.get("amount", 0) for p in payments])

        credit_amount = abs(previous_balance) if previous_balance < 0 else 0
        effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

        total_due = effective_previous + term_fees
        balance = max(0, total_due - total_paid - credit_amount)

        return (pupil_data, term_fees, total_paid, balance, previous_balance,
                credit_amount, is_sponsored, sponsor_reason, is_archived, pupil_type, effective_previous)

    def get_class_summary(self, class_name, term, year, include_archived=False):
        """Get class summary as DataFrames"""
        pupils = self.get_pupils_for_term(class_name, term, year, include_archived)
        summary = []
        cleared_list = []
        not_cleared_list = []
        archived_list = []

        for pupil in pupils:
            pupil_id = pupil.get('id')
            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)
            sponsor_reason = pupil.get("sponsor_reason", "")
            is_archived = pupil.get("archived", False)
            pupil_type = pupil.get("pupil_type", "Community Child")

            if is_sponsored:
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = self.get_ledger(pupil_id, term, year)
            total_paid = sum([p.get("amount", 0) for p in payments])

            credit_amount = abs(previous_balance) if previous_balance < 0 else 0
            effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

            total_due = effective_previous + term_fees
            balance = max(0, total_due - total_paid - credit_amount)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if is_sponsored:
                    status = f"Sponsored - {sponsor_reason}"

            pupil_info = {
                "Name": pupil["name"],
                "Pupil Type": pupil_type,
                "Enrolled": f"{pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', year)}",
                "Previous Bal (UGX)": previous_balance,
                "Credit (UGX)": credit_amount if credit_amount > 0 else 0,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if is_sponsored else "",
            }
            summary.append(pupil_info)

            if is_archived:
                archived_list.append(pupil_info)
            elif balance == 0 or is_sponsored:
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
        """Get school-wide summary as DataFrames"""
        cache_key = f"summary_{term}_{year}_{include_archived}"
        cached_result = cache.get(cache_key, "summary")
        if cached_result is not None:
            return cached_result

        all_pupils = self.get_all_pupils(include_archived)
        all_summaries = []
        staff_summaries = []
        shepherd_summaries = []
        community_summaries = []

        for pupil in all_pupils:
            pupil_id = pupil.get('id')
            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)
            sponsor_reason = pupil.get("sponsor_reason", "")
            is_archived = pupil.get("archived", False)
            pupil_type = pupil.get("pupil_type", "Community Child")

            if is_sponsored:
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = self.get_ledger(pupil_id, term, year)
            total_paid = sum([p.get("amount", 0) for p in payments])

            credit_amount = abs(previous_balance) if previous_balance < 0 else 0
            effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

            total_due = effective_previous + term_fees
            balance = max(0, total_due - total_paid - credit_amount)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if is_sponsored:
                    status = f"Sponsored - {sponsor_reason}"

            record = {
                "Class": pupil["class"],
                "Name": pupil["name"],
                "Pupil Type": pupil_type,
                "Enrolled": f"{pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', year)}",
                "Credit (UGX)": credit_amount if credit_amount > 0 else 0,
                "Term Fees (UGX)": term_fees,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
            }
            all_summaries.append(record)

            if pupil_type == "Staff Child" and not is_archived:
                staff_summaries.append(record)
            elif pupil_type == "Shepherd Child" and not is_archived:
                shepherd_summaries.append(record)
            elif pupil_type == "Community Child" and not is_archived:
                community_summaries.append(record)

        df_all = pd.DataFrame(all_summaries).reset_index(drop=True)
        df_staff = pd.DataFrame(staff_summaries).reset_index(drop=True)
        df_shepherd = pd.DataFrame(shepherd_summaries).reset_index(drop=True)
        df_community = pd.DataFrame(community_summaries).reset_index(drop=True)

        if not df_all.empty:
            df_all.insert(0, "No.", range(1, len(df_all) + 1))

        result = (df_all, df_staff, df_shepherd, df_community)
        cache.set(cache_key, result, "summary")
        return result

    def get_dashboard_stats(self, term, year):
        """Get dashboard statistics with caching"""
        cache_key = f"stats_{term}_{year}"
        cached = cache.get(cache_key, "stats")
        if cached is not None:
            return cached

        all_pupils = self.get_all_pupils(include_archived=False)

        stats = {
            "total_pupils": len(all_pupils),
            "staff_children": 0,
            "shepherd_children": 0,
            "community_children": 0,
            "total_expected": 0,
            "total_collected": 0,
            "total_balance": 0,
            "collection_rate": 0
        }

        for pupil in all_pupils:
            pupil_type = pupil.get("pupil_type", "Community Child")
            term_fees = pupil.get("term_fees", 0)
            is_sponsored = pupil.get("is_sponsored", False)

            if is_sponsored:
                term_fees = 0

            if pupil_type == "Staff Child":
                stats["staff_children"] += 1
            elif pupil_type == "Shepherd Child":
                stats["shepherd_children"] += 1
            else:
                stats["community_children"] += 1

            stats["total_expected"] += term_fees

            pupil_id = pupil.get('id')
            payments = self.get_ledger(pupil_id, term, year)
            total_paid = sum([p.get("amount", 0) for p in payments])
            stats["total_collected"] += total_paid

        stats["total_balance"] = stats["total_expected"] - stats["total_collected"]
        if stats["total_expected"] > 0:
            stats["collection_rate"] = (stats["total_collected"] / stats["total_expected"]) * 100

        cache.set(cache_key, stats, "stats")
        return stats


# ==================== LOGIN PAGE ====================
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
                <img src="data:{mime_type};base64,{logo_base64}" height="150" style="border-radius: 10px;">
                <div>
                    <h3 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h3>
                    <p style="color: #6C757D; margin: 2px 0 0 0; font-size: 0.8rem;">School Fees Management System</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; margin-top: 0px;">
                <div style="background: linear-gradient(135deg, #1E3A5F, #2E5A8A); border-radius: 10px; width: 70px; height: 70px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 1.8rem;">🏫</span>
                </div>
                <div>
                    <h3 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h3>
                    <p style="color: #6C757D; margin: 2px 0 0 0; font-size: 0.8rem;">School Fees Management System</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Create default users if none exist
        try:
            users_ref = db.collection("users")
            if len(list(users_ref.stream())) == 0:
                users_ref.document("bursar").set({
                    "username": "bursar",
                    "password": hash_password("bursar123"),
                    "role": "bursar",
                    "full_name": "School Bursar",
                    "created_at": datetime.datetime.now()
                })
                users_ref.document("admin").set({
                    "username": "admin",
                    "password": hash_password("admin123"),
                    "role": "admin",
                    "full_name": "School Administrator",
                    "created_at": datetime.datetime.now()
                })
        except:
            pass

        with st.form(key="login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    try:
                        users_ref = db.collection("users")
                        user_doc = users_ref.document(username).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            if user_data.get("password") == hash_password(password):
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.role = user_data.get("role", "admin")
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                        else:
                            st.error("Invalid username or password")
                    except Exception as e:
                        st.error(f"Authentication error: {str(e)}")


# ==================== MAIN APP ====================
def main_app():
    display_main_header()

    with st.sidebar:
        role = st.session_state["role"]

        profile_image_path = "jane.jpg"
        if os.path.exists(profile_image_path):
            with open(profile_image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{img_data}" 
                     style="width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 3px solid #A8B56C; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <div style="width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, #A8B56C, #6B7B3A); display: flex; align-items: center; justify-content: center;">
                    <span style="color: white; font-size: 1.8rem;">👤</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 5px;">
            <p style="font-weight: 600; font-size: 0.9rem; margin: 0; color: white;">Tukei Christine</p>
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
        current_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.datetime.now().year, step=1)

        st.markdown("---")

        # Term Enrollment Section (MOVED HERE - AFTER current_term/current_year are defined)
        if role == "bursar":
            st.markdown("### 📋 Term Enrollment")

            # Determine previous term
            term_order_list = ["Term 1", "Term 2", "Term 3"]
            try:
                current_idx = term_order_list.index(current_term)
            except:
                current_idx = 0

            if current_idx == 0:  # Term 1
                prev_term = "Term 3"
                prev_year = current_year - 1
            else:
                prev_term = term_order_list[current_idx - 1]
                prev_year = current_year

            st.caption(f"Enroll pupils from {prev_term} {prev_year} into {current_term} {current_year}")

            if st.button("📝 Enroll Previous Term Pupils", use_container_width=True, key="enroll_prev_btn"):
                st.session_state.show_enrollment_dialog = True
                st.session_state.enroll_from_term = prev_term
                st.session_state.enroll_from_year = prev_year
                st.session_state.enroll_to_term = current_term
                st.session_state.enroll_to_year = current_year
                st.rerun()
            st.markdown("---")

        # Show enrollment dialog if flag is set (ALSO MOVED HERE)
        if st.session_state.get("show_enrollment_dialog", False):
            with st.expander("📋 Enroll Pupils", expanded=True):
                # Get pupils from previous term
                prev_pupils = manager.get_pupils_for_term("All Classes",
                                                          st.session_state.enroll_from_term,
                                                          st.session_state.enroll_from_year,
                                                          include_archived=False)

                st.subheader(
                    f"Enroll from {st.session_state.enroll_from_term} {st.session_state.enroll_from_year} to {st.session_state.enroll_to_term} {st.session_state.enroll_to_year}")

                selected_pupils = []
                for pupil in prev_pupils:
                    # Check if already enrolled in current term
                    term_key = f"{st.session_state.enroll_to_year}_{st.session_state.enroll_to_term}"
                    enrollments = pupil.get("term_enrollments", {})
                    already_enrolled = enrollments.get(term_key, {}).get("active", False)

                    if already_enrolled:
                        st.info(f"✅ {pupil['name']} ({pupil['class']}) - Already enrolled")
                    else:
                        if st.checkbox(f"Enroll {pupil['name']} ({pupil['class']})", key=f"enroll_{pupil['id']}"):
                            selected_pupils.append(pupil)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Enroll Selected ({len(selected_pupils)} pupils)", use_container_width=True):
                        for pupil in selected_pupils:
                            manager.enroll_pupil_into_term(pupil['id'],
                                                           st.session_state.enroll_to_term,
                                                           st.session_state.enroll_to_year)
                        st.success(
                            f"✅ Enrolled {len(selected_pupils)} pupils into {st.session_state.enroll_to_term} {st.session_state.enroll_to_year}")
                        st.session_state.show_enrollment_dialog = False
                        cache.clear_all()
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_enrollment_dialog = False
                        st.rerun()

        if role == "bursar" and menu in ["Pupils & Ledgers", "Class Reports", "School Reports"]:
            show_archived = st.checkbox("Show Archived Pupils", value=st.session_state.show_archived,
                                        key="show_archived_checkbox")
            st.session_state.show_archived = show_archived

        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            for key in ["logged_in", "username", "role", "navigation_menu", "show_archived"]:
                if key in st.session_state:
                    del st.session_state[key]
            cache.clear_all()
            st.rerun()

        st.markdown("---")

        if role == "bursar" and menu in ["Pupils & Ledgers", "Class Reports", "School Reports"]:
            show_archived = st.checkbox("Show Archived Pupils", value=st.session_state.show_archived,
                                        key="show_archived_checkbox")
            st.session_state.show_archived = show_archived

        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            for key in ["logged_in", "username", "role", "navigation_menu", "show_archived"]:
                if key in st.session_state:
                    del st.session_state[key]
            cache.clear_all()
            st.rerun()

    manager = FeesManager()

    # ------------------- DASHBOARD -------------------
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #1E3A5F; margin-bottom: 0.5rem; font-size: 1.3rem;'>Dashboard</h2>",
                    unsafe_allow_html=True)

        stats = manager.get_dashboard_stats(current_term, current_year)

        # Row 1 - Compact Cards
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 1.6rem; font-weight: 700; color: #1E3A5F; margin: 0;">{stats['total_pupils']}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Total Pupils</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 1.6rem; font-weight: 700; color: #17A2B8; margin: 0;">{stats['staff_children']}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Staff Children</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 1.6rem; font-weight: 700; color: #20B2AA; margin: 0;">{stats['shepherd_children']}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Shepherd Children</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 1.6rem; font-weight: 700; color: #6C757D; margin: 0;">{stats['community_children']}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Community Children</p>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 0.9rem; font-weight: 700; color: #28A745; margin: 0;">UGX {stats['total_collected']:,.0f}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Total Collected</p>
            </div>
            """, unsafe_allow_html=True)

        with col6:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 1.6rem; font-weight: 700; color: #1E3A5F; margin: 0;">{stats['collection_rate']:.1f}%</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Collection Rate</p>
            </div>
            """, unsafe_allow_html=True)

        # Row 2 - Compact Cards
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 0.9rem; font-weight: 700; color: #1E3A5F; margin: 0;">UGX {stats['total_expected']:,.0f}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Total Expected</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 8px; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.05);">
                <p style="font-size: 0.9rem; font-weight: 700; color: #DC3545; margin: 0;">UGX {stats['total_balance']:,.0f}</p>
                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Total Balance</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            if stats["collection_rate"] > 0:
                st.progress(stats["collection_rate"] / 100)
                st.caption(f"📊 Progress: {stats['collection_rate']:.0f}%")

        st.markdown("---")
        st.markdown("<h3 style='font-size: 1.1rem;'>Quick Actions</h3>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Enroll New Pupil", use_container_width=True):
                st.session_state.navigation_menu = "Enroll Pupil"
                st.rerun()
        with col2:
            if st.button("💰 Record Payment", use_container_width=True):
                st.session_state.navigation_menu = "Record Payment"
                st.rerun()

    # ------------------- ENROLL PUPIL -------------------
    elif menu == "Enroll Pupil" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>Enroll New Pupil</h1>", unsafe_allow_html=True)
        st.caption(f"Enrolling for: **{current_term} {current_year}**")

        col1, col2 = st.columns(2)
        with col1:
            pupil_name = st.text_input("Full Name *", placeholder="Enter pupil's full name", key="enroll_name")
            pupil_class = st.selectbox("Class *", manager.classes, key="enroll_class")
            pupil_type = st.selectbox("Pupil Type *", manager.pupil_types, key="enroll_type")
        with col2:
            term_fees = st.number_input("Fees Per Term (UGX)", min_value=0, step=0, value=500000, key="enroll_fees",
                                        disabled=(pupil_type == "Shepherd Child"))
            if pupil_type == "Shepherd Child":
                st.info("🙏 Shepherd Child - No fees required")
            elif pupil_type == "Staff Child":
                st.info("👩‍🏫 Staff Child - Enter fees (can be 0)")

        if st.button("Enroll Pupil", use_container_width=True):
            if pupil_name:
                actual_fees = 0 if pupil_type == "Shepherd Child" else term_fees
                pupil_id = manager.enroll_pupil(pupil_name, pupil_class, actual_fees, pupil_type, current_term,
                                                current_year)
                if pupil_id:
                    st.success(f"✅ {pupil_name} enrolled as {pupil_type} for {current_term} {current_year}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Please enter pupil name")

    # ------------------- PUPILS & LEDGERS -------------------
    elif menu == "Pupils & Ledgers":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>Pupils & Ledgers</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(f"Showing **{current_term}, {current_year}** (INCLUDING ARCHIVED)")
        else:
            st.info(f"Showing **{current_term}, {current_year}** (Active pupils only)")

        col_class, col_search = st.columns([1, 2])
        with col_class:
            selected_class = st.selectbox("Select Class", manager.classes, key="ledger_class")
        with col_search:
            search_term = st.text_input("Search Pupil", placeholder="Type name to search...")

        pupils = manager.get_pupils_for_term(selected_class, current_term, current_year,
                                             include_archived=st.session_state.show_archived)
        if search_term:
            pupils = [p for p in pupils if search_term.lower() in p.get("name", "").lower()]

        if not pupils:
            st.info(f"No pupils found in {selected_class} for {current_term} {current_year}")
        else:
            st.markdown(f"### {len(pupils)} pupil(s) in {selected_class}")

            for pupil in pupils:
                pupil_id = pupil.get('id')
                is_archived = pupil.get("archived", False)
                term_fees = pupil.get("term_fees", 0)
                is_sponsored = pupil.get("is_sponsored", False)
                sponsor_reason = pupil.get("sponsor_reason", "")
                pupil_type = pupil.get("pupil_type", "Community Child")
                enrollment_info = f"{pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', current_year)}"

                previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                ledger_entries = manager.get_ledger(pupil_id, current_term, current_year)
                total_paid_this_term = sum([p.get("amount", 0) for p in ledger_entries])

                credit_amount = abs(previous_balance) if previous_balance < 0 else 0
                effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

                total_due = effective_previous + term_fees
                current_balance = max(0, total_due - total_paid_this_term - credit_amount)

                all_transactions = []

                # Show credit from previous term
                if credit_amount > 0:
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
                        "Credit Applied": f"UGX {credit_amount:,.0f}",
                        "Description": "Credit balance carried forward",
                        "Balance After": f"UGX {max(0, total_due - credit_amount):,.0f}",
                        "Receipt No": "N/A"
                    })

                for idx, entry in enumerate(ledger_entries, 1):
                    all_transactions.append({
                        "S/No": idx,
                        "Date": entry.get("date", "")[:10] if entry.get("date") else "",
                        "Amount Paid": f"UGX {entry.get('amount', 0):,.0f}",
                        "Credit Applied": "UGX 0",
                        "Description": entry.get("description", "Payment"),
                        "Balance After": f"UGX {entry.get('balance', 0):,.0f}",
                        "Receipt No": entry.get("receipt_no", "")
                    })

                if is_archived:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — [ARCHIVED]"
                elif is_sponsored:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — 🎓 SPONSORED"
                else:
                    if credit_amount > 0:
                        expander_title = f"📌 {pupil['name']} — {pupil_type} — 💳 Credit: UGX {credit_amount:,.0f} | Due: UGX {current_balance:,.0f}"
                    else:
                        expander_title = f"📌 {pupil['name']} — {pupil_type} — Fees: UGX {term_fees:,.0f} | Paid: UGX {total_paid_this_term:,.0f} | Balance: UGX {current_balance:,.0f}"

                with st.expander(expander_title):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.caption(f"📅 Enrolled: {enrollment_info}")
                    with col2:
                        st.caption(f"🏷️ Type: {pupil_type}")
                    with col3:
                        if is_sponsored:
                            st.caption(f"🙏 Reason: {sponsor_reason}")
                    with col4:
                        if credit_amount > 0:
                            st.success(f"💳 Credit: UGX {credit_amount:,.0f}")

                    if all_transactions:
                        df = pd.DataFrame(all_transactions)
                        st.dataframe(df, use_container_width=True, height=min(400, 35 * len(df) + 38))

                        if ledger_entries:
                            st.markdown("---")
                            st.markdown("### 📄 Receipts")
                            for entry in ledger_entries:
                                if st.button(f"🖨️ Receipt {entry.get('receipt_no', '')[-12:]}",
                                             key=f"print_{entry.get('id', '')}"):
                                    pdf_buffer = generate_pdf_receipt(
                                        school_name="Shepherd Academy Busiu",
                                        logo_path="images.jfif" if os.path.exists("images.jfif") else "",
                                        receipt_num=entry.get('receipt_no', ''),
                                        date_str=entry.get('date', '')[:10],
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
                                                       f"Receipt_{entry.get('receipt_no', '')}.pdf", "application/pdf")
                    else:
                        st.info(f"No payments for {current_term} {current_year}")

                    if role == "bursar" and not is_sponsored and not is_archived:
                        if st.button(f"💰 Record Payment for {pupil['name']}", key=f"pay_{pupil_id}",
                                     use_container_width=True):
                            st.session_state.navigation_menu = "Record Payment"
                            st.session_state.quick_pay_pupil = pupil_id
                            st.session_state.quick_pay_name = pupil['name']
                            st.rerun()

    # ------------------- RECORD PAYMENT -------------------
    elif menu == "Record Payment" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>Record Payment</h1>", unsafe_allow_html=True)
        st.caption(f"Recording for: **{current_term} {current_year}**")

        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.warning("No active pupils found.")
        else:
            col_filter1, col_filter2 = st.columns([1, 2])
            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_payment_class")
            with col_filter2:
                search_term = st.text_input("Search by Name", placeholder="Type name...", key="search_payment_pupil")

            pupil_dicts = [p for p in all_pupils if p.get("active", True) and not p.get("archived", False)]

            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]
            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning("No pupils found")
            else:
                pupil_options = {f"{p['name']} ({p['class']})": p['id'] for p in pupil_dicts}

                if "quick_pay_pupil" in st.session_state:
                    pupil_id = st.session_state.quick_pay_pupil
                    pupil_name = st.session_state.quick_pay_name
                    selected_pupil = next((p for p in pupil_dicts if p['id'] == pupil_id), None)
                    if not selected_pupil:
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
                    is_sponsored = pupil_data.get("is_sponsored", False)
                    pupil_type = pupil_data.get("pupil_type", "Community Child")

                    if is_sponsored:
                        st.warning("This is a sponsored child. No payment required.")
                    else:
                        previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                        existing_payments = manager.get_ledger(pupil_id, current_term, current_year)
                        total_paid_this_term = sum([p.get("amount", 0) for p in existing_payments])

                        credit_amount = abs(previous_balance) if previous_balance < 0 else 0
                        effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

                        total_due = effective_previous + term_fees
                        current_balance = max(0, total_due - total_paid_this_term - credit_amount)

                        col1, col2, col3, col4, col5 = st.columns(5)

                        with col1:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Name</p>
                                <p style="font-size: 0.8rem; font-weight: 600; color: #1E3A5F; margin: 0; word-break: break-word;">{pupil_name[:18] + '...' if len(pupil_name) > 18 else pupil_name}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col2:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Class</p>
                                <p style="font-size: 0.8rem; font-weight: 600; color: #1E3A5F; margin: 0;">{pupil_data['class']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col3:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Type</p>
                                <p style="font-size: 0.8rem; font-weight: 600; color: #1E3A5F; margin: 0;">{pupil_type}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col4:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Term Fees</p>
                                <p style="font-size: 0.75rem; font-weight: 700; color: #1E3A5F; margin: 0;">UGX {term_fees:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col5:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                <p style="font-size: 0.7rem; color: #6C757D; margin: 0;">Due This Term</p>
                                <p style="font-size: 0.75rem; font-weight: 700; color: {'#DC3545' if current_balance > 0 else '#28A745'}; margin: 0;">UGX {current_balance:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        if credit_amount > 0:
                            st.success(f"✅ **Credit Available: UGX {credit_amount:,.0f}**")
                            st.caption(f"👉 This credit will be automatically deducted from this term's fees")
                        if effective_previous > 0:
                            st.warning(f"⚠️ **Balance carried forward: UGX {effective_previous:,.0f}**")

                        st.markdown("---")

                        col1, col2 = st.columns(2)
                        with col1:
                            amount_paid = st.number_input("Amount (UGX)", min_value=0, value=0, key="payment_amount")
                        with col2:
                            description = st.text_input("Description", "Term Fees Payment", key="payment_description")

                        if st.button("💸 Process Payment & Generate Receipt", use_container_width=True):
                            if amount_paid <= 0:
                                st.error("Amount must be greater than zero")
                            else:
                                trans_id, new_balance, receipt_no, prev_bal, excess_amount = manager.add_payment(
                                    pupil_id, current_term, current_year, amount_paid, description)
                                if trans_id:
                                    if excess_amount > 0:
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded!")
                                        st.info(f"💰 Excess of UGX {excess_amount:,.0f} carried to next term!")
                                    else:
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded!")

                                    pdf_buffer = generate_pdf_receipt(
                                        school_name="Shepherd Academy Busiu",
                                        logo_path="images.jfif" if os.path.exists("images.jfif") else "",
                                        receipt_num=receipt_no,
                                        date_str=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        child_name=pupil_name,
                                        amount=amount_paid,
                                        description=f"{description} - {current_term} {current_year}",
                                        balance=new_balance,
                                        previous_balance=prev_bal,
                                        term_fees=term_fees,
                                        signature_text="Bursar's Signature",
                                        excess_amount=excess_amount
                                    )
                                    st.download_button("📥 Download Receipt", pdf_buffer, f"Receipt_{receipt_no}.pdf",
                                                       "application/pdf")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()

    # ------------------- CLASS REPORTS -------------------
    elif menu == "Class Reports":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>Class Fee Reports</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(f"Showing **{current_term}, {current_year}** (INCLUDING ARCHIVED)")
        else:
            st.info(f"Showing **{current_term}, {current_year}**")

        col1, col2 = st.columns(2)
        with col1:
            selected_class = st.selectbox("Select Class", manager.classes, key="summary_class")
        with col2:
            report_type = st.radio("View", ["All Pupils", "Cleared Only", "With Balance", "Archived Only"],
                                   horizontal=True)

        if st.button("Generate Report", use_container_width=True):
            df_full, df_cleared, df_not_cleared, df_archived = manager.get_class_summary(
                selected_class, current_term, current_year, include_archived=st.session_state.show_archived)

            if report_type == "All Pupils":
                df_to_show = df_full
            elif report_type == "Cleared Only":
                df_to_show = df_cleared
            elif report_type == "With Balance":
                df_to_show = df_not_cleared
            else:
                df_to_show = df_archived

            if not df_to_show.empty:
                st.dataframe(df_to_show, use_container_width=True)

                st.markdown("---")
                st.subheader("Export Options")
                col1, col2, col3 = st.columns(3)
                with col1:
                    csv = df_to_show.to_csv(index=False).encode()
                    st.download_button("📊 CSV", csv, f"{selected_class}_{current_term}_{current_year}_report.csv",
                                       "text/csv")
                with col2:
                    excel_data = {"Summary": df_full, "Cleared": df_cleared, "With Balance": df_not_cleared,
                                  "Archived": df_archived}
                    st.download_button("📘 Excel", export_to_excel(excel_data, "report.xlsx"),
                                       f"{selected_class}_{current_term}_{current_year}_report.xlsx")
                with col3:
                    pdf_buffer = export_summary_to_pdf(df_to_show, f"{selected_class} Report", "report.pdf")
                    st.download_button("📄 PDF", pdf_buffer,
                                       f"{selected_class}_{current_term}_{current_year}_report.pdf", "application/pdf")

    # ------------------- SCHOOL REPORTS -------------------
    elif menu == "School Reports":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>School-Wide Reports</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(f"Showing **{current_term}, {current_year}** (INCLUDING ARCHIVED)")
        else:
            st.info(f"Showing **{current_term}, {current_year}**")

        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            filter_type = st.selectbox("Filter by Type", ["All", "Staff Child", "Shepherd Child", "Community Child"],
                                       key="filter_type")
        with col_filter2:
            filter_status = st.selectbox("Filter by Status", ["All", "Cleared", "Not Cleared"], key="filter_status")

        if st.button("Generate School Summary", key="school_summary"):
            df_all, df_staff, df_shepherd, df_community = manager.get_school_wide_summary(
                current_term, current_year, include_archived=st.session_state.show_archived)

            if filter_type == "Staff Child":
                df_to_show = df_staff
            elif filter_type == "Shepherd Child":
                df_to_show = df_shepherd
            elif filter_type == "Community Child":
                df_to_show = df_community
            else:
                df_to_show = df_all

            if filter_status != "All" and not df_to_show.empty:
                df_to_show = df_to_show[df_to_show["Status"] == filter_status]

            if not df_to_show.empty:
                st.dataframe(df_to_show, use_container_width=True)

                st.markdown("---")
                st.subheader("Export Options")
                csv = df_to_show.to_csv(index=False).encode()
                st.download_button("📊 Download CSV", csv, f"school_wide_{current_term}_{current_year}.csv", "text/csv")

    # ------------------- MANAGE PUPILS -------------------
    elif menu == "Manage Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>Manage Pupils</h1>", unsafe_allow_html=True)

        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.info("No active pupils found")
        else:
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_manage_class")
            with col_filter2:
                filter_type = st.selectbox("Filter by Type",
                                           ["All", "Staff Child", "Shepherd Child", "Community Child"],
                                           key="filter_manage_type")
            with col_filter3:
                search_term = st.text_input("Search", placeholder="Type name...", key="search_pupil")

            pupil_dicts = [p for p in all_pupils]

            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]
            if filter_type != "All":
                pupil_dicts = [p for p in pupil_dicts if p.get("pupil_type", "Community Child") == filter_type]
            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning("No pupils found")
            else:
                st.markdown(f"### {len(pupil_dicts)} pupil(s)")

                for pupil in pupil_dicts:
                    pupil_type = pupil.get("pupil_type", "Community Child")
                    with st.expander(
                            f"📌 {pupil['name']} - {pupil['class']} (Fees: UGX {pupil.get('term_fees', 0):,.0f})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            **Info:**
                            - **Name:** {pupil['name']}
                            - **Class:** {pupil['class']}
                            - **Type:** {pupil_type}
                            - **Enrolled:** {pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', '2024')}
                            """)
                        with col2:
                            total_paid_all = 0
                            for term in ["Term 1", "Term 2", "Term 3"]:
                                payments = manager.get_ledger(pupil['id'], term, 2024)
                                term_paid = sum([p.get("amount", 0) for p in payments])
                                total_paid_all += term_paid
                                if term_paid > 0:
                                    st.write(f"- {term}: UGX {term_paid:,.0f}")
                            st.write(f"**Total Paid:** UGX {total_paid_all:,.0f}")

                        st.markdown("---")
                        with st.form(key=f"edit_form_{pupil['id']}"):
                            new_name = st.text_input("Name", pupil['name'], key=f"name_{pupil['id']}")
                            new_class = st.selectbox("Class", manager.classes,
                                                     index=manager.classes.index(pupil['class']) if pupil[
                                                                                                        'class'] in manager.classes else 0,
                                                     key=f"class_{pupil['id']}")
                            new_type = st.selectbox("Type", manager.pupil_types, index=manager.pupil_types.index(
                                pupil_type) if pupil_type in manager.pupil_types else 0, key=f"type_{pupil['id']}")

                            default_fees = 0 if new_type == "Shepherd Child" else pupil.get('term_fees', 0)
                            new_fees = st.number_input("Term Fees", value=int(default_fees), step=50000,
                                                       key=f"fees_{pupil['id']}",
                                                       disabled=(new_type == "Shepherd Child"))

                            col_edit, col_archive = st.columns(2)
                            with col_edit:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    manager.update_pupil(pupil['id'], new_name, new_class, new_fees, new_type)
                                    st.success("Updated!")
                                    st.rerun()
                            with col_archive:
                                leaving_reason = st.text_area("Archive Reason", placeholder="Reason for leaving",
                                                              key=f"leaving_{pupil['id']}")
                                if st.form_submit_button("📦 Archive Pupil", use_container_width=True):
                                    if leaving_reason:
                                        manager.archive_pupil(pupil['id'], leaving_reason)
                                        st.warning(f"✅ {pupil['name']} archived")
                                        st.rerun()
                                    else:
                                        st.error("Please provide a reason")

    # ------------------- ARCHIVED PUPILS -------------------
    elif menu == "Archived Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F; font-size: 1.5rem;'>Archived Pupils</h1>", unsafe_allow_html=True)

        archived_pupils = manager.get_archived_pupils()

        if not archived_pupils:
            st.info("No archived pupils found")
        else:
            for pupil in archived_pupils:
                with st.expander(
                        f"📌 {pupil['name']} - {pupil['class']} (Left: {pupil.get('leaving_date', 'Unknown')[:10]})"):
                    st.markdown(f"**Reason:** {pupil.get('leaving_reason', 'Not specified')}")

                    col1, col2 = st.columns(2)
                    with col1:
                        return_term = st.selectbox("Return Term", ["Term 1", "Term 2", "Term 3"],
                                                   key=f"return_term_{pupil['id']}")
                    with col2:
                        return_year = st.number_input("Return Year", value=current_year,
                                                      key=f"return_year_{pupil['id']}")

                    if st.button(f"🔄 Restore Pupil", key=f"restore_{pupil['id']}"):
                        if manager.restore_pupil(pupil['id'], return_term, return_year):
                            st.success(f"✅ {pupil['name']} restored to {return_term} {return_year}!")
                            st.rerun()


def main():
    if not st.session_state.get("logged_in", False):
        login_page()
    else:
        main_app()


if __name__ == "__main__":
    main()