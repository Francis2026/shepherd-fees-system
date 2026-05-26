import streamlit as st
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

# Import Supabase
from supabase import create_client

# ========== PAGE CONFIGURATION (MUST BE FIRST) ==========
st.set_page_config(
    page_title="Shepherd Academy | Fees Management",
    layout="wide",
    page_icon=":school:",
    initial_sidebar_state="expanded"
)

# ========== CRITICAL: Initialize session state ONCE ==========
if "app_initialized" not in st.session_state:
    st.session_state.app_initialized = True
    st.session_state.logged_in = False
    st.session_state.login_loaded = False
    st.session_state.navigation_menu = "Dashboard"
    st.session_state.show_archived = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.show_enrollment_dialog = False
    st.session_state.quick_pay_pupil = None
    st.session_state.quick_pay_name = ""

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


# ==================== SUPABASE INITIALIZATION ====================
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase connection error: {str(e)}")
        return None


supabase = init_supabase()


# ==================== ENHANCED CACHE SYSTEM ====================
class SmartCache:
    def __init__(self):
        self.cache = {}
        self.ttl_config = {
            "pupils": 1200,
            "ledger": 300,
            "stats": 600,
            "summary": 900,
        }

    def get(self, key, data_type="pupils"):
        if key in self.cache:
            data, timestamp = self.cache[key]
            ttl = self.ttl_config.get(data_type, 300)
            if datetime.datetime.now() - timestamp < timedelta(seconds=ttl):
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key, data, data_type="pupils"):
        self.cache[key] = (data, datetime.datetime.now())

    def invalidate(self, key=None, data_type=None):
        if key:
            self.cache.pop(key, None)
        elif data_type:
            keys_to_remove = [k for k in self.cache if k.startswith(data_type)]
            for k in keys_to_remove:
                self.cache.pop(k, None)
        else:
            self.cache.clear()

    def clear_all(self):
        self.cache.clear()


cache = SmartCache()


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

    # Ensure values are numbers (not None)
    previous_balance = previous_balance if previous_balance is not None else 0
    term_fees = term_fees if term_fees is not None else 0
    balance = balance if balance is not None else 0
    amount = amount if amount is not None else 0
    excess_amount = excess_amount if excess_amount is not None else 0

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
    "P7": None
}

TERM_ORDER = ["Term 1", "Term 2", "Term 3"]


# ==================== SUPABASE FEES MANAGER (COMPLETELY FIXED) ====================
class FeesManager:
    def __init__(self):
        self.classes = list(CLASS_PROGRESSION.keys())
        self.terms = ["Term 1", "Term 2", "Term 3"]
        self.term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
        self.pupil_types = ["Community Child", "Staff Child", "Shepherd Child"]

    def get_next_class(self, current_class):
        return CLASS_PROGRESSION.get(current_class, current_class)

    def get_all_pupils(self, include_archived=False):
        cache_key = f"pupils_all_{include_archived}"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        if supabase is None:
            return []

        try:
            query = supabase.table("pupils").select("*")
            if not include_archived:
                query = query.eq("active", True)
            result = query.execute()
            pupils = result.data
            cache.set(cache_key, pupils, "pupils")
            return pupils
        except Exception as e:
            st.error(f"Error fetching pupils: {str(e)}")
            return []

    def get_archived_pupils(self):
        cache_key = "pupils_archived"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        if supabase is None:
            return []

        try:
            result = supabase.table("pupils").select("*").eq("archived", True).execute()
            pupils = result.data
            cache.set(cache_key, pupils, "pupils")
            return pupils
        except:
            return []

    def get_pupils_by_class(self, class_name, include_archived=False):
        all_pupils = self.get_all_pupils(include_archived)
        return [p for p in all_pupils if p.get("class") == class_name]

    def get_pupils_for_term(self, class_name, term, year, include_archived=False):
        """ONLY show pupils who are ENROLLED in this specific term via term_enrollments table"""
        if supabase is None:
            return []

        try:
            # First, get all pupils enrolled in this term from term_enrollments
            result = supabase.table("term_enrollments") \
                .select("pupil_id, pupils(*)") \
                .eq("term", term) \
                .eq("year", year) \
                .eq("is_active", True) \
                .execute()

            pupils = []
            for item in result.data:
                pupil = item.get("pupils", {})
                if pupil:
                    # Check if class matches
                    if class_name == "All Classes" or pupil.get("class") == class_name:
                        if not include_archived and pupil.get("archived", False):
                            continue
                        pupils.append(pupil)

            return pupils
        except Exception as e:
            st.error(f"Error getting pupils for term: {str(e)}")
            return []

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
        """Get the closing balance from the previous term"""
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

        if supabase is None:
            return 0

        try:
            # Get the last payment of the previous term to get the closing balance
            result = supabase.table("payments").select("balance, excess_amount") \
                .eq("pupil_id", pupil_id) \
                .eq("term", prev_term) \
                .eq("year", prev_year) \
                .order("payment_date", desc=True) \
                .limit(1) \
                .execute()

            if result.data:
                last_entry = result.data[0]
                balance = last_entry.get("balance", 0)
                excess = last_entry.get("excess_amount", 0)

                # If balance is 0 but there's excess, return negative excess (credit)
                if balance == 0 and excess > 0:
                    return -excess
                return balance if balance is not None else 0
            return 0
        except:
            return 0

    def get_ledger(self, pupil_id, term, year):
        cache_key = f"ledger_{pupil_id}_{term}_{year}"
        cached = cache.get(cache_key, "ledger")
        if cached is not None:
            return cached

        if supabase is None:
            return []

        try:
            result = supabase.table("payments").select("*") \
                .eq("pupil_id", pupil_id) \
                .eq("term", term) \
                .eq("year", int(year)) \
                .order("payment_date") \
                .execute()
            payments = result.data
            cache.set(cache_key, payments, "ledger")
            return payments
        except:
            return []

    def enroll_pupil(self, name, class_name, term_fees, pupil_type, current_term, current_year):
        """Enroll a NEW pupil - automatically enrolls them in the current term"""
        if supabase is None:
            st.error("Database not connected")
            return None

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

            pupil_id = str(uuid.uuid4())

            pupil_data = {
                "id": pupil_id,
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "active": True,
                "archived": False,
                "enrollment_term": current_term,
                "enrollment_year": current_year,
                "current_term": current_term,
                "current_year": current_year
            }

            supabase.table("pupils").insert(pupil_data).execute()

            # Enroll in current term
            supabase.table("term_enrollments").insert({
                "pupil_id": pupil_id,
                "term": current_term,
                "year": current_year,
                "is_active": True
            }).execute()

            cache.invalidate(data_type="pupils")
            cache.invalidate(data_type="stats")
            return pupil_id
        except Exception as e:
            st.error(f"Error enrolling pupil: {str(e)}")
            return None

    def get_pupil_details(self, pupil_id):
        cache_key = f"pupil_{pupil_id}"
        cached = cache.get(cache_key, "pupils")
        if cached is not None:
            return cached

        if supabase is None:
            return None

        try:
            result = supabase.table("pupils").select("*").eq("id", pupil_id).execute()
            if result.data:
                pupil = result.data[0]
                cache.set(cache_key, pupil, "pupils")
                return pupil
            return None
        except:
            return None

    def update_pupil(self, pupil_id, name, class_name, term_fees, pupil_type):
        if supabase is None:
            return False

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

            supabase.table("pupils").update({
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason
            }).eq("id", pupil_id).execute()

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error updating pupil: {str(e)}")
            return False

    def archive_pupil(self, pupil_id, leaving_reason=""):
        if supabase is None:
            return False

        try:
            supabase.table("pupils").update({
                "active": False,
                "archived": True,
                "leaving_date": datetime.datetime.now().isoformat(),
                "leaving_reason": leaving_reason
            }).eq("id", pupil_id).execute()

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id, return_term, return_year):
        if supabase is None:
            return False

        try:
            supabase.table("pupils").update({
                "active": True,
                "archived": False,
                "current_term": return_term,
                "current_year": return_year
            }).eq("id", pupil_id).execute()

            supabase.table("term_enrollments").insert({
                "pupil_id": pupil_id,
                "term": return_term,
                "year": return_year,
                "is_active": True
            }).execute()

            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    def enroll_pupil_into_term(self, pupil_id, term, year):
        """Enroll a pupil from previous term into current term with balance carry-forward"""
        if supabase is None:
            return False

        try:
            # Check if already enrolled in this term
            existing = supabase.table("term_enrollments").select("*") \
                .eq("pupil_id", pupil_id) \
                .eq("term", term) \
                .eq("year", year) \
                .execute()

            if existing.data:
                return True  # Already enrolled

            # Get pupil details
            pupil = self.get_pupil_details(pupil_id)
            if not pupil:
                return False

            # Get previous term balance
            previous_balance = self.get_previous_term_balance(pupil_id, term, year)

            # Enroll in term
            supabase.table("term_enrollments").insert({
                "pupil_id": pupil_id,
                "term": term,
                "year": year,
                "is_active": True,
                "enrolled_at": datetime.datetime.now().isoformat()
            }).execute()

            # Update pupil's current term
            supabase.table("pupils").update({
                "current_term": term,
                "current_year": year
            }).eq("id", pupil_id).execute()

            # If there's a positive balance (debt), create an opening balance record
            if previous_balance > 0:
                term_fees = pupil.get("term_fees", 0)
                opening_id = str(uuid.uuid4())
                receipt_no = f"OPEN-BAL-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

                # Get the term order to create description
                term_order = self.term_order
                current_order = term_order.get(term, 1)
                if current_order == 1:
                    source_term = f"Term 3, {year - 1}"
                elif current_order == 2:
                    source_term = f"Term 1, {year}"
                else:
                    source_term = f"Term 2, {year}"

                supabase.table("payments").insert({
                    "id": opening_id,
                    "pupil_id": pupil_id,
                    "term": term,
                    "year": int(year),
                    "amount": 0,
                    "description": f"Opening balance carried forward from {source_term}",
                    "balance": previous_balance,
                    "previous_balance": previous_balance,
                    "term_fees": term_fees,
                    "receipt_no": receipt_no,
                    "excess_amount": 0,
                    "payment_date": datetime.datetime.now().isoformat()
                }).execute()

            cache.invalidate(data_type="pupils")
            cache.invalidate(data_type="ledger")
            cache.invalidate(data_type="summary")
            return True
        except Exception as e:
            st.error(f"Error enrolling pupil into term: {str(e)}")
            return False

    def add_payment(self, pupil_id, term, year, amount, description):
        if supabase is None:
            return None, "Database not connected", None, None, 0

        try:
            result = supabase.rpc("process_payment", {
                "p_pupil_id": pupil_id,
                "p_term": term,
                "p_year": int(year),
                "p_amount": amount,
                "p_description": description
            }).execute()

            data = result.data
            cache.invalidate(data_type="stats")
            cache.invalidate(data_type="summary")
            cache.invalidate(data_type="ledger")

            return (data.get('payment_id'), data.get('new_balance'),
                    data.get('receipt_no'), data.get('previous_balance'),
                    data.get('excess_amount'))
        except Exception as e:
            st.error(f"Error adding payment: {str(e)}")
            return None, str(e), None, None, 0

    def get_class_summary(self, class_name, term, year, include_archived=False):
        if supabase is None:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        try:
            result = supabase.rpc("get_class_summary", {
                "p_class": class_name,
                "p_term": term,
                "p_year": int(year),
                "p_include_archived": include_archived
            }).execute()

            summary_data = result.data
            df_summary = pd.DataFrame(summary_data).reset_index(drop=True)
            if not df_summary.empty:
                df_summary.insert(0, "No.", range(1, len(df_summary) + 1))

            df_cleared = df_summary[df_summary["status"] == "Cleared"] if not df_summary.empty else pd.DataFrame()
            df_not_cleared = df_summary[
                df_summary["status"] == "Not Cleared"] if not df_summary.empty else pd.DataFrame()
            df_archived = df_summary[
                df_summary["status"].str.contains("Archived", na=False)] if not df_summary.empty else pd.DataFrame()

            return df_summary, df_cleared, df_not_cleared, df_archived
        except Exception as e:
            st.error(f"Error getting class summary: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def get_school_wide_summary(self, term, year, include_archived=False):
        cache_key = f"school_summary_{term}_{year}_{include_archived}"
        cached = cache.get(cache_key, "summary")
        if cached is not None:
            return cached

        if supabase is None:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        try:
            all_summaries = []
            for class_name in self.classes:
                result = supabase.rpc("get_class_summary", {
                    "p_class": class_name,
                    "p_term": term,
                    "p_year": int(year),
                    "p_include_archived": include_archived
                }).execute()

                for row in result.data:
                    row["Class"] = class_name
                    all_summaries.append(row)

            df_all = pd.DataFrame(all_summaries).reset_index(drop=True)
            if not df_all.empty:
                df_all.insert(0, "No.", range(1, len(df_all) + 1))

            df_staff = df_all[df_all["pupil_type"] == "Staff Child"] if not df_all.empty else pd.DataFrame()
            df_shepherd = df_all[df_all["pupil_type"] == "Shepherd Child"] if not df_all.empty else pd.DataFrame()
            df_community = df_all[df_all["pupil_type"] == "Community Child"] if not df_all.empty else pd.DataFrame()

            result = (df_all, df_staff, df_shepherd, df_community)
            cache.set(cache_key, result, "summary")
            return result
        except:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def get_dashboard_stats(self, term, year):
        cache_key = f"stats_{term}_{year}"
        cached = cache.get(cache_key, "stats")
        if cached is not None:
            return cached

        if supabase is None:
            return {
                "total_pupils": 0,
                "staff_children": 0,
                "shepherd_children": 0,
                "community_children": 0,
                "total_expected": 0,
                "total_collected": 0,
                "total_balance": 0,
                "collection_rate": 0
            }

        try:
            # Get pupils enrolled in this specific term
            enrolled_pupils = []
            result = supabase.table("term_enrollments") \
                .select("pupil_id, pupils(*)") \
                .eq("term", term) \
                .eq("year", int(year)) \
                .eq("is_active", True) \
                .execute()

            for item in result.data:
                pupil = item.get("pupils", {})
                if pupil and not pupil.get("archived", False):
                    enrolled_pupils.append(pupil)

            stats = {
                "total_pupils": len(enrolled_pupils),
                "staff_children": 0,
                "shepherd_children": 0,
                "community_children": 0,
                "total_expected": 0,
                "total_collected": 0,
                "total_balance": 0,
                "collection_rate": 0
            }

            for pupil in enrolled_pupils:
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

                # Get total paid for this term
                result = supabase.table("payments").select("amount") \
                    .eq("pupil_id", pupil.get("id")) \
                    .eq("term", term) \
                    .eq("year", int(year)) \
                    .execute()

                total_paid = sum([p.get("amount", 0) for p in result.data])
                stats["total_collected"] += total_paid

            stats["total_balance"] = stats["total_expected"] - stats["total_collected"]
            if stats["total_expected"] > 0:
                stats["collection_rate"] = (stats["total_collected"] / stats["total_expected"]) * 100

            cache.set(cache_key, stats, "stats")
            return stats
        except Exception as e:
            st.error(f"Error getting dashboard stats: {str(e)}")
            return {
                "total_pupils": 0,
                "staff_children": 0,
                "shepherd_children": 0,
                "community_children": 0,
                "total_expected": 0,
                "total_collected": 0,
                "total_balance": 0,
                "collection_rate": 0
            }

# ==================== AUTHENTICATION ====================
def authenticate_user(username, password):
    if supabase is None:
        return None

    try:
        result = supabase.table("users").select("*").eq("username", username).execute()

        if result.data:
            user_data = result.data[0]
            stored_password = user_data.get("password", "")
            if stored_password == hash_password(password):
                return user_data.get("role", "admin")
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None


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
        current_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.datetime.now().year,
                                       step=1)

        st.markdown("---")

        # Term Enrollment Section
        if role == "bursar":
            st.markdown("### 📋 Term Enrollment")

            term_order_list = ["Term 1", "Term 2", "Term 3"]
            try:
                current_idx = term_order_list.index(current_term)
            except:
                current_idx = 0

            if current_idx == 0:
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

        manager = FeesManager()

        # Show enrollment dialog if flag is set
        if st.session_state.get("show_enrollment_dialog", False):
            with st.expander("📋 Enroll Pupils", expanded=True):
                prev_pupils = manager.get_pupils_for_term("All Classes",
                                                          st.session_state.enroll_from_term,
                                                          st.session_state.enroll_from_year,
                                                          include_archived=False)

                st.subheader(
                    f"Enroll from {st.session_state.enroll_from_term} {st.session_state.enroll_from_year} to {st.session_state.enroll_to_term} {st.session_state.enroll_to_year}")

                selected_pupils = []
                for pupil in prev_pupils:
                    # Check if already enrolled
                    try:
                        result = supabase.table("term_enrollments").select("*") \
                            .eq("pupil_id", pupil.get("id")) \
                            .eq("term", st.session_state.enroll_to_term) \
                            .eq("year", st.session_state.enroll_to_year) \
                            .execute()
                        already_enrolled = len(result.data) > 0
                    except:
                        already_enrolled = False

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
            show_archived = st.checkbox("Show Archived Pupils", value=st.session_state.get("show_archived", False),
                                        key="show_archived_checkbox")
            st.session_state.show_archived = show_archived

        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            for key in ["logged_in", "username", "role", "navigation_menu", "show_archived"]:
                if key in st.session_state:
                    del st.session_state[key]
            cache.clear_all()
            st.rerun()

    # ------------------- DASHBOARD -------------------
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #1E3A5F; margin-bottom: 0.5rem; font-size: 1.3rem;'>Dashboard</h2>",
                    unsafe_allow_html=True)

        stats = manager.get_dashboard_stats(current_term, current_year)

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

                # Handle None values
                if previous_balance is None:
                    previous_balance = 0

                previous_balance = previous_balance if previous_balance is not None else 0
                term_fees = term_fees if term_fees is not None else 0
                total_paid_this_term = total_paid_this_term if total_paid_this_term is not None else 0

                credit_amount = abs(previous_balance) if previous_balance < 0 else 0
                effective_previous = max(0, previous_balance) if previous_balance > 0 else 0

                total_due = effective_previous + term_fees
                current_balance = max(0, total_due - total_paid_this_term - credit_amount)

                all_transactions = []

                if credit_amount > 0:
                    term_order = manager.term_order[current_term]
                    if term_order == 1:
                        source_term = f"Term 3, {current_year - 1}"
                    elif term_order == 2:
                        source_term = f"Term 1, {current_year}"
                    else:
                        source_term = f"Term 2, {current_year}"

                    # Ensure values are numbers (not None)
                    credit_amt = credit_amount if credit_amount is not None else 0
                    total_due_amt = total_due if total_due is not None else 0

                    all_transactions.append({
                        "S/No": 0,
                        "Date": f"Credit from {source_term}",
                        "Amount Paid": "UGX 0",
                        "Credit Applied": f"UGX {credit_amt:,.0f}",
                        "Description": "Credit balance carried forward",
                        "Balance After": f"UGX {max(0, total_due_amt - credit_amt):,.0f}",
                        "Receipt No": "N/A"
                    })

                for idx, entry in enumerate(ledger_entries, 1):
                    # Safely get values, ensuring they are numbers
                    amount = entry.get('amount', 0)
                    if amount is None:
                        amount = 0

                    balance = entry.get('balance', 0)
                    if balance is None:
                        balance = 0

                    all_transactions.append({
                        "S/No": idx,
                        "Date": entry.get("payment_date", "")[:10] if entry.get("payment_date") else "",
                        "Amount Paid": f"UGX {amount:,.0f}",
                        "Credit Applied": "UGX 0",
                        "Description": entry.get("description", "Payment"),
                        "Balance After": f"UGX {balance:,.0f}",
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
                                        date_str=entry.get('payment_date', ''),
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

                        # Handle None values
                        if previous_balance is None:
                            previous_balance = 0

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

                # ========== CLASS SUMMARY STATISTICS ==========
                st.markdown("---")
                st.markdown("### 📊 Class Summary Statistics")

                # Filter out archived pupils for financial stats
                if report_type == "Archived Only":
                    financial_df = df_archived
                else:
                    financial_df = df_full[
                        df_full["status"] != "Archived (Left School)"] if not df_full.empty else pd.DataFrame()

                if not financial_df.empty:
                    # Use correct column names
                    total_pupils = len(financial_df)
                    total_expected = financial_df["term_fees"].sum() if "term_fees" in financial_df.columns else 0
                    total_paid = financial_df["total_paid"].sum() if "total_paid" in financial_df.columns else 0
                    total_balance = financial_df["balance"].sum() if "balance" in financial_df.columns else 0

                    cleared_count = len(
                        financial_df[financial_df["status"] == "Cleared"]) if "status" in financial_df.columns else 0
                    not_cleared_count = len(financial_df[financial_df[
                                                             "status"] == "Not Cleared"]) if "status" in financial_df.columns else 0

                    collection_rate = (total_paid / total_expected * 100) if total_expected > 0 else 0

                    # Display metrics using custom HTML (smaller fonts)
                    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)

                    with col_a:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 4px; text-align: center;">
                            <p style="font-size: 0.55rem; color: #6c757d; margin: 0;">📚 Pupils</p>
                            <p style="font-size: 0.9rem; font-weight: 600; color: #1E3A5F; margin: 0;">{total_pupils}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_b:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 4px; text-align: center;">
                            <p style="font-size: 0.55rem; color: #6c757d; margin: 0;">💰 Expected</p>
                            <p style="font-size: 0.65rem; font-weight: 600; color: #1E3A5F; margin: 0;">UGX {total_expected:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_c:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 4px; text-align: center;">
                            <p style="font-size: 0.55rem; color: #6c757d; margin: 0;">✅ Collected</p>
                            <p style="font-size: 0.65rem; font-weight: 600; color: #28A745; margin: 0;">UGX {total_paid:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_d:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 4px; text-align: center;">
                            <p style="font-size: 0.55rem; color: #6c757d; margin: 0;">⚠️ Balance</p>
                            <p style="font-size: 0.65rem; font-weight: 600; color: #DC3545; margin: 0;">UGX {total_balance:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_e:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 4px; text-align: center;">
                            <p style="font-size: 0.55rem; color: #6c757d; margin: 0;">🎯 Cleared</p>
                            <p style="font-size: 0.9rem; font-weight: 600; color: #28A745; margin: 0;">{cleared_count}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_f:
                        st.markdown(f"""
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 4px; text-align: center;">
                            <p style="font-size: 0.55rem; color: #6c757d; margin: 0;">❌ Not Cleared</p>
                            <p style="font-size: 0.9rem; font-weight: 600; color: #DC3545; margin: 0;">{not_cleared_count}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    if collection_rate > 0:
                        st.progress(collection_rate / 100)
                        st.caption(f"📈 Progress: {collection_rate:.1f}%")

                    st.markdown("---")

                    # ========== BREAKDOWN BY PUPIL TYPE ==========
                    st.markdown("#### 👥 Breakdown by Pupil Type")

                    if "pupil_type" in financial_df.columns:
                        category_stats = financial_df.groupby("pupil_type").agg({
                            "term_fees": "sum",
                            "total_paid": "sum",
                            "balance": "sum",
                            "name": "count"
                        }).rename(columns={"name": "count"})

                        if not category_stats.empty:
                            cat_col1, cat_col2, cat_col3 = st.columns(3)

                            for idx, (cat_type, row) in enumerate(category_stats.iterrows()):
                                cat_col = [cat_col1, cat_col2, cat_col3][idx % 3]
                                with cat_col:
                                    cat_rate = (row['total_paid'] / row['term_fees'] * 100) if row[
                                                                                                   'term_fees'] > 0 else 0

                                    st.markdown(f"""
                                    <div style="background: linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%); border-radius: 12px; padding: 12px; margin: 5px 0; border-left: 4px solid #1E3A5F;">
                                        <h4 style="color: #1E3A5F; margin: 0 0 8px 0; font-size: 1rem;">{cat_type}</h4>
                                        <p style="margin: 3px 0; font-size: 0.75rem;">👥 Count: {int(row['count'])}</p>
                                        <p style="margin: 3px 0; font-size: 0.75rem;">💰 Expected: UGX {row['term_fees']:,.0f}</p>
                                        <p style="margin: 3px 0; font-size: 0.75rem;">✅ Paid: UGX {row['total_paid']:,.0f}</p>
                                        <p style="margin: 3px 0; font-size: 0.75rem;">⚠️ Balance: UGX {row['balance']:,.0f}</p>
                                        <p style="margin: 3px 0; font-size: 0.75rem; font-weight: bold;">📊 Rate: {cat_rate:.1f}%</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                else:
                    st.info("No financial data available for this report")

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

        col_filter1, col_filter2, col_filter3 = st.columns(3)
        with col_filter1:
            filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes, key="filter_class_report")
        with col_filter2:
            filter_type = st.selectbox("Filter by Type", ["All", "Staff Child", "Shepherd Child", "Community Child"],
                                       key="filter_type_report")
        with col_filter3:
            filter_status = st.selectbox("Filter by Status", ["All", "Cleared", "Not Cleared", "Archived"],
                                         key="filter_status_report")

        if st.button("Generate School Summary", key="school_summary"):
            df_all, df_staff, df_shepherd, df_community = manager.get_school_wide_summary(
                current_term, current_year, include_archived=st.session_state.show_archived)


            # Apply filters
            if filter_class != "All Classes" and not df_all.empty:
                if "Class" in df_all.columns:
                    df_all = df_all[df_all["Class"] == filter_class]

            if filter_type == "Staff Child":
                df_to_show = df_staff
            elif filter_type == "Shepherd Child":
                df_to_show = df_shepherd
            elif filter_type == "Community Child":
                df_to_show = df_community
            else:
                df_to_show = df_all

            # Apply status filter - try different possible column names
            if not df_to_show.empty and filter_status != "All":
                # Check what column name exists
                status_col = None
                for col in ["Status", "status", "STATUS"]:
                    if col in df_to_show.columns:
                        status_col = col
                        break

                if status_col:
                    if filter_status == "Cleared":
                        df_to_show = df_to_show[df_to_show[status_col] == "Cleared"]
                    elif filter_status == "Not Cleared":
                        df_to_show = df_to_show[df_to_show[status_col] == "Not Cleared"]
                    elif filter_status == "Archived":
                        df_to_show = df_to_show[df_to_show[status_col] == "Archived (Left School)"]

            if not df_to_show.empty:
                st.dataframe(df_to_show, use_container_width=True)

                # ========== SCHOOL SUMMARY STATISTICS ==========
                st.markdown("---")
                st.markdown("### 📊 School-Wide Summary Statistics")

                # Add custom CSS for smaller metrics
                st.markdown("""
                <style>
                    div[data-testid="stMetric"] {
                        background-color: #f8f9fa;
                        border-radius: 10px;
                        padding: 6px;
                        text-align: center;
                    }
                    div[data-testid="stMetric"] label {
                        font-size: 0.65rem !important;
                        color: #6c757d !important;
                    }
                    div[data-testid="stMetric"] div {
                        font-size: 0.85rem !important;
                        font-weight: 600 !important;
                    }
                </style>
                """, unsafe_allow_html=True)

                # Filter out archived - find the correct column name
                financial_df = df_to_show.copy()
                if "Status" in financial_df.columns:
                    financial_df = financial_df[financial_df["Status"] != "Archived (Left School)"]
                elif "status" in financial_df.columns:
                    financial_df = financial_df[financial_df["status"] != "Archived (Left School)"]

                if not financial_df.empty:
                    # Determine column names dynamically
                    term_fees_col = "Term Fees (UGX)" if "Term Fees (UGX)" in financial_df.columns else "term_fees"
                    total_paid_col = "Total Paid (UGX)" if "Total Paid (UGX)" in financial_df.columns else "total_paid"
                    balance_col = "Balance (UGX)" if "Balance (UGX)" in financial_df.columns else "balance"
                    class_col = "Class" if "Class" in financial_df.columns else "class"
                    pupil_type_col = "Pupil Type" if "Pupil Type" in financial_df.columns else "pupil_type"
                    status_col_final = "Status" if "Status" in financial_df.columns else "status"

                    # Calculate totals
                    total_pupils = len(financial_df)
                    total_expected = financial_df[term_fees_col].sum()
                    total_paid = financial_df[total_paid_col].sum()
                    total_balance = financial_df[balance_col].sum()

                    # Count cleared/not cleared
                    cleared_count = len(financial_df[financial_df[status_col_final] == "Cleared"])
                    not_cleared_count = len(financial_df[financial_df[status_col_final] == "Not Cleared"])

                    collection_rate = (total_paid / total_expected * 100) if total_expected > 0 else 0

                    # Display metrics
                    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
                    with col_a:
                        st.metric("📚 Pupils", total_pupils)
                    with col_b:
                        st.metric("💰 Expected", f"UGX {total_expected:,.0f}")
                    with col_c:
                        st.metric("✅ Collected", f"UGX {total_paid:,.0f}")
                    with col_d:
                        st.metric("⚠️ Balance", f"UGX {total_balance:,.0f}")
                    with col_e:
                        st.metric("🎯 Cleared", cleared_count)
                    with col_f:
                        st.metric("❌ Not Cleared", not_cleared_count)

                    if collection_rate > 0:
                        st.progress(collection_rate / 100)
                        st.caption(f"📈 Collection Rate: {collection_rate:.1f}%")

                    st.markdown("---")

                    # ========== PERFORMANCE BY CLASS ==========
                    st.markdown("### 🏫 Performance by Class")

                    # Build class summary manually
                    class_summary_list = []
                    for class_name in financial_df[class_col].unique():
                        class_data = financial_df[financial_df[class_col] == class_name]
                        class_summary_list.append({
                            "Class": class_name,
                            "Pupils": len(class_data),
                            "Expected": class_data[term_fees_col].sum(),
                            "Collected": class_data[total_paid_col].sum(),
                            "Balance": class_data[balance_col].sum()
                        })

                    if class_summary_list:
                        class_summary_df = pd.DataFrame(class_summary_list)
                        class_summary_df["Rate"] = (
                                    class_summary_df["Collected"] / class_summary_df["Expected"] * 100).fillna(0).round(
                            1)
                        class_summary_df = class_summary_df.sort_values("Class")

                        st.dataframe(
                            class_summary_df.style.format({
                                "Expected": "UGX {:,.0f}",
                                "Collected": "UGX {:,.0f}",
                                "Balance": "UGX {:,.0f}",
                                "Rate": "{:.1f}%"
                            }),
                            use_container_width=True
                        )

                        if len(class_summary_df) > 1:
                            fig = px.bar(
                                class_summary_df,
                                x="Class",
                                y="Rate",
                                title="Collection Rate by Class",
                                color="Rate",
                                color_continuous_scale="RdYlGn",
                                text="Rate"
                            )
                            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=400)
                            st.plotly_chart(fig, use_container_width=True)

                    st.markdown("---")

                    # ========== PERFORMANCE BY CATEGORY ==========
                    st.markdown("### 👥 Performance by Pupil Category")

                    # Build category summary manually
                    category_summary_list = []
                    for cat_type in financial_df[pupil_type_col].unique():
                        cat_data = financial_df[financial_df[pupil_type_col] == cat_type]
                        category_summary_list.append({
                            "Category": cat_type,
                            "Pupils": len(cat_data),
                            "Expected": cat_data[term_fees_col].sum(),
                            "Collected": cat_data[total_paid_col].sum(),
                            "Balance": cat_data[balance_col].sum()
                        })

                    if category_summary_list:
                        category_summary_df = pd.DataFrame(category_summary_list)
                        category_summary_df["Rate"] = (
                                    category_summary_df["Collected"] / category_summary_df["Expected"] * 100).fillna(
                            0).round(1)

                        # Display in columns
                        cat_cols = st.columns(len(category_summary_df))
                        for idx, row in category_summary_df.iterrows():
                            with cat_cols[idx]:
                                st.markdown(f"""
                                <div style="background: #f8f9fa; border-radius: 10px; padding: 8px; text-align: center;">
                                    <p style="font-weight: 700; margin: 0; font-size: 0.75rem;">{row['Category']}</p>
                                    <p style="margin: 2px 0; font-size: 0.65rem;">👥 {int(row['Pupils'])}</p>
                                    <p style="margin: 2px 0; font-size: 0.6rem;">💰 UGX {row['Expected']:,.0f}</p>
                                    <p style="margin: 2px 0; font-size: 0.6rem;">✅ UGX {row['Collected']:,.0f}</p>
                                    <p style="margin: 2px 0; font-size: 0.6rem;">⚠️ UGX {row['Balance']:,.0f}</p>
                                    <p style="margin: 2px 0; font-size: 0.65rem; font-weight: 700;">📊 {row['Rate']:.1f}%</p>
                                </div>
                                """, unsafe_allow_html=True)

                        # Pie chart
                        fig2 = px.pie(
                            category_summary_df,
                            values="Pupils",
                            names="Category",
                            title="Pupil Distribution by Category",
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig2.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=350)
                        st.plotly_chart(fig2, use_container_width=True)

                    st.markdown("---")

                    # ========== TOP PERFORMING CLASSES ==========
                    if class_summary_list:
                        st.markdown("### 🏆 Top 5 Performing Classes")
                        top_classes = class_summary_df.nlargest(5, "Rate")[
                            ["Class", "Pupils", "Expected", "Collected", "Rate"]]
                        st.dataframe(
                            top_classes.style.format({
                                "Expected": "UGX {:,.0f}",
                                "Collected": "UGX {:,.0f}",
                                "Rate": "{:.1f}%"
                            }),
                            use_container_width=True
                        )

                st.markdown("---")
                st.subheader("Export Options")
                csv = df_to_show.to_csv(index=False).encode()
                st.download_button("📊 Download CSV", csv, f"school_wide_{current_term}_{current_year}.csv", "text/csv")
            else:
                st.warning("No data available for the selected filters")

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