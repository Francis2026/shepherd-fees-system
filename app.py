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
import streamlit as st

# ========== FIX: Prevent multiple initializations ==========
if "firebase_done" not in st.session_state:
    st.session_state.firebase_done = False

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

    /* Remove top white space and padding */
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 2rem;
        margin-top: 0rem !important;
    }

    /* Style header instead of hiding - make it transparent/small */
    header {
        background: transparent !important;
        padding: 0rem !important;
        height: 0rem !important;
        min-height: 0rem !important;
    }

    /* Hide the default Streamlit header content but keep sidebar button */
    header .stDecoration {
        display: none !important;
    }

    /* Ensure sidebar toggle button is visible and accessible */
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

    /* Remove extra space from top of app */
    .stApp {
        margin-top: 0rem;
        padding-top: 0rem;
    }

    /* Remove spacing from first element in main content */
    .main > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }

    /* Hide default Streamlit menu but keep sidebar button */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Remove top padding from the main area */
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

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%);
        border-right: none;
    }

    [data-testid="stSidebar"] * {
        color: #E8E8E8 !important;
    }

    /* Fix for selectbox labels in sidebar */
    [data-testid="stSidebar"] .stSelectbox label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }

    /* Fix for number input labels in sidebar */
    [data-testid="stSidebar"] .stNumberInput label {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 5px !important;
        display: block !important;
    }

    /* Fix for selectbox selected value text */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    /* Fix for number input value */
    [data-testid="stSidebar"] .stNumberInput input {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
    }

    /* Sidebar headers */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4 {
        color: #A8B56C !important;
    }

    /* Sidebar markdown text */
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

    /* Additional fix for sidebar radio buttons */
    [data-testid="stSidebar"] .stRadio label {
        color: #E8E8E8 !important;
    }

    /* Fix for sidebar divider */
    [data-testid="stSidebar"] hr {
        border-color: #2E5A8A !important;
    }

    /* Remove blue box when clicking on elements */
    .stButton > button:focus {
        outline: none !important;
        box-shadow: none !important;
    }

    /* Better scrollbar styling */
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

    /* Top header with logo and title on the right */
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

    /* Adjust main content to account for header */
    .main .block-container {
        padding-top: 0rem !important;
    }
    
    /* REMOVE STREAMLIT BRANDING - ADD THESE 6 LINES */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .stStatusWidget {display: none;}
    [data-testid="stToolbar"] {display: none;}
    a[href*="github"] {display: none !important;}
    
    /* REMOVE BOTTOM HOSTED BY STREAMLIT AND PROFILE ICON */
    .stApp footer {
        display: none !important;
    }
    .stAppViewerBadge {
        display: none !important;
    }
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    .css-1lsmg2y {
        display: none !important;
    }
    .st-emotion-cache-1lsmg2y {
        display: none !important;
    }
    .viewerBadge_link__qS5y8 {
        display: none !important;
    }
    .stApp > div:last-child {
        display: none !important;
    }
    
    
</style>
""", unsafe_allow_html=True)


# ------------------- Firebase Initialization -------------------
def init_firebase():
    # Only initialize once
    if st.session_state.firebase_done:
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


# ------------------- Logo Functions -------------------
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


def display_logo(height=100):
    logo_base64, mime_type = get_logo_base64()
    if logo_base64:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 0px; padding: 0px;">
            <img src="data:{mime_type};base64,{logo_base64}" height="{height}" style="border-radius: 15px;">
        </div>
        """, unsafe_allow_html=True)
        return True
    else:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 0px; padding: 0px;">
            <div style="background: linear-gradient(135deg, #1E3A5F, #2E5A8A); padding: 15px; border-radius: 15px;">
                <h2 style="color: white; margin: 0;">Shepherd Academy</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return False


# ------------------- Display Main Header Function -------------------
def display_main_header():
    """Display logo and title on the right side of the main app"""
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


# ------------------- User Authentication -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    try:
        users_ref = db.collection("users")
        user_doc = users_ref.document(username).get()

        if user_doc.exists:
            user_data = user_doc.to_dict()
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
            return True
        return False
    except Exception as e:
        st.error(f"Error creating users: {str(e)}")
        return False


# ------------------- Helper Functions -------------------
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

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
        """Calculate balance from previous term that carries over"""
        term_order = self.term_order[current_term]

        if term_order == 1:
            prev_year = current_year - 1
            prev_term = "Term 3"
        elif term_order == 2:
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
                balance = last_payment.get("balance", 0)
                return balance
            return 0
        except:
            return 0

    def enroll_pupil(self, name, class_name, term_fees, is_sponsored=False, sponsor_reason=""):
        """Enroll a new pupil with term fees"""
        try:
            pupil_ref = db.collection("pupils").document()
            pupil_ref.set({
                "name": name,
                "class": class_name,
                "enrollment_date": datetime.datetime.now(),
                "term_fees": term_fees,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "active": True,
                "archived": False,
                "leaving_date": None,
                "leaving_reason": None
            })
            return pupil_ref.id
        except Exception as e:
            st.error(f"Error enrolling pupil: {str(e)}")
            return None

    def archive_pupil(self, pupil_id, leaving_reason=""):
        """Archive a pupil who has left the school (soft delete)"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "active": False,
                "archived": True,
                "leaving_date": datetime.datetime.now(),
                "leaving_reason": leaving_reason,
                "archived_at": datetime.datetime.now()
            })
            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id):
        """Restore an archived pupil"""
        try:
            db.collection("pupils").document(pupil_id).update({
                "active": True,
                "archived": False,
                "restored_at": datetime.datetime.now()
            })
            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    def get_pupils(self, class_name, include_archived=False):
        """Get pupils, optionally including archived ones"""
        try:
            if include_archived:
                pupils_ref = db.collection("pupils").where(filter=firestore.FieldFilter("class", "==", class_name))
            else:
                pupils_ref = db.collection("pupils").where(
                    filter=firestore.FieldFilter("class", "==", class_name)).where(
                    filter=firestore.FieldFilter("active", "==", True))
            return list(pupils_ref.stream())
        except:
            if include_archived:
                pupils_ref = db.collection("pupils").where("class", "==", class_name)
            else:
                pupils_ref = db.collection("pupils").where("class", "==", class_name).where("active", "==", True)
            return list(pupils_ref.stream())

    def get_all_pupils(self, include_archived=False):
        """Get all pupils, optionally including archived ones"""
        try:
            if include_archived:
                return list(db.collection("pupils").stream())
            else:
                return list(db.collection("pupils").where("active", "==", True).stream())
        except:
            return list(db.collection("pupils").stream())

    def get_archived_pupils(self):
        """Get all archived pupils"""
        try:
            return list(db.collection("pupils").where("archived", "==", True).stream())
        except:
            return []

    def get_ledger(self, pupil_id, term, year):
        """Get all payments for a pupil for a specific term and year"""
        try:
            # Get the collection reference
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)

            # Get ALL documents first (no filter to avoid index requirement)
            all_docs = list(ledger_ref.stream())

            # Filter by year in Python
            filtered_docs = []
            for doc in all_docs:
                data = doc.to_dict()
                doc_year = data.get("year")
                if doc_year is not None and int(doc_year) == int(year):
                    filtered_docs.append(doc)

            # Sort by date in Python
            filtered_docs.sort(key=lambda x: x.to_dict().get("date", datetime.datetime.min))

            return filtered_docs
        except Exception as e:
            st.error(f"Error fetching ledger: {str(e)}")
            return []

    def check_ledger_data(self, pupil_id, term, year):
        """Debug method to check what data exists"""
        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            all_docs = list(ledger_ref.stream())

            print(f"\n=== LEDGER DEBUG for {pupil_id} - {term} {year} ===")
            print(f"Total documents in collection: {len(all_docs)}")

            for doc in all_docs:
                data = doc.to_dict()
                print(f"  Doc ID: {doc.id}")
                print(f"    year: {data.get('year')} (type: {type(data.get('year'))})")
                print(f"    amount: {data.get('amount')}")
                print(f"    date: {data.get('date')}")
                print(f"    receipt_no: {data.get('receipt_no')}")

            # Also check payments without year filter
            return all_docs
        except Exception as e:
            print(f"Debug error: {e}")
            return []

    def get_pupil_details(self, pupil_id):
        try:
            return db.collection("pupils").document(pupil_id).get()
        except Exception as e:
            return None

    def update_pupil(self, pupil_id, name, class_name, term_fees, is_sponsored=False, sponsor_reason=""):
        try:
            db.collection("pupils").document(pupil_id).update({
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason if is_sponsored else "",
                "updated_at": datetime.datetime.now()
            })
            return True
        except Exception as e:
            st.error(f"Error updating pupil: {str(e)}")
            return False

    def add_payment(self, pupil_id, term, year, amount, description):
        """Add a payment for a pupil for a specific term and year with carry-over balance"""
        try:
            ledger_ref = db.collection("ledgers").document(pupil_id).collection(term)
            pupil = self.get_pupil_details(pupil_id)
            if not pupil or not pupil.exists:
                return None, "Pupil not found", None, None, 0

            pupil_data = pupil.to_dict()
            term_fees = pupil_data.get("term_fees", 0)
            is_sponsored = pupil_data.get("is_sponsored", False)

            if is_sponsored:
                term_fees = 0

            # Ensure year is integer
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

            # Store with year as integer
            ledger_ref.document(transaction_id).set({
                "date": datetime.datetime.now(),
                "amount": amount,
                "description": description,
                "balance": new_balance,
                "previous_balance": previous_balance,
                "term_fees": term_fees,
                "total_due": total_due,
                "year": year_int,  # Store as integer
                "receipt_no": receipt_no,
                "excess_amount": excess_amount
            })
            return transaction_id, new_balance, receipt_no, previous_balance, excess_amount
        except Exception as e:
            st.error(f"Error adding payment: {str(e)}")
            return None, str(e), None, None, 0

    def get_pupil_term_summary(self, pupil_id, term, year):
        try:
            pupil_doc = self.get_pupil_details(pupil_id)
            if not pupil_doc or not pupil_doc.exists:
                return None, 0, 0, 0, 0, 0, False, "", False

            pupil_data = pupil_doc.to_dict()
            term_fees = pupil_data.get("term_fees", 0)
            is_sponsored = pupil_data.get("is_sponsored", False)
            sponsor_reason = pupil_data.get("sponsor_reason", "")
            is_archived = pupil_data.get("archived", False)

            if is_sponsored:
                term_fees = 0

            previous_balance = self.get_previous_term_balance(pupil_id, term, year)
            payments = db.collection("ledgers").document(pupil_id).collection(term).where("year", "==", year).stream()
            total_paid = sum([p.to_dict().get("amount", 0) for p in payments])

            total_due = previous_balance + term_fees
            balance = max(0, total_due - total_paid)

            credit_balance = previous_balance if previous_balance < 0 else 0

            return pupil_data, term_fees, total_paid, balance, previous_balance, credit_balance, is_sponsored, sponsor_reason, is_archived
        except Exception as e:
            return None, 0, 0, 0, 0, 0, False, "", False

    def get_class_summary(self, class_name, term, year, include_archived=False):
        pupils = self.get_pupils(class_name, include_archived)
        summary = []
        cleared_list = []
        not_cleared_list = []
        archived_list = []

        for pup in pupils:
            pupil_data = pup.to_dict()
            pupil_id = pup.id
            term_fees = pupil_data.get("term_fees", 0)
            is_sponsored = pupil_data.get("is_sponsored", False)
            sponsor_reason = pupil_data.get("sponsor_reason", "")
            is_archived = pupil_data.get("archived", False)

            if is_sponsored:
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
                if is_sponsored:
                    status = "Sponsored - Cleared"

            pupil_info = {
                "Name": pupil_data["name"],
                "Previous Balance (UGX)": previous_balance,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if is_sponsored else "",
                "Leaving Date": pupil_data.get("leaving_date", "").strftime("%Y-%m-%d") if pupil_data.get(
                    "leaving_date") else "",
                "Leaving Reason": pupil_data.get("leaving_reason", "")
            }
            summary.append(pupil_info)

            if is_archived:
                archived_list.append(pupil_info)
            elif balance == 0 or is_sponsored:
                cleared_list.append(pupil_info)
            else:
                not_cleared_list.append(pupil_info)

        # Reset index to remove default index column
        df_summary = pd.DataFrame(summary).reset_index(drop=True)
        df_cleared = pd.DataFrame(cleared_list).reset_index(drop=True)
        df_not_cleared = pd.DataFrame(not_cleared_list).reset_index(drop=True)
        df_archived = pd.DataFrame(archived_list).reset_index(drop=True)

        # Add serial numbers as first column
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
        all_pupils = self.get_all_pupils(include_archived)
        all_summaries = []

        for pupil in all_pupils:
            pupil_data = pupil.to_dict()
            pupil_id = pupil.id
            term_fees = pupil_data.get("term_fees", 0)
            is_sponsored = pupil_data.get("is_sponsored", False)
            sponsor_reason = pupil_data.get("sponsor_reason", "")
            is_archived = pupil_data.get("archived", False)

            if is_sponsored:
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
                if is_sponsored:
                    status = "Sponsored - Cleared"

            all_summaries.append({
                "Class": pupil_data["class"],
                "Name": pupil_data["name"],
                "Previous Balance (UGX)": previous_balance,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if is_sponsored else "",
                "Leaving Date": pupil_data.get("leaving_date", "").strftime("%Y-%m-%d") if pupil_data.get(
                    "leaving_date") else "",
                "Leaving Reason": pupil_data.get("leaving_reason", "")
            })

        df = pd.DataFrame(all_summaries).reset_index(drop=True)
        if not df.empty:
            df.insert(0, "No.", range(1, len(df) + 1))
        return df


# ------------------- Modern Login UI -------------------
def login_page():
    # Show loading only once
    if "login_loaded" not in st.session_state:
        with st.spinner("Loading Shepherd Academy School Fees Management System..."):
            time.sleep(0.5)
        st.session_state.login_loaded = True
    # create_default_users()

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

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    role = authenticate_user(username, password)
                    if role:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.session_state["role"] = role
                        st.rerun()
                    else:
                        st.error("Invalid username or password")


# ------------------- Main App -------------------
def main_app():
    # Display the header with logo on the right at the top of the main interface
    display_main_header()

    if "navigation_menu" not in st.session_state:
        st.session_state.navigation_menu = "Dashboard"

    # Track if we should show archived pupils
    if "show_archived" not in st.session_state:
        st.session_state.show_archived = False

    with st.sidebar:
        role = st.session_state["role"]

        # Profile photo in circular format
        profile_image_path = "jane.jpg"
        if os.path.exists(profile_image_path):
            # Read and encode the image
            with open(profile_image_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-bottom: 15px;">
                <img src="data:image/jpeg;base64,{img_data}" 
                     style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #A8B56C; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback if image doesn't exist
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

        # Define navigation options
        if role == "bursar":
            nav_options = ["Dashboard", "Enroll Pupil", "Pupils & Ledgers", "Record Payment",
                           "Class Reports", "School Reports", "Manage Pupils", "Archived Pupils"]
        else:
            nav_options = ["Dashboard", "Pupils & Ledgers", "Class Reports", "School Reports"]

        # Simple radio button navigation
        selected_menu = st.radio(
            "Menu",
            nav_options,
            key="nav_radio",
            label_visibility="collapsed"
        )

        st.session_state.navigation_menu = selected_menu
        menu = selected_menu

        st.markdown("---")

        # Period section
        st.markdown("### Period")
        current_term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="global_term")
        current_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.datetime.now().year,
                                       step=1)

        st.markdown("---")

        # Show archived toggle for bursar
        if role == "bursar" and menu in ["Pupils & Ledgers", "Class Reports", "School Reports"]:
            st.session_state.show_archived = st.checkbox("Show Archived Pupils", value=st.session_state.show_archived)

        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            for key in ["logged_in", "username", "role", "navigation_menu", "show_archived"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    manager = FeesManager()

    # ------------------- Dashboard -------------------
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #1E3A5F; margin-bottom: 1rem;'>Dashboard</h2>", unsafe_allow_html=True)

        total_pupils = len(manager.get_all_pupils(include_archived=False))
        total_archived = len(manager.get_archived_pupils())
        total_expected = 0
        total_collected = 0
        total_balance = 0
        collection_rate = 0

        df_school = manager.get_school_wide_summary(current_term, current_year, include_archived=False)
        if not df_school.empty:
            total_expected = df_school["Total Due (UGX)"].sum()
            total_collected = df_school["Total Paid (UGX)"].sum()
            total_balance = df_school["Balance (UGX)"].sum()
            collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 2rem;">{total_pupils}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Active Pupils</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1.5rem;">{total_archived}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Archived Pupils</p>
                <small style="color: #ADB5BD;">Left School</small>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1rem;">UGX {total_expected:,.0f}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Total Due ({current_term})</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1rem;">UGX {total_collected:,.0f}</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Total Collected ({current_term})</p>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            st.markdown(f"""
            <div class="modern-card" style="text-align: center;">
                <h3 style="color: #1E3A5F; margin-bottom: 0; font-size: 1.5rem;">{collection_rate:.1f}%</h3>
                <p style="color: #6C757D; margin-bottom: 0; font-weight: 600;">Collection Rate</p>
            </div>
            """, unsafe_allow_html=True)

        if collection_rate > 0:
            st.progress(collection_rate / 100)

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

    # ------------------- Enroll Pupil -------------------
    elif menu == "Enroll Pupil" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Enroll New Pupil</h1>", unsafe_allow_html=True)
        st.info("When you enroll a pupil, you set the fees for EACH TERM.")

        col1, col2 = st.columns(2)
        with col1:
            pupil_name = st.text_input("Full Name *", placeholder="Enter pupil's full name", key="enroll_name")
            pupil_class = st.selectbox("Class *", manager.classes, key="enroll_class")
        with col2:
            term_fees = st.number_input("Fees Per Term (UGX) *", min_value=0, step=0, value=0, key="enroll_fees",
                                        placeholder="0")
            is_sponsored = st.checkbox("Sponsored Child (Shepherd Beneficiary)", key="is_sponsored")
            sponsor_reason = ""
            if is_sponsored:
                sponsor_reason = st.text_input("Sponsor Reason", value="Shepherd Child", key="sponsor_reason")
            enrollment_note = st.text_area("Notes (Optional)", placeholder="Any additional information",
                                           key="enroll_note")

        if st.button("Enroll Pupil", use_container_width=True):
            if pupil_name:
                pupil_id = manager.enroll_pupil(pupil_name, pupil_class, term_fees, is_sponsored, sponsor_reason)
                if pupil_id:
                    if is_sponsored:
                        st.success(
                            f"✅ {pupil_name} has been successfully enrolled as a SPONSORED CHILD (Shepherd Beneficiary)!")
                        st.info(f"📌 This child has been marked as sponsored. No fees will be charged.")
                    else:
                        st.success(f"✅ {pupil_name} has been successfully enrolled!")
                        st.info(f"📌 Term Fees set to UGX {term_fees:,.0f} per term.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Please fill all required fields")

    # ------------------- Pupils & Ledgers -------------------
    elif menu == "Pupils & Ledgers":
        st.markdown("<h1 style='color: #1E3A5F;'>Pupils & Ledgers</h1>", unsafe_allow_html=True)

        if st.session_state.show_archived:
            st.info(
                f"Showing data for **{current_term}, {current_year}** (INCLUDING ARCHIVED PUPILS - those who left the school)")
        else:
            st.info(f"Showing data for **{current_term}, {current_year}** (Active pupils only)")

        col_class, col_search = st.columns([1, 2])
        with col_class:
            selected_class = st.selectbox("Select Class", manager.classes, key="ledger_class")
        with col_search:
            search_term = st.text_input("Search Pupil", placeholder="Type name to search...")

        pupils = manager.get_pupils(selected_class, include_archived=st.session_state.show_archived)
        if search_term:
            pupils = [p for p in pupils if search_term.lower() in p.to_dict()["name"].lower()]

        if not pupils:
            st.info(f"No pupils found in {selected_class}")
        else:
            st.markdown(f"### Found {len(pupils)} pupil(s) in {selected_class}")

            for pupil_doc in pupils:
                pupil = pupil_doc.to_dict()
                pupil_id = pupil_doc.id

                is_archived = pupil.get("archived", False)
                term_fees = pupil.get("term_fees", 0)
                is_sponsored = pupil.get("is_sponsored", False)
                sponsor_reason = pupil.get("sponsor_reason", "")

                # Get previous term balance
                previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)

                # Get all payments without requiring composite index
                try:
                    ledger_ref = db.collection("ledgers").document(pupil_id).collection(current_term)
                    all_ledger_docs = list(ledger_ref.stream())

                    ledger_entries = []
                    for doc in all_ledger_docs:
                        data = doc.to_dict()
                        doc_year = data.get("year")
                        if doc_year is not None and int(doc_year) == int(current_year):
                            ledger_entries.append(doc)

                    ledger_entries.sort(key=lambda x: x.to_dict().get("date", datetime.datetime.min))

                except Exception as e:
                    st.error(f"Error fetching ledger: {str(e)}")
                    ledger_entries = []

                total_paid_this_term = sum([p.to_dict().get("amount", 0) for p in ledger_entries])

                # Calculate totals
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

                # Create transaction list for display
                all_transactions = []

                # Add opening balance row if there's a carry-over
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

                # Add all payment transactions
                for idx, entry in enumerate(ledger_entries, 1):
                    data = entry.to_dict()
                    all_transactions.append({
                        "S/No": idx,
                        "Date": data["date"].strftime("%Y-%m-%d %H:%M:%S"),
                        "Amount Paid": f"UGX {data['amount']:,.0f}",
                        "Description": data.get("description", "Payment"),
                        "Balance After": f"UGX {data.get('balance', 0):,.0f}",
                        "Receipt No": data.get("receipt_no", "")
                    })

                # Create expander title
                if is_archived:
                    expander_title = f"📌 {pupil['name']} — [ARCHIVED - LEFT SCHOOL]"
                elif is_sponsored:
                    expander_title = f"📌 {pupil['name']} — 🎓 SPONSORED CHILD (No fees)"
                else:
                    if show_credit:
                        expander_title = f"📌 {pupil['name']} — 💳 Credit: UGX {carry_over_amount:,.0f} | Term: UGX {term_fees:,.0f} | Balance: UGX {current_balance:,.0f}"
                    elif show_carry_over:
                        expander_title = f"📌 {pupil['name']} — ⚠️ Carry-over: UGX {carry_over_amount:,.0f} | Term: UGX {term_fees:,.0f} | Balance: UGX {current_balance:,.0f}"
                    else:
                        expander_title = f"📌 {pupil['name']} — Term: UGX {term_fees:,.0f} | Paid: UGX {total_paid_this_term:,.0f} | Balance: UGX {current_balance:,.0f}"

                with st.expander(expander_title):
                    if is_archived:
                        st.warning(f"🏁 **This pupil has left the school**")
                        leaving_date = pupil.get('leaving_date')
                        if leaving_date and isinstance(leaving_date, datetime.datetime):
                            st.info(f"Left on: {leaving_date.strftime('%Y-%m-%d')}")
                        st.info(f"Reason: {pupil.get('leaving_reason', 'Not specified')}")

                    if is_sponsored:
                        st.success(f"🎓 **Sponsored Child** - Reason: {sponsor_reason}")

                    if show_carry_over:
                        st.warning(f"⚠️ **Balance brought forward: UGX {carry_over_amount:,.0f}**")
                    elif show_credit:
                        st.success(f"✅ **Credit brought forward: UGX {carry_over_amount:,.0f}**")

                    if all_transactions:
                        df = pd.DataFrame(all_transactions)
                        st.dataframe(df, use_container_width=True)

                        # Summary metrics
                        col1, col2, col3, col4, col5 = st.columns(5)

                        with col1:
                            if show_carry_over:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Carry-over</p>
                                    <p style="color: #DC3545; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {carry_over_amount:,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            elif show_credit:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Credit</p>
                                    <p style="color: #28A745; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {carry_over_amount:,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Previous</p>
                                    <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX 0</p>
                                </div>
                                """, unsafe_allow_html=True)

                        with col2:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Term Fees</p>
                                <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {term_fees:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col3:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Total Paid</p>
                                <p style="color: #28A745; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_paid_this_term:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col4:
                            total_due_amount = (carry_over_amount if show_carry_over else 0) + term_fees
                            if show_credit:
                                total_due_amount = max(0, term_fees - carry_over_amount)
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Total Due</p>
                                <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_due_amount:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col5:
                            balance_color = "#DC3545" if current_balance > 0 else "#28A745"
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Balance</p>
                                <p style="color: {balance_color}; margin: 2px 0 0 0; font-weight: 700; font-size: 0.7rem;">UGX {current_balance:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # Print receipt buttons
                        if ledger_entries:
                            st.markdown("---")
                            st.markdown("### 📄 Payment Receipts")

                            receipt_buttons = []
                            for entry in ledger_entries:
                                data = entry.to_dict()
                                receipt_buttons.append({
                                    "receipt_no": data.get("receipt_no", ""),
                                    "date": data["date"],
                                    "amount": data["amount"],
                                    "description": data["description"],
                                    "balance": data["balance"],
                                    "previous_balance": data.get("previous_balance", 0),
                                    "excess_amount": data.get("excess_amount", 0),
                                    "id": entry.id
                                })

                            for i in range(0, len(receipt_buttons), 3):
                                cols = st.columns(3)
                                for j, btn in enumerate(receipt_buttons[i:i + 3]):
                                    with cols[j]:
                                        if st.button(f"🖨️ Receipt {btn['receipt_no'][-12:]}",
                                                     key=f"print_{btn['id']}"):
                                            pdf_buffer = generate_pdf_receipt(
                                                school_name="Shepherd Academy Busiu",
                                                logo_path="images.jfif" if os.path.exists("images.jfif") else "",
                                                receipt_num=btn['receipt_no'],
                                                date_str=btn['date'].strftime("%Y-%m-%d %H:%M:%S"),
                                                child_name=pupil['name'],
                                                amount=btn['amount'],
                                                description=btn['description'],
                                                balance=btn['balance'],
                                                previous_balance=btn['previous_balance'],
                                                term_fees=term_fees,
                                                signature_text="Bursar's Signature",
                                                excess_amount=btn['excess_amount']
                                            )
                                            st.download_button("📥 PDF", pdf_buffer, f"Receipt_{btn['receipt_no']}.pdf",
                                                               "application/pdf")

                        # Export ledger button
                        csv = df.to_csv(index=False).encode()
                        st.download_button("📥 Download Ledger (CSV)", csv, f"{pupil['name']}_ledger.csv", "text/csv")

                    else:
                        st.info(f"No payments recorded yet for {current_term}, {current_year}")

                        # Show expected fees
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if show_carry_over:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Balance B/F</p>
                                    <p style="color: #DC3545; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {carry_over_amount:,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            elif show_credit:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Credit B/F</p>
                                    <p style="color: #28A745; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">-UGX {carry_over_amount:,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Balance B/F</p>
                                    <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX 0</p>
                                </div>
                                """, unsafe_allow_html=True)

                        with col2:
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Term Fees</p>
                                <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {term_fees:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        with col3:
                            total_due_amount = (carry_over_amount if show_carry_over else 0) + term_fees
                            if show_credit:
                                total_due_amount = max(0, term_fees - carry_over_amount)
                            st.markdown(f"""
                            <div style="background: #F8F9FA; border-radius: 8px; padding: 5px; text-align: center;">
                                <p style="color: #6C757D; margin: 0; font-size: 0.6rem;">Amount Due</p>
                                <p style="color: #DC3545; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {total_due_amount:,.0f}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    # Record Payment button
                    if role == "bursar" and not is_sponsored and not is_archived:
                        st.markdown("---")
                        if st.button(f"💰 Record Payment for {pupil['name']}", key=f"pay_{pupil_id}",
                                     use_container_width=True):
                            st.session_state.navigation_menu = "Record Payment"
                            st.session_state.quick_pay_pupil = pupil_id
                            st.session_state.quick_pay_name = pupil['name']
                            st.rerun()

    # ------------------- Record Payment -------------------
    elif menu == "Record Payment" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Record Payment</h1>", unsafe_allow_html=True)
        st.info(f"Recording payment for **{current_term}, {current_year}**")

        # Get all active pupils
        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.warning("No active pupils found. Please enroll pupils first.")
        else:
            # --- FILTERS ---
            st.markdown("### 🔍 Filter Pupils")
            col_filter1, col_filter2 = st.columns([1, 2])

            with col_filter1:
                # Class filter
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_payment_class")

            with col_filter2:
                # Search bar
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_payment_pupil")

            # Apply filters
            pupil_dicts = []
            for p in all_pupils:
                pupil_dict = p.to_dict()
                pupil_dict['id'] = p.id
                pupil_dicts.append(pupil_dict)

            # Filter by class
            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]

            # Filter by search term
            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning(f"No pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(pupil_dicts)} pupil(s)")

                # Create selectable options
                pupil_options = {f"{p['name']} ({p['class']})": p['id'] for p in pupil_dicts}

                # Check if coming from quick pay
                if "quick_pay_pupil" in st.session_state:
                    pupil_id = st.session_state.quick_pay_pupil
                    pupil_name = st.session_state.quick_pay_name
                    st.success(f"Selected pupil: **{pupil_name}**")
                    # Find the pupil in the filtered list
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
                    # Regular selection
                    selected = st.selectbox("Select Pupil", list(pupil_options.keys()), key="payment_pupil")
                    pupil_id = pupil_options[selected]
                    pupil_name = selected.split(" (")[0]
                    selected_pupil = next((p for p in pupil_dicts if p['id'] == pupil_id), None)

                if selected_pupil:
                    pupil_doc = manager.get_pupil_details(pupil_id)
                    if pupil_doc and pupil_doc.exists:
                        pupil_data = pupil_doc.to_dict()
                        term_fees = pupil_data.get("term_fees", 0)
                        is_sponsored = pupil_data.get("is_sponsored", False)
                        is_archived = pupil_data.get("archived", False)

                        if is_archived:
                            st.error("This pupil has left the school. Cannot record payments for archived pupils.")
                        elif is_sponsored:
                            st.warning("This is a sponsored child. No payment is required.")
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
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.65rem;">Pupil Name</p>
                                    <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.7rem;">{pupil_name}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            with col2:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.65rem;">Class</p>
                                    <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.7rem;">{pupil_data['class']}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            with col3:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.65rem;">Previous Balance</p>
                                    <p style="color: #DC3545; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {max(0, previous_balance):,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            with col4:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.65rem;">Term Fees</p>
                                    <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.65rem;">UGX {term_fees:,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            with col5:
                                st.markdown(f"""
                                <div style="background: #F8F9FA; border-radius: 10px; padding: 6px; text-align: center;">
                                    <p style="color: #6C757D; margin: 0; font-size: 0.65rem;">Due This Term</p>
                                    <p style="color: #1E3A5F; margin: 2px 0 0 0; font-weight: 700; font-size: 0.7rem;">UGX {current_balance:,.0f}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            if previous_balance < 0:
                                st.success(
                                    f"✅ **Credit Balance from previous term: UGX {abs(previous_balance):,.0f} (This amount has been deducted from current term fees)**")

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
                                                f"💰 Excess payment of UGX {excess_amount:,.0f} has been carried forward as credit to next term!")
                                        else:
                                            st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded successfully!")
                                        st.info(
                                            f"New balance for {current_term}, {current_year}: UGX {new_balance:,.0f}")

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

    # ------------------- Class Reports -------------------
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
                    fig = px.bar(df_full[df_full["Status"] != "Archived (Left School)"], x="Name",
                                 y=["Total Paid (UGX)", "Balance (UGX)"],
                                 title=f"Fee Overview - {selected_class} ({current_term} {current_year})",
                                 barmode="group", color_discrete_sequence=['#28A745', '#DC3545'])
                    fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
                    st.plotly_chart(fig, use_container_width=True)

                    total_expected = df_full[df_full["Status"] != "Archived (Left School)"]["Total Due (UGX)"].sum()
                    total_paid = df_full[df_full["Status"] != "Archived (Left School)"]["Total Paid (UGX)"].sum()
                    total_balance = df_full[df_full["Status"] != "Archived (Left School)"]["Balance (UGX)"].sum()
                    cleared_count = len(df_cleared)
                    not_cleared_count = len(df_not_cleared)
                    archived_count = len(df_archived)

                    col1, col2, col3, col4, col5, col6 = st.columns(6)

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
                            <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Archived</h4>
                            <p style="color: #6C757D; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{archived_count}</p>
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

    # ------------------- School Reports -------------------
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
            columns_to_export = st.multiselect("Columns to Export",
                                               ["Class", "Name", "Previous Balance (UGX)", "Term Fees (UGX)",
                                                "Total Due (UGX)", "Total Paid (UGX)", "Balance (UGX)", "Status",
                                                "Sponsor Reason", "Leaving Date", "Leaving Reason"],
                                               default=["Class", "Name", "Total Due (UGX)", "Total Paid (UGX)",
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

            if not df_school.empty:
                display_columns = [col for col in columns_to_export if col in df_school.columns]
                if display_columns:
                    st.dataframe(df_school[display_columns], use_container_width=True)
                else:
                    st.dataframe(df_school, use_container_width=True)

                total_expected = df_school[df_school["Status"] != "Archived (Left School)"][
                    "Total Due (UGX)"].sum() if not df_school.empty else 0
                total_paid = df_school[df_school["Status"] != "Archived (Left School)"][
                    "Total Paid (UGX)"].sum() if not df_school.empty else 0
                total_balance = df_school[df_school["Status"] != "Archived (Left School)"][
                    "Balance (UGX)"].sum() if not df_school.empty else 0

                cleared = len(df_school[(df_school["Balance (UGX)"] == 0) & (
                    ~df_school["Status"].str.contains("Sponsored|Archived", na=False))])
                sponsored = len(df_school[df_school["Status"].str.contains("Sponsored", na=False)])
                not_cleared = len(df_school[(df_school["Balance (UGX)"] > 0) & (
                    ~df_school["Status"].str.contains("Sponsored|Archived", na=False))])
                archived = len(df_school[df_school["Status"] == "Archived (Left School)"])

                st.markdown("### Summary Statistics")
                col1, col2, col3, col4, col5, col6 = st.columns(6)

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
                        <h4 style="color: #1E3A5F; margin: 0; font-size: 0.7rem;">Archived</h4>
                        <p style="color: #6C757D; margin: 3px 0 0 0; font-weight: 700; font-size: 1rem;">{archived}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.info(f"🎓 Sponsored Children: {sponsored}")

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

    # ------------------- Manage Pupils -------------------
    elif menu == "Manage Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Manage Pupils</h1>", unsafe_allow_html=True)

        # Get all active pupils
        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.info("No active pupils found")
        else:
            # --- FILTERS ---
            st.markdown("### 🔍 Filter Pupils")
            col_filter1, col_filter2 = st.columns([1, 2])

            with col_filter1:
                # Class filter
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_manage_class")

            with col_filter2:
                # Search bar
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_pupil")

            # Apply filters
            filtered_pupils = all_pupils
            pupil_dicts = []

            for p in filtered_pupils:
                pupil_dict = p.to_dict()
                pupil_dict['id'] = p.id
                pupil_dicts.append(pupil_dict)

            # Filter by class
            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]

            # Filter by search term
            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning(f"No pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(pupil_dicts)} pupil(s)")

                # Show pupils in a selectable format
                for idx, pupil in enumerate(pupil_dicts):
                    with st.expander(
                            f"📌 {pupil['name']} - {pupil['class']} (Fees: UGX {pupil.get('term_fees', 0):,.0f})"):

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            **Current Information:**
                            - **Name:** {pupil['name']}
                            - **Class:** {pupil['class']}
                            - **Term Fees:** UGX {pupil.get('term_fees', 0):,.0f}
                            - **Sponsored:** {'Yes' if pupil.get('is_sponsored', False) else 'No'}
                            - **Sponsor Reason:** {pupil.get('sponsor_reason', 'N/A')}
                            """)

                        with col2:
                            # Show payment summary
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

                        # Edit Form
                        st.markdown("### ✏️ Edit Pupil Details")
                        with st.form(key=f"edit_form_{pupil['id']}"):
                            new_name = st.text_input("Name", pupil['name'], key=f"name_{pupil['id']}")
                            new_class = st.selectbox("Class", manager.classes,
                                                     index=manager.classes.index(pupil['class']) if pupil[
                                                                                                        'class'] in manager.classes else 0,
                                                     key=f"class_{pupil['id']}")
                            new_fees = st.number_input("Term Fees (UGX)", value=int(pupil.get('term_fees', 0)),
                                                       step=50000, key=f"fees_{pupil['id']}")

                            is_sponsored = st.checkbox("Sponsored Child", value=pupil.get('is_sponsored', False),
                                                       key=f"sponsored_{pupil['id']}")
                            sponsor_reason = ""
                            if is_sponsored:
                                sponsor_reason = st.text_input("Sponsor Reason",
                                                               value=pupil.get('sponsor_reason', "Shepherd Child"),
                                                               key=f"reason_{pupil['id']}")

                            col_edit, col_archive = st.columns(2)

                            with col_edit:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    manager.update_pupil(pupil['id'], new_name, new_class, new_fees, is_sponsored,
                                                         sponsor_reason)
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

    # ------------------- Archived Pupils -------------------
    elif menu == "Archived Pupils":
        st.markdown("<h1 style='color: #1E3A5F;'>Archived Pupils (Left School)</h1>", unsafe_allow_html=True)
        st.info(
            "These pupils have left the school. Their historical payment records are preserved for reporting purposes.")

        archived_pupils = manager.get_archived_pupils()

        if not archived_pupils:
            st.info("No archived pupils found.")
        else:
            # --- FILTERS ---
            st.markdown("### 🔍 Filter Archived Pupils")
            col_filter1, col_filter2 = st.columns([1, 2])

            with col_filter1:
                # Get unique classes from archived pupils
                archived_classes = list(set([p.to_dict().get("class", "") for p in archived_pupils]))
                archived_classes.sort()
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + archived_classes,
                                            key="filter_archived_class")

            with col_filter2:
                # Search bar
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_archived_pupil")

            # Apply filters
            filtered_archived = archived_pupils
            filtered_list = []

            for p in filtered_archived:
                pupil_dict = p.to_dict()
                pupil_dict['id'] = p.id

                # Filter by class
                if filter_class != "All Classes" and pupil_dict.get("class") != filter_class:
                    continue

                # Filter by search term
                if search_term and search_term.lower() not in pupil_dict.get("name", "").lower():
                    continue

                filtered_list.append(pupil_dict)

            if not filtered_list:
                st.warning(f"No archived pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(filtered_list)} archived pupil(s)")

                for pupil in filtered_list:
                    pupil_id = pupil['id']

                    with st.expander(
                            f"📌 {pupil['name']} - {pupil['class']} (Left on {pupil.get('leaving_date', '').strftime('%Y-%m-%d') if pupil.get('leaving_date') else 'Unknown date'})"):

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            **Pupil Information:**
                            - **Name:** {pupil['name']}
                            - **Class:** {pupil['class']}
                            - **Original Term Fees:** UGX {pupil.get('term_fees', 0):,.0f}
                            - **Sponsored:** {'Yes' if pupil.get('is_sponsored', False) else 'No'}
                            - **Leaving Date:** {pupil.get('leaving_date', '').strftime('%Y-%m-%d') if pupil.get('leaving_date') else 'N/A'}
                            - **Leaving Reason:** {pupil.get('leaving_reason', 'Not specified')}
                            """)

                        with col2:
                            # Show payment summary across all terms
                            st.markdown("**Payment Summary:**")
                            total_paid_all = 0
                            for term in ["Term 1", "Term 2", "Term 3"]:
                                payments = db.collection("ledgers").document(pupil_id).collection(term).stream()
                                term_paid = sum([p.to_dict().get("amount", 0) for p in payments])
                                total_paid_all += term_paid
                                if term_paid > 0:
                                    st.write(f"- {term}: UGX {term_paid:,.0f}")

                            # Show any excess/credit balance
                            st.write(f"**Total Paid (All Time):** UGX {total_paid_all:,.0f}")

                            # Check if there's any outstanding balance
                            total_expected = pupil.get('term_fees', 0) * 3  # 3 terms
                            if total_paid_all < total_expected:
                                st.warning(f"⚠️ Outstanding balance: UGX {total_expected - total_paid_all:,.0f}")
                            elif total_paid_all > total_expected:
                                st.success(f"✅ Excess payment: UGX {total_paid_all - total_expected:,.0f}")

                        # Only show Restore button for Bursar (Admin cannot restore)
                        if role == "bursar":
                            if st.button(f"🔄 Restore Pupil", key=f"restore_{pupil_id}"):
                                if manager.restore_pupil(pupil_id):
                                    st.success(f"✅ {pupil['name']} has been restored to active pupils!")
                                    st.rerun()


def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        main_app()


if __name__ == "__main__":
    main()