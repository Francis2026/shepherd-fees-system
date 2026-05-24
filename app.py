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
import sqlite3
import json
from pathlib import Path
from functools import lru_cache
import threading

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
    st.session_state.offline_mode = False

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
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 0rem !important; padding-bottom: 2rem; margin-top: 0rem !important; }
    header { background: transparent !important; padding: 0rem !important; height: 0rem !important; min-height: 0rem !important; }
    header .stDecoration { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: flex !important; background-color: #1E3A5F !important; border-radius: 0 8px 8px 0 !important; padding: 8px 10px !important; margin-top: 20px !important; }
    [data-testid="stSidebarCollapseButton"] svg { fill: white !important; }
    .stApp { margin-top: 0rem; padding-top: 0rem; }
    .main > div:first-child { padding-top: 0rem !important; margin-top: 0rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    section.main > div { padding-top: 0rem !important; }
    .modern-card { background: white; border-radius: 20px; padding: 1.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s; border: 1px solid rgba(0,0,0,0.05); }
    .modern-card:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    .stButton > button { background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8A 100%); color: white; border-radius: 12px; border: none; padding: 0.7rem 1.5rem; font-weight: 600; transition: all 0.3s ease; width: 100%; font-size: 0.9rem; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(30,58,95,0.3); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%); border-right: none; }
    [data-testid="stSidebar"] * { color: #E8E8E8 !important; }
    [data-testid="stSidebar"] .stSelectbox label, [data-testid="stSidebar"] .stNumberInput label { color: #FFFFFF !important; font-weight: 600 !important; font-size: 14px !important; margin-bottom: 5px !important; display: block !important; }
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div, [data-testid="stSidebar"] .stNumberInput input { color: #1A1A2E !important; background-color: #FFFFFF !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 { color: #A8B56C !important; }
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea { border-radius: 12px; border: 2px solid #E5E7EB; padding: 0.6rem 1rem; }
    .dataframe { border-radius: 16px !important; overflow: hidden; }
    .dataframe thead tr th { background: linear-gradient(135deg, #1E3A5F 0%, #2E5A8A 100%) !important; color: white !important; padding: 12px !important; }
    .streamlit-expanderHeader { background: #F8F9FA; border-radius: 12px; font-weight: 600; }
    .badge-success { background: #28A745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-warning { background: #FFC107; color: #333; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-info { background: #17A2B8; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    .badge-secondary { background: #6C757D; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
    [data-testid="stSidebar"] .stRadio label { color: #E8E8E8 !important; }
    [data-testid="stSidebar"] hr { border-color: #2E5A8A !important; }
    .stButton > button:focus { outline: none !important; box-shadow: none !important; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #F1F1F1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #1E3A5F; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #2E5A8A; }
    .main-header { display: flex; justify-content: flex-end; align-items: center; padding: 10px 20px; background: white; border-radius: 0 0 0 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; position: sticky; top: 0; z-index: 999; }
    .header-content { display: flex; align-items: center; gap: 15px; }
    .header-logo { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; border: 2px solid #A8B56C; }
    .header-text { text-align: right; }
    .header-title { font-size: 1.1rem; font-weight: 700; color: #1E3A5F; margin: 0; }
    .header-subtitle { font-size: 0.7rem; color: #6C757D; margin: 0; }
    .main .block-container { padding-top: 0rem !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .stStatusWidget {display: none;}
    [data-testid="stToolbar"] {display: none;}
    a[href*="github"] {display: none !important;}
    .stAppViewerBadge {display: none !important;}
</style>
""", unsafe_allow_html=True)


# ==================== FLASH DISK DATABASE ====================

class FlashDiskDB:
    """SQLite database on flash disk with automatic Firebase sync"""

    def __init__(self):
        self.db_path = self._detect_flash_disk()
        self._init_database()
        self._pending_syncs = []

    def _detect_flash_disk(self):
        """Auto-detect flash disk or use default location"""
        # Check common flash disk drive letters (Windows)
        possible_drives = ["D:", "E:", "F:", "G:", "H:", "I:", "J:", "K:"]

        for drive in possible_drives:
            if os.path.exists(drive):
                flash_folder = f"{drive}/ShepherdAcademyData"
                try:
                    os.makedirs(flash_folder, exist_ok=True)
                    test_file = f"{flash_folder}/test.txt"
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    return f"{flash_folder}/school_data.db"
                except:
                    continue

        # For Mac/Linux
        if os.path.exists("/Volumes"):
            for volume in os.listdir("/Volumes"):
                if volume not in ["Macintosh HD", "System"]:
                    flash_folder = f"/Volumes/{volume}/ShepherdAcademyData"
                    try:
                        os.makedirs(flash_folder, exist_ok=True)
                        return f"{flash_folder}/school_data.db"
                    except:
                        continue

        # Fallback to local hard drive
        fallback_path = os.path.join(os.path.expanduser("~"), "ShepherdAcademyData", "school_data.db")
        os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
        return fallback_path

    def _init_database(self):
        """Create all tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Pupils table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pupils (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                class TEXT NOT NULL,
                term_fees INTEGER DEFAULT 0,
                pupil_type TEXT DEFAULT 'Community Child',
                is_sponsored INTEGER DEFAULT 0,
                sponsor_reason TEXT,
                active INTEGER DEFAULT 1,
                archived INTEGER DEFAULT 0,
                enrollment_date TEXT,
                leaving_date TEXT,
                leaving_reason TEXT,
                last_modified TEXT
            )
        ''')

        # Ledger table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ledgers (
                id TEXT PRIMARY KEY,
                pupil_id TEXT NOT NULL,
                term TEXT NOT NULL,
                year INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT,
                balance INTEGER,
                previous_balance INTEGER,
                term_fees INTEGER,
                receipt_no TEXT,
                excess_amount INTEGER DEFAULT 0,
                payment_date TEXT,
                FOREIGN KEY (pupil_id) REFERENCES pupils(id)
            )
        ''')

        # Sync metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def save_pupil(self, pupil_data):
        """Save or update pupil"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO pupils 
            (id, name, class, term_fees, pupil_type, is_sponsored, sponsor_reason, 
             active, archived, enrollment_date, leaving_date, leaving_reason, last_modified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pupil_data.get('id'), pupil_data.get('name'), pupil_data.get('class'),
            pupil_data.get('term_fees', 0), pupil_data.get('pupil_type', 'Community Child'),
            1 if pupil_data.get('is_sponsored') else 0,
            pupil_data.get('sponsor_reason', ''),
            1 if pupil_data.get('active', True) else 0,
            1 if pupil_data.get('archived', False) else 0,
            pupil_data.get('enrollment_date'), pupil_data.get('leaving_date'),
            pupil_data.get('leaving_reason'), datetime.datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()
        return True

    def get_all_pupils(self, include_archived=False):
        """Get all pupils"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if include_archived:
            cursor.execute("SELECT * FROM pupils ORDER BY name")
        else:
            cursor.execute("SELECT * FROM pupils WHERE active = 1 ORDER BY name")

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_pupil_by_id(self, pupil_id):
        """Get single pupil"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pupils WHERE id = ?", (pupil_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def save_ledger_entry(self, ledger_data):
        """Save ledger entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO ledgers 
            (id, pupil_id, term, year, amount, description, balance, 
             previous_balance, term_fees, receipt_no, excess_amount, payment_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ledger_data.get('id'), ledger_data.get('pupil_id'), ledger_data.get('term'),
            ledger_data.get('year'), ledger_data.get('amount'), ledger_data.get('description'),
            ledger_data.get('balance'), ledger_data.get('previous_balance'),
            ledger_data.get('term_fees'), ledger_data.get('receipt_no'),
            ledger_data.get('excess_amount', 0), ledger_data.get('payment_date')
        ))

        conn.commit()
        conn.close()
        return True

    def get_ledger_entries(self, pupil_id, term, year):
        """Get ledger entries for a pupil"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM ledgers 
            WHERE pupil_id = ? AND term = ? AND year = ?
            ORDER BY payment_date
        ''', (pupil_id, term, year))

        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_last_sync(self):
        """Get last sync timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM sync_metadata WHERE key = 'last_sync'")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def set_last_sync(self, timestamp):
        """Set last sync timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
            VALUES ('last_sync', ?, ?)
        ''', (timestamp, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()


# ==================== FIREBASE HELPER ====================

def get_firebase_client():
    """Get Firebase client - cached"""
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
                return None
    return firestore.client()


db = get_firebase_client()


def is_firebase_available():
    """Check if Firebase is reachable"""
    if db is None:
        return False
    try:
        db.collection("test").limit(1).get()
        return True
    except:
        return False


# ==================== DATA SYNC MANAGER ====================

class SyncManager:
    """Manages sync between Firebase and Flash Disk"""

    def __init__(self, flash_db):
        self.flash_db = flash_db
        self.sync_in_progress = False

    def sync_from_firebase_to_flash(self):
        """Download all data from Firebase to flash disk"""
        if not is_firebase_available():
            return 0, "Firebase not available"

        try:
            # Get all pupils from Firebase
            pupils_ref = db.collection("pupils")
            pupils_docs = pupils_ref.stream()

            count = 0
            for doc in pupils_docs:
                pupil_data = doc.to_dict()
                pupil_data['id'] = doc.id
                self.flash_db.save_pupil(pupil_data)
                count += 1

                # Get ledger entries for this pupil
                for term in ["Term 1", "Term 2", "Term 3"]:
                    for year in [2024, 2025, 2026]:
                        ledger_ref = db.collection("ledgers").document(doc.id).collection(term)
                        payments = ledger_ref.where("year", "==", year).stream()
                        for payment in payments:
                            payment_data = payment.to_dict()
                            payment_data['id'] = payment.id
                            payment_data['pupil_id'] = doc.id
                            payment_data['term'] = term
                            payment_data['year'] = year
                            self.flash_db.save_ledger_entry(payment_data)

            self.flash_db.set_last_sync(datetime.datetime.now().isoformat())
            return count, "Sync completed successfully"

        except Exception as e:
            return 0, f"Sync error: {str(e)}"

    def sync_from_flash_to_firebase(self):
        """Upload flash disk data to Firebase"""
        if not is_firebase_available():
            return 0, "Firebase not available - offline mode"

        try:
            pupils = self.flash_db.get_all_pupils(include_archived=True)
            count = 0

            for pupil in pupils:
                # Update pupil in Firebase
                pupil_id = pupil.get('id')
                if pupil_id:
                    pupil_copy = pupil.copy()
                    pupil_copy.pop('id', None)
                    db.collection("pupils").document(pupil_id).set(pupil_copy)
                    count += 1

                # Update ledger entries
                for term in ["Term 1", "Term 2", "Term 3"]:
                    for year in [2024, 2025, 2026]:
                        entries = self.flash_db.get_ledger_entries(pupil_id, term, year)
                        for entry in entries:
                            entry_id = entry.get('id')
                            if entry_id:
                                entry_copy = entry.copy()
                                entry_copy.pop('id', None)
                                entry_copy.pop('pupil_id', None)
                                entry_copy.pop('term', None)
                                entry_copy.pop('year', None)
                                db.collection("ledgers").document(pupil_id).collection(term).document(entry_id).set(
                                    entry_copy)

            self.flash_db.set_last_sync(datetime.datetime.now().isoformat())
            return count, f"Uploaded {count} records to Firebase"

        except Exception as e:
            return 0, f"Upload error: {str(e)}"


# ==================== INITIALIZE FLASH DATABASE ====================

flash_db = FlashDiskDB()
sync_manager = SyncManager(flash_db)

# Auto-sync from Firebase to flash on first run
if flash_db.get_last_sync() is None and is_firebase_available():
    with st.spinner("Initial sync from Firebase to flash disk..."):
        count, msg = sync_manager.sync_from_firebase_to_flash()
        if count > 0:
            st.success(f"✅ {msg}")


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


# ==================== FEES MANAGER ====================

class FeesManager:
    def __init__(self):
        self.classes = ["Baby Class", "Middle Class", "Top Class", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
        self.terms = ["Term 1", "Term 2", "Term 3"]
        self.term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
        self.pupil_types = ["Community Child", "Staff Child", "Shepherd Child"]
        self.use_flash = True  # Always use flash as primary

    def _get_pupils_from_source(self, include_archived=False):
        """Get pupils from flash disk (primary source)"""
        return flash_db.get_all_pupils(include_archived)

    def _save_pupil_to_source(self, pupil_data):
        """Save pupil to flash disk"""
        return flash_db.save_pupil(pupil_data)

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
        """Calculate balance from previous term"""
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

        entries = flash_db.get_ledger_entries(pupil_id, prev_term, prev_year)
        if entries:
            return entries[-1].get('balance', 0)
        return 0

    def enroll_pupil(self, name, class_name, term_fees, pupil_type="Community Child"):
        """Enroll a new pupil"""
        try:
            pupil_id = str(uuid.uuid4())

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

            pupil_data = {
                "id": pupil_id,
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
                "leaving_reason": None
            }

            # Save to flash disk first
            self._save_pupil_to_source(pupil_data)

            # Try to sync to Firebase if online
            if is_firebase_available():
                try:
                    db.collection("pupils").document(pupil_id).set(pupil_data)
                except:
                    pass

            return pupil_id
        except Exception as e:
            st.error(f"Error enrolling pupil: {str(e)}")
            return None

    def get_pupil_details(self, pupil_id):
        """Get pupil details from flash disk"""
        return flash_db.get_pupil_by_id(pupil_id)

    def update_pupil(self, pupil_id, name, class_name, term_fees, pupil_type="Community Child"):
        """Update pupil details"""
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

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

            pupil_data.update({
                "name": name,
                "class": class_name,
                "term_fees": term_fees,
                "pupil_type": pupil_type,
                "is_sponsored": is_sponsored,
                "sponsor_reason": sponsor_reason,
                "last_modified": datetime.datetime.now().isoformat()
            })

            # Save to flash disk
            flash_db.save_pupil(pupil_data)

            # Try to sync to Firebase
            if is_firebase_available():
                try:
                    db.collection("pupils").document(pupil_id).update(pupil_data)
                except:
                    pass

            return True
        except Exception as e:
            st.error(f"Error updating pupil: {str(e)}")
            return False

    def archive_pupil(self, pupil_id, leaving_reason=""):
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

            pupil_data.update({
                "active": False,
                "archived": True,
                "leaving_date": datetime.datetime.now().isoformat(),
                "leaving_reason": leaving_reason
            })

            flash_db.save_pupil(pupil_data)

            if is_firebase_available():
                try:
                    db.collection("pupils").document(pupil_id).update({
                        "active": False,
                        "archived": True,
                        "leaving_date": datetime.datetime.now().isoformat(),
                        "leaving_reason": leaving_reason
                    })
                except:
                    pass

            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id):
        try:
            pupil_data = self.get_pupil_details(pupil_id)
            if not pupil_data:
                return False

            pupil_data.update({
                "active": True,
                "archived": False,
                "leaving_date": None,
                "leaving_reason": None
            })

            flash_db.save_pupil(pupil_data)

            if is_firebase_available():
                try:
                    db.collection("pupils").document(pupil_id).update({
                        "active": True,
                        "archived": False,
                        "leaving_date": None,
                        "leaving_reason": None
                    })
                except:
                    pass

            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    def get_pupils(self, class_name, include_archived=False):
        all_pupils = self._get_pupils_from_source(include_archived)
        return [p for p in all_pupils if p.get('class') == class_name]

    def get_all_pupils(self, include_archived=False):
        return self._get_pupils_from_source(include_archived)

    def get_archived_pupils(self):
        all_pupils = self._get_pupils_from_source(True)
        return [p for p in all_pupils if p.get('archived', False)]

    def get_ledger(self, pupil_id, term, year):
        return flash_db.get_ledger_entries(pupil_id, term, year)

    def add_payment(self, pupil_id, term, year, amount, description):
        """Add a payment"""
        try:
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
            total_paid_this_term = sum([p.get('amount', 0) for p in existing_payments])

            total_due = previous_balance + term_fees
            total_paid = total_paid_this_term + amount
            new_balance = total_due - total_paid

            excess_amount = 0
            if new_balance < 0:
                excess_amount = abs(new_balance)
                new_balance = 0

            transaction_id = str(uuid.uuid4())
            receipt_no = generate_receipt_number()

            ledger_data = {
                "id": transaction_id,
                "pupil_id": pupil_id,
                "term": term,
                "year": year_int,
                "amount": amount,
                "description": description,
                "balance": new_balance,
                "previous_balance": previous_balance,
                "term_fees": term_fees,
                "receipt_no": receipt_no,
                "excess_amount": excess_amount,
                "payment_date": datetime.datetime.now().isoformat()
            }

            # Save to flash disk
            flash_db.save_ledger_entry(ledger_data)

            # Try to sync to Firebase
            if is_firebase_available():
                try:
                    ledger_copy = ledger_data.copy()
                    ledger_copy.pop('id', None)
                    ledger_copy.pop('pupil_id', None)
                    ledger_copy.pop('term', None)
                    ledger_copy.pop('year', None)
                    db.collection("ledgers").document(pupil_id).collection(term).document(transaction_id).set(
                        ledger_copy)
                except:
                    pass

            return transaction_id, new_balance, receipt_no, previous_balance, excess_amount
        except Exception as e:
            st.error(f"Error adding payment: {str(e)}")
            return None, str(e), None, None, 0

    def get_pupil_term_summary(self, pupil_id, term, year):
        pupil_data = self.get_pupil_details(pupil_id)
        if not pupil_data:
            return None, 0, 0, 0, 0, 0, False, "", False, "Community Child"

        term_fees = pupil_data.get("term_fees", 0)
        is_sponsored = pupil_data.get("is_sponsored", False)
        sponsor_reason = pupil_data.get("sponsor_reason", "")
        is_archived = pupil_data.get("archived", False)
        pupil_type = pupil_data.get("pupil_type", "Community Child")

        if is_sponsored:
            term_fees = 0

        previous_balance = self.get_previous_term_balance(pupil_id, term, year)
        payments = self.get_ledger(pupil_id, term, year)
        total_paid = sum([p.get('amount', 0) for p in payments])

        total_due = previous_balance + term_fees
        balance = max(0, total_due - total_paid)
        credit_balance = previous_balance if previous_balance < 0 else 0

        return pupil_data, term_fees, total_paid, balance, previous_balance, credit_balance, is_sponsored, sponsor_reason, is_archived, pupil_type

    def get_class_summary(self, class_name, term, year, include_archived=False):
        pupils = self.get_pupils(class_name, include_archived)
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
            total_paid = sum([p.get('amount', 0) for p in payments])

            total_due = previous_balance + term_fees
            balance = max(0, total_due - total_paid)

            if is_archived:
                status = "Archived (Left School)"
            else:
                status = "Cleared" if balance == 0 else "Not Cleared"
                if is_sponsored:
                    status = f"Sponsored - {sponsor_reason}"

            pupil_info = {
                "Name": pupil["name"],
                "Pupil Type": pupil_type,
                "Previous Balance (UGX)": previous_balance,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if is_sponsored else "",
                "Leaving Date": pupil.get("leaving_date", ""),
                "Leaving Reason": pupil.get("leaving_reason", "")
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
        pupils = self.get_all_pupils(include_archived)
        all_summaries = []
        staff_summaries = []
        shepherd_summaries = []
        community_summaries = []

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
            total_paid = sum([p.get('amount', 0) for p in payments])

            total_due = previous_balance + term_fees
            balance = max(0, total_due - total_paid)

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
                "Previous Balance (UGX)": previous_balance,
                "Term Fees (UGX)": term_fees,
                "Total Due (UGX)": total_due,
                "Total Paid (UGX)": total_paid,
                "Balance (UGX)": balance,
                "Status": status,
                "Sponsor Reason": sponsor_reason if is_sponsored else "",
                "Leaving Date": pupil.get("leaving_date", ""),
                "Leaving Reason": pupil.get("leaving_reason", "")
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
        if not df_staff.empty:
            df_staff.insert(0, "No.", range(1, len(df_staff) + 1))
        if not df_shepherd.empty:
            df_shepherd.insert(0, "No.", range(1, len(df_shepherd) + 1))
        if not df_community.empty:
            df_community.insert(0, "No.", range(1, len(df_community) + 1))

        return df_all, df_staff, df_shepherd, df_community

    def get_dashboard_stats(self, term, year):
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
            total_paid = sum([p.get('amount', 0) for p in payments])
            stats["total_collected"] += total_paid

        stats["total_balance"] = stats["total_expected"] - stats["total_collected"]
        if stats["total_expected"] > 0:
            stats["collection_rate"] = (stats["total_collected"] / stats["total_expected"]) * 100

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

        # Show flash disk info
        st.info(f"💾 Flash Disk DB: {os.path.basename(os.path.dirname(flash_db.db_path))}\n📁 {flash_db.db_path}")

        with st.form(key="login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                # Simple authentication (you can expand this)
                if username == "bursar" and password == "bursar123":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "bursar"
                    st.rerun()
                elif username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = "admin"
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

        # ========== SYNC STATUS SECTION ==========
        st.markdown("### 💾 Storage & Sync")

        # Show flash disk location
        flash_folder = os.path.dirname(flash_db.db_path)
        st.caption(f"📀 Flash DB: {os.path.basename(flash_folder)}")

        # Show online/offline status
        if is_firebase_available():
            st.success("☁️ Firebase Online")
            st.caption("✅ Auto-sync enabled")
        else:
            st.warning("📴 Offline Mode")
            st.caption("⚠️ Working from flash disk only")

        # Show last sync time
        last_sync = flash_db.get_last_sync()
        if last_sync:
            st.caption(f"Last sync: {last_sync[:16]}")

        # Sync buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download from Cloud", use_container_width=True, key="download_btn"):
                with st.spinner("Downloading from Firebase..."):
                    count, msg = sync_manager.sync_from_firebase_to_flash()
                    if count > 0:
                        st.success(f"✅ Downloaded {count} records")
                        st.rerun()
                    else:
                        st.info(msg)

        with col2:
            if st.button("📤 Upload to Cloud", use_container_width=True, key="upload_btn"):
                if is_firebase_available():
                    with st.spinner("Uploading to Firebase..."):
                        count, msg = sync_manager.sync_from_flash_to_firebase()
                        if count > 0:
                            st.success(f"✅ Uploaded {count} records")
                        else:
                            st.info(msg)
                else:
                    st.error("Firebase not available - check internet")

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

    # ------------------- Dashboard -------------------
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #1E3A5F; margin-bottom: 1rem;'>Dashboard</h2>", unsafe_allow_html=True)

        stats = manager.get_dashboard_stats(current_term, current_year)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Pupils", stats["total_pupils"])
        col2.metric("Staff Children", stats["staff_children"])
        col3.metric("Shepherd Children", stats["shepherd_children"])
        col4.metric("Community Children", stats["community_children"])
        col5.metric("Total Collected", f"UGX {stats['total_collected']:,.0f}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Expected", f"UGX {stats['total_expected']:,.0f}")
        col2.metric("Total Balance", f"UGX {stats['total_balance']:,.0f}")
        col3.metric("Collection Rate", f"{stats['collection_rate']:.1f}%")

        if stats["collection_rate"] > 0:
            st.progress(stats["collection_rate"] / 100)

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
            pupil_type = st.selectbox("Pupil Type *", ["Community Child", "Staff Child", "Shepherd Child"],
                                      key="enroll_type")
        with col2:
            term_fees = st.number_input("Fees Per Term (UGX) *", min_value=0, step=0, value=500000, key="enroll_fees",
                                        placeholder="0", disabled=(pupil_type == "Shepherd Child"))

            if pupil_type == "Shepherd Child":
                st.info("🎓 Shepherd Child - No fees required")
            elif pupil_type == "Staff Child":
                st.info("👨‍🏫 Staff Child - Can enter 0 fees if applicable")

        if st.button("Enroll Pupil", use_container_width=True):
            if pupil_name:
                actual_fees = 0 if pupil_type == "Shepherd Child" else term_fees
                pupil_id = manager.enroll_pupil(pupil_name, pupil_class, actual_fees, pupil_type)
                if pupil_id:
                    st.success(f"✅ {pupil_name} has been successfully enrolled as a {pupil_type}!")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("Please fill all required fields")

    # ------------------- Pupils & Ledgers -------------------
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
                is_sponsored = pupil.get("is_sponsored", False)
                sponsor_reason = pupil.get("sponsor_reason", "")
                pupil_type = pupil.get("pupil_type", "Community Child")

                previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                ledger_entries = manager.get_ledger(pupil_id, current_term, current_year)
                total_paid_this_term = sum([p.get("amount", 0) for p in ledger_entries])

                if previous_balance < 0:
                    show_credit = True
                    show_carry_over = False
                    carry_over_amount = abs(previous_balance)
                elif previous_balance > 0:
                    show_credit = False
                    show_carry_over = True
                    carry_over_amount = previous_balance
                else:
                    show_credit = False
                    show_carry_over = False
                    carry_over_amount = 0

                current_balance = max(0, (
                    previous_balance if previous_balance > 0 else 0) + term_fees - total_paid_this_term)

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
                        "Date": entry.get("payment_date", ""),
                        "Amount Paid": f"UGX {entry.get('amount', 0):,.0f}",
                        "Description": entry.get("description", "Payment"),
                        "Balance After": f"UGX {entry.get('balance', 0):,.0f}",
                        "Receipt No": entry.get("receipt_no", "")
                    })

                if is_archived:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — [ARCHIVED]"
                elif is_sponsored:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — 🎓 SPONSORED"
                else:
                    if show_credit:
                        expander_title = f"📌 {pupil['name']} — {pupil_type} — 💳 Credit: UGX {carry_over_amount:,.0f} | Balance: UGX {current_balance:,.0f}"
                    elif show_carry_over:
                        expander_title = f"📌 {pupil['name']} — {pupil_type} — ⚠️ Carry-over: UGX {carry_over_amount:,.0f} | Balance: UGX {current_balance:,.0f}"
                    else:
                        expander_title = f"📌 {pupil['name']} — {pupil_type} — Term: UGX {term_fees:,.0f} | Paid: UGX {total_paid_this_term:,.0f} | Balance: UGX {current_balance:,.0f}"

                with st.expander(expander_title):
                    if is_archived:
                        st.warning(f"🏁 This pupil has left the school")
                    if is_sponsored:
                        st.info(f"🎓 Sponsored Child - Reason: {sponsor_reason}")
                    if show_carry_over:
                        st.warning(f"⚠️ Balance brought forward: UGX {carry_over_amount:,.0f}")
                    elif show_credit:
                        st.success(f"✅ Credit brought forward: UGX {carry_over_amount:,.0f}")

                    if all_transactions:
                        df = pd.DataFrame(all_transactions)
                        st.dataframe(df, use_container_width=True)

                        if ledger_entries:
                            st.markdown("---")
                            st.markdown("### 📄 Payment Receipts")
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

                        csv = df.to_csv(index=False).encode()
                        st.download_button("📥 Download Ledger (CSV)", csv, f"{pupil['name']}_ledger.csv", "text/csv")
                    else:
                        st.info(f"No payments recorded yet for {current_term}, {current_year}")

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
                    is_sponsored = pupil_data.get("is_sponsored", False)
                    is_archived = pupil_data.get("archived", False)

                    if is_archived:
                        st.error("This pupil has left the school. Cannot record payments for archived pupils.")
                    elif is_sponsored:
                        st.warning("This is a sponsored child. No payment is required.")
                    else:
                        previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                        existing_payments = manager.get_ledger(pupil_id, current_term, current_year)
                        total_paid_this_term = sum([p.get('amount', 0) for p in existing_payments])

                        total_due = max(0, previous_balance) + term_fees
                        current_balance = max(0, total_due - total_paid_this_term)

                        st.markdown("### Pupil Information")
                        col1, col2, col3, col4, col5 = st.columns(5)
                        col1.metric("Pupil Name", pupil_name)
                        col2.metric("Class", pupil_data['class'])
                        col3.metric("Previous Balance", f"UGX {max(0, previous_balance):,.0f}")
                        col4.metric("Term Fees", f"UGX {term_fees:,.0f}")
                        col5.metric("Due This Term", f"UGX {current_balance:,.0f}")

                        if previous_balance < 0:
                            st.success(f"✅ Credit Balance: UGX {abs(previous_balance):,.0f}")

                        st.markdown("---")

                        col1, col2 = st.columns(2)
                        with col1:
                            amount_paid = st.number_input("Amount (UGX)", min_value=0, step=0, value=0,
                                                          key="payment_amount")
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
                                        st.info(f"💰 Excess payment of UGX {excess_amount:,.0f} carried forward!")
                                    else:
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded!")

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
            elif report_type == "Cleared Only":
                df_to_show = df_cleared
            elif report_type == "With Balance":
                df_to_show = df_not_cleared
            else:
                df_to_show = df_archived

            if not df_to_show.empty:
                st.dataframe(df_to_show, use_container_width=True)

                if not df_full.empty:
                    chart_data = df_full[df_full["Status"] != "Archived (Left School)"]
                    if not chart_data.empty:
                        fig = px.bar(chart_data, x="Name", y=["Total Paid (UGX)", "Balance (UGX)"],
                                     title=f"Fee Overview - {selected_class} ({current_term} {current_year})",
                                     barmode="group", color_discrete_sequence=['#28A745', '#DC3545'])
                        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')
                        st.plotly_chart(fig, use_container_width=True)

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
                    pdf_buffer = export_summary_to_pdf(df_to_show, f"{selected_class} Report", "report.pdf")
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
            filter_type = st.selectbox("Filter by Pupil Type",
                                       ["All", "Staff Child", "Shepherd Child", "Community Child"], key="filter_type")
        with col_filter2:
            filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes, key="filter_class")
        with col_filter3:
            filter_status = st.selectbox("Filter by Status", ["All", "Cleared", "Not Cleared"], key="filter_status")

        if st.button("Generate School Summary", key="school_summary"):
            df_all, df_staff, df_shepherd, df_community = manager.get_school_wide_summary(current_term, current_year,
                                                                                          include_archived=st.session_state.show_archived)

            if filter_type == "Staff Child":
                df_to_show = df_staff
            elif filter_type == "Shepherd Child":
                df_to_show = df_shepherd
            elif filter_type == "Community Child":
                df_to_show = df_community
            else:
                df_to_show = df_all

            if filter_class != "All Classes" and not df_to_show.empty:
                df_to_show = df_to_show[df_to_show["Class"] == filter_class]
            if filter_status != "All" and not df_to_show.empty:
                df_to_show = df_to_show[df_to_show["Status"] == filter_status]

            if not df_to_show.empty:
                st.dataframe(df_to_show, use_container_width=True)

                st.markdown("### Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)

                total_expected = df_to_show["Total Due (UGX)"].sum() if "Total Due (UGX)" in df_to_show.columns else 0
                total_paid = df_to_show["Total Paid (UGX)"].sum() if "Total Paid (UGX)" in df_to_show.columns else 0

                col1.metric("Total Pupils", len(df_to_show))
                col2.metric("Total Expected", f"UGX {total_expected:,.0f}")
                col3.metric("Total Paid", f"UGX {total_paid:,.0f}")

                if total_expected > 0:
                    collection_rate = (total_paid / total_expected) * 100
                    col4.metric("Collection Rate", f"{collection_rate:.1f}%")
                    st.progress(collection_rate / 100)

                st.markdown("### Pupil Type Breakdown")
                type_col1, type_col2, type_col3 = st.columns(3)
                type_col1.metric("Staff Children", len(df_staff))
                type_col2.metric("Shepherd Children", len(df_shepherd))
                type_col3.metric("Community Children", len(df_community))

                st.markdown("---")
                st.subheader("Export Options")
                csv = df_to_show.to_csv(index=False).encode()
                st.download_button("📊 Download Report (CSV)", csv, f"school_wide_{current_term}_{current_year}.csv",
                                   "text/csv")
            else:
                st.warning("No data available for the selected filters")

    # ------------------- Manage Pupils -------------------
    elif menu == "Manage Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Manage Pupils</h1>", unsafe_allow_html=True)

        all_pupils = manager.get_all_pupils(include_archived=False)

        if not all_pupils:
            st.info("No active pupils found")
        else:
            st.markdown("### 🔍 Filter Pupils")
            col_filter1, col_filter2, col_filter3 = st.columns(3)

            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes,
                                            key="filter_manage_class")
            with col_filter2:
                filter_type = st.selectbox("Filter by Pupil Type",
                                           ["All", "Staff Child", "Shepherd Child", "Community Child"],
                                           key="filter_manage_type")
            with col_filter3:
                search_term = st.text_input("Search by Name", placeholder="Type pupil name to search...",
                                            key="search_pupil")

            pupil_dicts = [p for p in all_pupils]

            if filter_class != "All Classes":
                pupil_dicts = [p for p in pupil_dicts if p.get("class") == filter_class]
            if filter_type != "All":
                pupil_dicts = [p for p in pupil_dicts if p.get("pupil_type", "Community Child") == filter_type]
            if search_term:
                pupil_dicts = [p for p in pupil_dicts if search_term.lower() in p.get("name", "").lower()]

            if not pupil_dicts:
                st.warning("No pupils found matching the criteria")
            else:
                st.markdown(f"### Found {len(pupil_dicts)} pupil(s)")

                for pupil in pupil_dicts:
                    pupil_type = pupil.get("pupil_type", "Community Child")

                    with st.expander(
                            f"📌 {pupil['name']} - {pupil['class']} (Fees: UGX {pupil.get('term_fees', 0):,.0f})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"""
                            **Current Information:**
                            - **Name:** {pupil['name']}
                            - **Class:** {pupil['class']}
                            - **Pupil Type:** {pupil_type}
                            - **Term Fees:** UGX {pupil.get('term_fees', 0):,.0f}
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
                        st.markdown("### ✏️ Edit Pupil Details")
                        with st.form(key=f"edit_form_{pupil['id']}"):
                            new_name = st.text_input("Name", pupil['name'], key=f"name_{pupil['id']}")
                            new_class = st.selectbox("Class", manager.classes,
                                                     index=manager.classes.index(pupil['class']) if pupil[
                                                                                                        'class'] in manager.classes else 0,
                                                     key=f"class_{pupil['id']}")
                            new_type = st.selectbox("Pupil Type", ["Community Child", "Staff Child", "Shepherd Child"],
                                                    index=["Community Child", "Staff Child", "Shepherd Child"].index(
                                                        pupil_type) if pupil_type in ["Community Child", "Staff Child",
                                                                                      "Shepherd Child"] else 0,
                                                    key=f"type_{pupil['id']}")

                            default_fees = 0 if new_type == "Shepherd Child" else pupil.get('term_fees', 0)
                            new_fees = st.number_input("Term Fees (UGX)", value=int(default_fees), step=50000,
                                                       key=f"fees_{pupil['id']}",
                                                       disabled=(new_type == "Shepherd Child"))

                            col_edit, col_archive = st.columns(2)

                            with col_edit:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    manager.update_pupil(pupil['id'], new_name, new_class, new_fees, new_type)
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
                                            st.rerun()
                                    else:
                                        st.error("Please provide a reason for leaving")

    # ------------------- Archived Pupils -------------------
    elif menu == "Archived Pupils":
        st.markdown("<h1 style='color: #1E3A5F;'>Archived Pupils (Left School)</h1>", unsafe_allow_html=True)
        st.info("These pupils have left the school. Their historical payment records are preserved.")

        archived_pupils = manager.get_archived_pupils()

        if not archived_pupils:
            st.info("No archived pupils found.")
        else:
            for pupil in archived_pupils:
                with st.expander(
                        f"📌 {pupil['name']} - {pupil['class']} (Left: {pupil.get('leaving_date', 'Unknown')[:10] if pupil.get('leaving_date') else 'Unknown'})"):
                    st.markdown(f"**Reason:** {pupil.get('leaving_reason', 'Not specified')}")
                    if role == "bursar":
                        if st.button(f"🔄 Restore Pupil", key=f"restore_{pupil['id']}"):
                            if manager.restore_pupil(pupil['id']):
                                st.success(f"✅ {pupil['name']} restored!")
                                st.rerun()


def main():
    if not st.session_state.get("logged_in", False):
        login_page()
    else:
        main_app()


if __name__ == "__main__":
    main()