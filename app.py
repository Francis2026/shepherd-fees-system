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

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Shepherd Academy | Fees Management",
    layout="wide",
    page_icon=":school:",
    initial_sidebar_state="expanded"
)

# ========== SESSION STATE INITIALIZATION ==========
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
    st.session_state.initialized_terms = {}

# ========== SUPABASE INITIALIZATION ==========
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

# ========== CACHE SYSTEM ==========
class SmartCache:
    def __init__(self):
        self.cache = {}
        self.ttl_config = {"pupils": 1200, "ledger": 300, "stats": 600, "summary": 900, "enrollments": 600}

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

# ========== HELPER FUNCTIONS ==========
def get_logo_base64():
    logo_files = ["images.jfif", "school_logo.jpg", "school_logo.png", "logo.jpg", "logo.png"]
    for logo_file in logo_files:
        if os.path.exists(logo_file):
            try:
                with open(logo_file, "rb") as img_file:
                    img_data = img_file.read()
                    mime_type = "image/png" if logo_file.endswith('.png') else "image/jpeg"
                    return base64.b64encode(img_data).decode(), mime_type
            except:
                continue
    return None, None

def display_main_header():
    logo_base64, mime_type = get_logo_base64()
    if logo_base64:
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: white; border-radius: 0 0 20px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <div>
                <h2 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h2>
                <p style="color: #6C757D; margin: 0;">School Fees Management System</p>
            </div>
            <img src="data:{mime_type};base64,{logo_base64}" style="height: 50px; border-radius: 10px;">
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: white; border-radius: 0 0 20px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <div>
                <h2 style="color: #1E3A5F; margin: 0;">SHEPHERD ACADEMY BUSIU</h2>
                <p style="color: #6C757D; margin: 0;">School Fees Management System</p>
            </div>
            <div style="background: linear-gradient(135deg, #1E3A5F, #2E5A8A); width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 24px;">🏫</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_receipt_number():
    return f"RCP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"

def safe_value(val, default=0):
    """Safely convert None to default value"""
    return val if val is not None else default

def generate_pdf_receipt(school_name, logo_path, receipt_num, date_str, child_name, amount, description, balance,
                         previous_balance, term_fees, signature_text, excess_amount=0):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    amount = safe_value(amount, 0)
    balance = safe_value(balance, 0)
    previous_balance = safe_value(previous_balance, 0)
    term_fees = safe_value(term_fees, 0)
    excess_amount = safe_value(excess_amount, 0)

    try:
        if os.path.exists(logo_path):
            c.drawImage(logo_path, 50, height - 80, width=60, height=60, preserveAspectRatio=True)
    except:
        pass

    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.12, 0.23, 0.37)
    c.drawString(120, height - 60, school_name)
    c.setFont("Helvetica", 10)
    c.drawString(120, height - 80, "P.O. Box 1400, Busiu - Uganda | Tel: +256779462142 (Director)")
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

# ========== CLASS PROGRESSION ==========
CLASS_PROGRESSION = {
    "Baby Class": "Middle Class", "Middle Class": "Top Class", "Top Class": "P1",
    "P1": "P2", "P2": "P3", "P3": "P4", "P4": "P5", "P5": "P6", "P6": "P7", "P7": None
}

# ========== FEES MANAGER ==========
class FeesManager:
    def __init__(self):
        self.classes = list(CLASS_PROGRESSION.keys())
        self.terms = ["Term 1", "Term 2", "Term 3"]
        self.term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
        self.pupil_types = ["Community Child", "Staff Child", "Shepherd Child"]

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

    def is_pupil_enrolled_in_term(self, pupil_id, term, year):
        if supabase is None:
            return False
        try:
            result = supabase.table("term_enrollments").select("id") \
                .eq("pupil_id", pupil_id) .eq("term", term) .eq("year", year) .eq("is_active", True).execute()
            return len(result.data) > 0
        except:
            return False

    def get_pupils_for_term(self, class_name, term, year, include_archived=False):
        if supabase is None:
            return []
        try:
            result = supabase.table("term_enrollments") \
                .select("pupil_id, pupils(*)") \
                .eq("term", term) .eq("year", year) .eq("is_active", True).execute()
            pupils = []
            for item in result.data:
                pupil = item.get("pupils", {})
                if pupil:
                    if class_name == "All Classes" or pupil.get("class") == class_name:
                        if not include_archived and pupil.get("archived", False):
                            continue
                        pupils.append(pupil)
            return pupils
        except Exception as e:
            st.error(f"Error getting pupils for term: {str(e)}")
            return []

    def get_term_closing_balance(self, pupil_id, term, year):
        if supabase is None:
            return 0
        try:
            result = supabase.table("payments").select("balance, excess_amount") \
                .eq("pupil_id", pupil_id) .eq("term", term) .eq("year", year) \
                .order("payment_date", desc=True).limit(1).execute()
            if result.data:
                last_entry = result.data[0]
                balance = safe_value(last_entry.get("balance"), 0)
                excess = safe_value(last_entry.get("excess_amount"), 0)
                if balance == 0 and excess > 0:
                    return -excess
                return balance
            return 0
        except:
            return 0

    def get_previous_term_balance(self, pupil_id, current_term, current_year):
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
        return self.get_term_closing_balance(pupil_id, prev_term, prev_year)

    def get_ledger(self, pupil_id, term, year):
        cache_key = f"ledger_{pupil_id}_{term}_{year}"
        cached = cache.get(cache_key, "ledger")
        if cached is not None:
            return cached
        if supabase is None:
            return []
        try:
            result = supabase.table("payments").select("*") \
                .eq("pupil_id", pupil_id) .eq("term", term) .eq("year", int(year)) \
                .order("payment_date").execute()
            payments = result.data
            cache.set(cache_key, payments, "ledger")
            return payments
        except:
            return []

    def enroll_pupil(self, name, class_name, term_fees, pupil_type, current_term, current_year):
        if supabase is None:
            return None
        try:
            if pupil_type == "Shepherd Child":
                is_sponsored, sponsor_reason, term_fees = True, "Shepherd Child", 0
            elif pupil_type == "Staff Child":
                is_sponsored, sponsor_reason = False, "Staff Child"
            else:
                is_sponsored, sponsor_reason = False, ""

            pupil_id = str(uuid.uuid4())
            pupil_data = {
                "id": pupil_id, "name": name, "class": class_name, "term_fees": term_fees,
                "pupil_type": pupil_type, "is_sponsored": is_sponsored, "sponsor_reason": sponsor_reason,
                "active": True, "archived": False, "enrollment_term": current_term, "enrollment_year": current_year,
                "current_term": current_term, "current_year": current_year
            }
            supabase.table("pupils").insert(pupil_data).execute()
            supabase.table("term_enrollments").insert({
                "pupil_id": pupil_id, "term": current_term, "year": current_year,
                "is_active": True, "enrolled_at": datetime.datetime.now().isoformat()
            }).execute()
            cache.invalidate(data_type="pupils")
            cache.invalidate(data_type="stats")
            cache.invalidate(data_type="enrollments")
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
                is_sponsored, sponsor_reason, term_fees = True, "Shepherd Child", 0
            elif pupil_type == "Staff Child":
                is_sponsored, sponsor_reason = False, "Staff Child"
            else:
                is_sponsored, sponsor_reason = False, ""
            supabase.table("pupils").update({
                "name": name, "class": class_name, "term_fees": term_fees,
                "pupil_type": pupil_type, "is_sponsored": is_sponsored, "sponsor_reason": sponsor_reason
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
            supabase.table("term_enrollments").update({"is_active": False}).eq("pupil_id", pupil_id).execute()
            supabase.table("pupils").update({
                "active": False, "archived": True,
                "leaving_date": datetime.datetime.now().isoformat(), "leaving_reason": leaving_reason
            }).eq("id", pupil_id).execute()
            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            cache.invalidate(data_type="enrollments")
            return True
        except Exception as e:
            st.error(f"Error archiving pupil: {str(e)}")
            return False

    def restore_pupil(self, pupil_id, return_term, return_year):
        if supabase is None:
            return False
        try:
            supabase.table("pupils").update({
                "active": True, "archived": False, "current_term": return_term, "current_year": return_year
            }).eq("id", pupil_id).execute()
            supabase.table("term_enrollments").insert({
                "pupil_id": pupil_id, "term": return_term, "year": return_year,
                "is_active": True, "enrolled_at": datetime.datetime.now().isoformat()
            }).execute()
            cache.invalidate(data_type="pupils")
            cache.invalidate(f"pupil_{pupil_id}")
            cache.invalidate(data_type="enrollments")
            return True
        except Exception as e:
            st.error(f"Error restoring pupil: {str(e)}")
            return False

    def initialize_existing_pupils_for_term(self, term, year):
        if supabase is None:
            return 0
        try:
            init_key = f"{term}_{year}"
            if st.session_state.initialized_terms.get(init_key, False):
                return 0
            pupils = self.get_all_pupils(include_archived=False)
            initialized_count = 0
            term_order = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
            current_term_num = term_order.get(term, 1)
            for pupil in pupils:
                enrollment_term = pupil.get("enrollment_term", "Term 1")
                enrollment_year = pupil.get("enrollment_year", year)
                enrollment_term_num = term_order.get(enrollment_term, 1)
                if enrollment_year < year:
                    should_enroll = True
                elif enrollment_year == year:
                    should_enroll = (current_term_num >= enrollment_term_num)
                else:
                    should_enroll = False
                if not should_enroll:
                    continue
                existing = supabase.table("term_enrollments").select("*") \
                    .eq("pupil_id", pupil["id"]) .eq("term", term) .eq("year", year).execute()
                if not existing.data:
                    supabase.table("term_enrollments").insert({
                        "pupil_id": pupil["id"], "term": term, "year": year,
                        "is_active": True, "enrolled_at": datetime.datetime.now().isoformat()
                    }).execute()
                    initialized_count += 1
            if initialized_count > 0:
                cache.invalidate(data_type="enrollments")
                cache.invalidate(data_type="stats")
            st.session_state.initialized_terms[init_key] = True
            return initialized_count
        except Exception as e:
            st.error(f"Error initializing term data: {str(e)}")
            return 0

    def enroll_pupil_into_term(self, pupil_id, to_term, to_year, from_term, from_year):
        if supabase is None:
            return False
        try:
            existing = supabase.table("term_enrollments").select("*") \
                .eq("pupil_id", pupil_id) .eq("term", to_term) .eq("year", to_year).execute()
            if existing.data:
                return True
            pupil = self.get_pupil_details(pupil_id)
            if not pupil:
                return False
            previous_balance = self.get_term_closing_balance(pupil_id, from_term, from_year)
            supabase.table("term_enrollments").insert({
                "pupil_id": pupil_id, "term": to_term, "year": to_year,
                "is_active": True, "enrolled_at": datetime.datetime.now().isoformat()
            }).execute()
            supabase.table("pupils").update({
                "current_term": to_term, "current_year": to_year
            }).eq("id", pupil_id).execute()
            if previous_balance != 0:
                term_fees = safe_value(pupil.get("term_fees"), 0)
                receipt_no = f"BAL-CF-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                source_desc = f"{from_term} {from_year}"
                if previous_balance < 0:
                    credit_amount = abs(previous_balance)
                    supabase.table("payments").insert({
                        "id": str(uuid.uuid4()), "pupil_id": pupil_id, "term": to_term, "year": int(to_year),
                        "amount": 0, "description": f"Credit carried forward from {source_desc}",
                        "balance": previous_balance, "previous_balance": 0, "term_fees": term_fees,
                        "receipt_no": receipt_no, "excess_amount": credit_amount,
                        "payment_date": datetime.datetime.now().isoformat()
                    }).execute()
                else:
                    supabase.table("payments").insert({
                        "id": str(uuid.uuid4()), "pupil_id": pupil_id, "term": to_term, "year": int(to_year),
                        "amount": 0, "description": f"Balance carried forward from {source_desc}",
                        "balance": previous_balance, "previous_balance": previous_balance, "term_fees": term_fees,
                        "receipt_no": receipt_no, "excess_amount": 0,
                        "payment_date": datetime.datetime.now().isoformat()
                    }).execute()
            cache.invalidate(data_type="pupils")
            cache.invalidate(data_type="ledger")
            cache.invalidate(data_type="summary")
            cache.invalidate(data_type="enrollments")
            return True
        except Exception as e:
            st.error(f"Error enrolling pupil into term: {str(e)}")
            return False

    def add_payment(self, pupil_id, term, year, amount, description):
        if supabase is None:
            return None, "Database not connected", None, None, 0
        try:
            result = supabase.rpc("process_payment", {
                "p_pupil_id": pupil_id, "p_term": term, "p_year": int(year),
                "p_amount": amount, "p_description": description
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
                "p_class": class_name, "p_term": term, "p_year": int(year), "p_include_archived": include_archived
            }).execute()
            summary_data = result.data
            df_summary = pd.DataFrame(summary_data).reset_index(drop=True)
            if not df_summary.empty:
                df_summary.insert(0, "No.", range(1, len(df_summary) + 1))
            df_cleared = df_summary[df_summary["status"] == "Cleared"] if not df_summary.empty else pd.DataFrame()
            df_not_cleared = df_summary[df_summary["status"] == "Not Cleared"] if not df_summary.empty else pd.DataFrame()
            df_archived = df_summary[df_summary["status"].str.contains("Archived", na=False)] if not df_summary.empty else pd.DataFrame()
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
                    "p_class": class_name, "p_term": term, "p_year": int(year), "p_include_archived": include_archived
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
            return {"total_pupils": 0, "staff_children": 0, "shepherd_children": 0, "community_children": 0,
                    "total_expected": 0, "total_collected": 0, "total_balance": 0, "collection_rate": 0}
        try:
            enrolled_pupils = []
            result = supabase.table("term_enrollments") \
                .select("pupil_id, pupils(*)") .eq("term", term) .eq("year", int(year)) .eq("is_active", True).execute()
            for item in result.data:
                pupil = item.get("pupils", {})
                if pupil and not pupil.get("archived", False):
                    enrolled_pupils.append(pupil)
            stats = {"total_pupils": len(enrolled_pupils), "staff_children": 0, "shepherd_children": 0,
                     "community_children": 0, "total_expected": 0, "total_collected": 0, "total_balance": 0, "collection_rate": 0}
            for pupil in enrolled_pupils:
                pupil_type = pupil.get("pupil_type", "Community Child")
                term_fees = safe_value(pupil.get("term_fees"), 0)
                if pupil.get("is_sponsored", False):
                    term_fees = 0
                if pupil_type == "Staff Child":
                    stats["staff_children"] += 1
                elif pupil_type == "Shepherd Child":
                    stats["shepherd_children"] += 1
                else:
                    stats["community_children"] += 1
                stats["total_expected"] += term_fees
                result = supabase.table("payments").select("amount") \
                    .eq("pupil_id", pupil.get("id")) .eq("term", term) .eq("year", int(year)).execute()
                total_paid = sum([safe_value(p.get("amount"), 0) for p in result.data])
                stats["total_collected"] += total_paid
            stats["total_balance"] = stats["total_expected"] - stats["total_collected"]
            if stats["total_expected"] > 0:
                stats["collection_rate"] = (stats["total_collected"] / stats["total_expected"]) * 100
            cache.set(cache_key, stats, "stats")
            return stats
        except Exception as e:
            st.error(f"Error getting dashboard stats: {str(e)}")
            return {"total_pupils": 0, "staff_children": 0, "shepherd_children": 0, "community_children": 0,
                    "total_expected": 0, "total_collected": 0, "total_balance": 0, "collection_rate": 0}

# ========== AUTHENTICATION ==========
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

# ========== LOGIN PAGE ==========
def login_page():
    if not st.session_state.get("login_loaded", False):
        with st.spinner("Loading Shepherd Academy School Fees Management System..."):
            time.sleep(0.5)
        st.session_state.login_loaded = True
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        logo_base64, mime_type = get_logo_base64()
        if logo_base64:
            st.image(f"data:{mime_type};base64,{logo_base64}", width=150)
        else:
            st.markdown("<h1 style='text-align: center; color: #1E3A5F;'>🏫 SHEPHERD ACADEMY BUSIU</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>School Fees Management System</h3>", unsafe_allow_html=True)
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

# ========== MAIN APP ==========
def main_app():
    display_main_header()
    with st.sidebar:
        role = st.session_state["role"]
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown(f"**Role:** {role.upper()}")
        st.markdown("---")
        st.markdown("### Navigation")
        if role == "bursar":
            nav_options = ["Dashboard", "Enroll Pupil", "Pupils & Ledgers", "Record Payment",
                           "Class Reports", "School Reports", "Manage Pupils", "Archived Pupils"]
        else:
            nav_options = ["Dashboard", "Pupils & Ledgers", "Class Reports", "School Reports"]
        menu = st.radio("Menu", nav_options, label_visibility="collapsed")
        st.markdown("---")
        st.markdown("### Period")
        current_term = st.selectbox("Term", ["Term 1", "Term 2", "Term 3"], key="global_term")
        current_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.datetime.now().year, step=1)
        st.markdown("---")
        if role == "bursar":
            st.markdown("### 📋 Term Enrollment")
            term_order_list = ["Term 1", "Term 2", "Term 3"]
            try:
                current_idx = term_order_list.index(current_term)
            except:
                current_idx = 0
            if current_idx == 0:
                prev_term, prev_year = "Term 3", current_year - 1
            else:
                prev_term, prev_year = term_order_list[current_idx - 1], current_year
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
        if role == "bursar":
            init_key = f"{current_term}_{current_year}"
            if not st.session_state.initialized_terms.get(init_key, False):
                with st.spinner(f"Initializing term data for {current_term} {current_year}..."):
                    initialized = manager.initialize_existing_pupils_for_term(current_term, current_year)
                    if initialized > 0:
                        st.success(f"✅ Initialized {initialized} existing pupils for {current_term} {current_year}")
                    time.sleep(0.5)
                    st.rerun()
        if st.session_state.get("show_enrollment_dialog", False):
            with st.expander("📋 Enroll Pupils", expanded=True):
                prev_pupils = manager.get_pupils_for_term("All Classes", st.session_state.enroll_from_term, st.session_state.enroll_from_year, include_archived=False)
                st.subheader(f"Enroll from {st.session_state.enroll_from_term} {st.session_state.enroll_from_year} to {st.session_state.enroll_to_term} {st.session_state.enroll_to_year}")
                selected_pupils = []
                for pupil in prev_pupils:
                    already_enrolled = manager.is_pupil_enrolled_in_term(pupil.get("id"), st.session_state.enroll_to_term, st.session_state.enroll_to_year)
                    if already_enrolled:
                        st.info(f"✅ {pupil['name']} ({pupil['class']}) - Already enrolled")
                    else:
                        if st.checkbox(f"Enroll {pupil['name']} ({pupil['class']})", key=f"enroll_{pupil['id']}"):
                            selected_pupils.append(pupil)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Enroll Selected ({len(selected_pupils)} pupils)", use_container_width=True):
                        for pupil in selected_pupils:
                            manager.enroll_pupil_into_term(pupil['id'], st.session_state.enroll_to_term, st.session_state.enroll_to_year, st.session_state.enroll_from_term, st.session_state.enroll_from_year)
                        st.success(f"✅ Enrolled {len(selected_pupils)} pupils into {st.session_state.enroll_to_term} {st.session_state.enroll_to_year}")
                        st.session_state.show_enrollment_dialog = False
                        cache.clear_all()
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_enrollment_dialog = False
                        st.rerun()
        if role == "bursar" and menu in ["Pupils & Ledgers", "Class Reports", "School Reports"]:
            show_archived = st.checkbox("Show Archived Pupils", value=st.session_state.get("show_archived", False), key="show_archived_checkbox")
            st.session_state.show_archived = show_archived
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["logged_in", "username", "role", "navigation_menu", "show_archived", "initialized_terms"]:
                if key in st.session_state:
                    del st.session_state[key]
            cache.clear_all()
            st.rerun()

    # ========== DASHBOARD ==========
    if menu == "Dashboard":
        st.markdown("<h2 style='color: #1E3A5F;'>Dashboard</h2>", unsafe_allow_html=True)
        stats = manager.get_dashboard_stats(current_term, current_year)
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("📚 Total Pupils", stats['total_pupils'])
        with col2:
            st.metric("👩‍🏫 Staff Children", stats['staff_children'])
        with col3:
            st.metric("🙏 Shepherd Children", stats['shepherd_children'])
        with col4:
            st.metric("🏠 Community Children", stats['community_children'])
        with col5:
            st.metric("💰 Total Collected", f"UGX {stats['total_collected']:,.0f}")
        with col6:
            st.metric("📊 Collection Rate", f"{stats['collection_rate']:.1f}%")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Total Expected", f"UGX {stats['total_expected']:,.0f}")
        with col2:
            st.metric("⚠️ Total Balance", f"UGX {stats['total_balance']:,.0f}")
        with col3:
            if stats["collection_rate"] > 0:
                st.progress(stats["collection_rate"] / 100)
        st.markdown("---")
        st.markdown("### Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Enroll New Pupil", use_container_width=True):
                st.session_state.navigation_menu = "Enroll Pupil"
                st.rerun()
        with col2:
            if st.button("💰 Record Payment", use_container_width=True):
                st.session_state.navigation_menu = "Record Payment"
                st.rerun()

    # ========== ENROLL PUPIL ==========
    elif menu == "Enroll Pupil" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Enroll New Pupil</h1>", unsafe_allow_html=True)
        st.caption(f"Enrolling for: **{current_term} {current_year}**")
        col1, col2 = st.columns(2)
        with col1:
            pupil_name = st.text_input("Full Name *", placeholder="Enter pupil's full name", key="enroll_name")
            pupil_class = st.selectbox("Class *", manager.classes, key="enroll_class")
            pupil_type = st.selectbox("Pupil Type *", manager.pupil_types, key="enroll_type")
        with col2:
            term_fees = st.number_input("Fees Per Term (UGX)", min_value=0, value=500000, key="enroll_fees", disabled=(pupil_type == "Shepherd Child"))
            if pupil_type == "Shepherd Child":
                st.info("🙏 Shepherd Child - No fees required")
        if st.button("Enroll Pupil", use_container_width=True):
            if pupil_name:
                actual_fees = 0 if pupil_type == "Shepherd Child" else term_fees
                pupil_id = manager.enroll_pupil(pupil_name, pupil_class, actual_fees, pupil_type, current_term, current_year)
                if pupil_id:
                    st.success(f"✅ {pupil_name} enrolled for {current_term} {current_year}!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Please enter pupil name")

    # ========== PUPILS & LEDGERS ==========
    elif menu == "Pupils & Ledgers":
        st.markdown("<h1 style='color: #1E3A5F;'>Pupils & Ledgers</h1>", unsafe_allow_html=True)
        if st.session_state.show_archived:
            st.info(f"Showing **{current_term}, {current_year}** (INCLUDING ARCHIVED)")
        else:
            st.info(f"Showing **{current_term}, {current_year}**")
        col_class, col_search = st.columns([1, 2])
        with col_class:
            selected_class = st.selectbox("Select Class", manager.classes, key="ledger_class")
        with col_search:
            search_term = st.text_input("Search Pupil", placeholder="Type name to search...")
        pupils = manager.get_pupils_for_term(selected_class, current_term, current_year, include_archived=st.session_state.show_archived)
        if search_term:
            pupils = [p for p in pupils if search_term.lower() in p.get("name", "").lower()]
        if not pupils:
            st.info(f"No pupils found in {selected_class} for {current_term} {current_year}")
        else:
            st.markdown(f"### {len(pupils)} pupil(s) in {selected_class}")
            for pupil in pupils:
                pupil_id = pupil.get('id')
                term_fees = safe_value(pupil.get("term_fees"), 0)
                pupil_type = pupil.get("pupil_type", "Community Child")
                is_sponsored = pupil.get("is_sponsored", False)
                sponsor_reason = pupil.get("sponsor_reason", "")
                previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                ledger_entries = manager.get_ledger(pupil_id, current_term, current_year)
                total_paid = sum([safe_value(p.get("amount"), 0) for p in ledger_entries if safe_value(p.get("amount"), 0) > 0])
                credit_amount = abs(previous_balance) if previous_balance < 0 else 0
                debt_amount = previous_balance if previous_balance > 0 else 0
                total_due = debt_amount + term_fees
                current_balance = max(0, total_due - total_paid - credit_amount)
                # Build expander title
                if pupil.get("archived", False):
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — [ARCHIVED]"
                elif is_sponsored:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — 🎓 SPONSORED"
                elif previous_balance > 0:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — ⚠️ Debt: UGX {previous_balance:,.0f} | Fees: UGX {term_fees:,.0f} | Balance: UGX {current_balance:,.0f}"
                elif previous_balance < 0:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — 💳 Credit: UGX {abs(previous_balance):,.0f} | Balance: UGX {current_balance:,.0f}"
                else:
                    expander_title = f"📌 {pupil['name']} — {pupil_type} — Fees: UGX {term_fees:,.0f} | Paid: UGX {total_paid:,.0f} | Balance: UGX {current_balance:,.0f}"
                with st.expander(expander_title):
                    if previous_balance > 0:
                        st.warning(f"💰 **Previous Term Debt:** UGX {previous_balance:,.0f}")
                    elif previous_balance < 0:
                        st.success(f"💳 **Previous Term Credit:** UGX {abs(previous_balance):,.0f}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.caption(f"📅 Enrolled: {pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', current_year)}")
                    with col2:
                        st.caption(f"🏷️ Type: {pupil_type}")
                    with col3:
                        if is_sponsored:
                            st.caption(f"🙏 Reason: {sponsor_reason}")
                    if ledger_entries:
                        # Build transactions table
                        transactions = []
                        for idx, entry in enumerate(ledger_entries, 1):
                            amt = safe_value(entry.get('amount'), 0)
                            bal = safe_value(entry.get('balance'), 0)
                            date_str = entry.get("payment_date", "")[:10] if entry.get("payment_date") else ""
                            desc = entry.get("description", "Payment") or "Payment"
                            receipt = entry.get("receipt_no", "") or ""
                            transactions.append({
                                "No.": idx, "Date": date_str, "Amount": f"UGX {amt:,.0f}",
                                "Description": desc, "Balance": f"UGX {bal:,.0f}", "Receipt": receipt[-12:] if receipt else "N/A"
                            })
                        df = pd.DataFrame(transactions)
                        st.dataframe(df, use_container_width=True)
                        # Receipt buttons
                        payment_entries = [e for e in ledger_entries if safe_value(e.get("amount"), 0) > 0]
                        if payment_entries:
                            st.markdown("---")
                            st.markdown("### 📄 Receipts")
                            for entry in payment_entries:
                                receipt_no = entry.get("receipt_no", "") or ""
                                if st.button(f"🖨️ Receipt {receipt_no[-12:]}", key=f"print_{entry.get('id', uuid.uuid4())}"):
                                    pdf_buffer = generate_pdf_receipt(
                                        school_name="Shepherd Academy Busiu", logo_path="images.jfif" if os.path.exists("images.jfif") else "",
                                        receipt_num=receipt_no, date_str=entry.get("payment_date", "") or "",
                                        child_name=pupil['name'], amount=safe_value(entry.get("amount"), 0),
                                        description=entry.get("description", "") or "", balance=safe_value(entry.get("balance"), 0),
                                        previous_balance=safe_value(entry.get("previous_balance"), 0), term_fees=term_fees,
                                        signature_text="Bursar's Signature", excess_amount=safe_value(entry.get("excess_amount"), 0)
                                    )
                                    st.download_button("📥 PDF", pdf_buffer, f"Receipt_{receipt_no}.pdf", "application/pdf")
                    else:
                        st.info(f"No payments recorded for {current_term} {current_year}")
                    if role == "bursar" and not is_sponsored and not pupil.get("archived", False):
                        if st.button(f"💰 Record Payment", key=f"pay_{pupil_id}"):
                            st.session_state.navigation_menu = "Record Payment"
                            st.session_state.quick_pay_pupil = pupil_id
                            st.session_state.quick_pay_name = pupil['name']
                            st.rerun()

    # ========== RECORD PAYMENT ==========
    elif menu == "Record Payment" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Record Payment</h1>", unsafe_allow_html=True)
        st.caption(f"Recording for: **{current_term} {current_year}**")
        all_enrolled = manager.get_pupils_for_term("All Classes", current_term, current_year, include_archived=False)
        if not all_enrolled:
            st.warning(f"No pupils enrolled for {current_term} {current_year}. Use Term Enrollment section.")
        else:
            col_filter1, col_filter2 = st.columns([1, 2])
            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes, key="filter_payment_class")
            with col_filter2:
                search_term = st.text_input("Search by Name", placeholder="Type name...", key="search_payment_pupil")
            pupil_list = [p for p in all_enrolled if not p.get("archived", False)]
            if filter_class != "All Classes":
                pupil_list = [p for p in pupil_list if p.get("class") == filter_class]
            if search_term:
                pupil_list = [p for p in pupil_list if search_term.lower() in p.get("name", "").lower()]
            if not pupil_list:
                st.warning("No pupils found")
            else:
                pupil_options = {f"{p['name']} ({p['class']})": p['id'] for p in pupil_list}
                if "quick_pay_pupil" in st.session_state:
                    pupil_id = st.session_state.quick_pay_pupil
                    pupil_name = st.session_state.quick_pay_name
                    selected_pupil = next((p for p in pupil_list if p['id'] == pupil_id), None)
                    if not selected_pupil:
                        del st.session_state.quick_pay_pupil
                        del st.session_state.quick_pay_name
                        st.rerun()
                else:
                    selected = st.selectbox("Select Pupil", list(pupil_options.keys()), key="payment_pupil")
                    pupil_id = pupil_options[selected]
                    pupil_name = selected.split(" (")[0]
                    selected_pupil = next((p for p in pupil_list if p['id'] == pupil_id), None)
                if selected_pupil:
                    term_fees = safe_value(selected_pupil.get("term_fees"), 0)
                    is_sponsored = selected_pupil.get("is_sponsored", False)
                    if is_sponsored:
                        st.warning("This is a sponsored child. No payment required.")
                    else:
                        previous_balance = manager.get_previous_term_balance(pupil_id, current_term, current_year)
                        existing_payments = manager.get_ledger(pupil_id, current_term, current_year)
                        total_paid = sum([safe_value(p.get("amount"), 0) for p in existing_payments if safe_value(p.get("amount"), 0) > 0])
                        credit_amount = abs(previous_balance) if previous_balance < 0 else 0
                        debt_amount = previous_balance if previous_balance > 0 else 0
                        total_due = debt_amount + term_fees
                        current_balance = max(0, total_due - total_paid - credit_amount)
                        # Display info cards
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.info(f"**Name**\n{pupil_name[:20]}")
                        with col2:
                            st.info(f"**Class**\n{selected_pupil['class']}")
                        with col3:
                            st.info(f"**Type**\n{selected_pupil.get('pupil_type', 'Community Child')}")
                        with col4:
                            st.info(f"**Term Fees**\nUGX {term_fees:,.0f}")
                        with col5:
                            st.info(f"**Due**\nUGX {current_balance:,.0f}")
                        if previous_balance > 0:
                            st.warning(f"⚠️ **Previous Term Debt: UGX {previous_balance:,.0f}**")
                        elif previous_balance < 0:
                            st.success(f"✅ **Previous Term Credit: UGX {abs(previous_balance):,.0f}**")
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
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded! Excess UGX {excess_amount:,.0f} carried forward.")
                                    else:
                                        st.success(f"✅ Payment of UGX {amount_paid:,.0f} recorded!")
                                    pdf_buffer = generate_pdf_receipt(
                                        school_name="Shepherd Academy Busiu", logo_path="images.jfif" if os.path.exists("images.jfif") else "",
                                        receipt_num=receipt_no, date_str=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        child_name=pupil_name, amount=amount_paid, description=f"{description} - {current_term} {current_year}",
                                        balance=new_balance, previous_balance=prev_bal, term_fees=term_fees,
                                        signature_text="Bursar's Signature", excess_amount=excess_amount
                                    )
                                    st.download_button("📥 Download Receipt", pdf_buffer, f"Receipt_{receipt_no}.pdf", "application/pdf")
                                    st.balloons()
                                    time.sleep(1)
                                    st.rerun()

    # ========== CLASS REPORTS ==========
    elif menu == "Class Reports":
        st.markdown("<h1 style='color: #1E3A5F;'>Class Fee Reports</h1>", unsafe_allow_html=True)
        if st.session_state.show_archived:
            st.info(f"Showing **{current_term}, {current_year}** (INCLUDING ARCHIVED)")
        else:
            st.info(f"Showing **{current_term}, {current_year}**")
        col1, col2 = st.columns(2)
        with col1:
            selected_class = st.selectbox("Select Class", manager.classes, key="summary_class")
        with col2:
            report_type = st.radio("View", ["All Pupils", "Cleared Only", "With Balance", "Archived Only"], horizontal=True)
        if st.button("Generate Report", use_container_width=True):
            df_full, df_cleared, df_not_cleared, df_archived = manager.get_class_summary(selected_class, current_term, current_year, include_archived=st.session_state.show_archived)
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
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_to_show.to_csv(index=False).encode()
                    st.download_button("📊 CSV", csv, f"{selected_class}_{current_term}_{current_year}_report.csv", "text/csv")
                with col2:
                    st.download_button("📘 Excel", export_to_excel({"Summary": df_full, "Cleared": df_cleared, "With Balance": df_not_cleared, "Archived": df_archived}, "report.xlsx"), f"{selected_class}_{current_term}_{current_year}_report.xlsx")
            else:
                st.warning("No data available")

    # ========== SCHOOL REPORTS ==========
    elif menu == "School Reports":
        st.markdown("<h1 style='color: #1E3A5F;'>School-Wide Reports</h1>", unsafe_allow_html=True)
        if st.session_state.show_archived:
            st.info(f"Showing **{current_term}, {current_year}** (INCLUDING ARCHIVED)")
        else:
            st.info(f"Showing **{current_term}, {current_year}**")
        if st.button("Generate School Summary", use_container_width=True):
            df_all, df_staff, df_shepherd, df_community = manager.get_school_wide_summary(current_term, current_year, include_archived=st.session_state.show_archived)
            if not df_all.empty:
                st.dataframe(df_all, use_container_width=True)
                csv = df_all.to_csv(index=False).encode()
                st.download_button("📊 Download CSV", csv, f"school_wide_{current_term}_{current_year}.csv", "text/csv")
            else:
                st.warning("No data available")

    # ========== MANAGE PUPILS ==========
    elif menu == "Manage Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Manage Pupils</h1>", unsafe_allow_html=True)
        all_pupils = manager.get_all_pupils(include_archived=False)
        if not all_pupils:
            st.info("No active pupils found")
        else:
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            with col_filter1:
                filter_class = st.selectbox("Filter by Class", ["All Classes"] + manager.classes, key="filter_manage_class")
            with col_filter2:
                filter_type = st.selectbox("Filter by Type", ["All", "Staff Child", "Shepherd Child", "Community Child"], key="filter_manage_type")
            with col_filter3:
                search_term = st.text_input("Search", placeholder="Type name...", key="search_pupil")
            pupil_list = [p for p in all_pupils]
            if filter_class != "All Classes":
                pupil_list = [p for p in pupil_list if p.get("class") == filter_class]
            if filter_type != "All":
                pupil_list = [p for p in pupil_list if p.get("pupil_type", "Community Child") == filter_type]
            if search_term:
                pupil_list = [p for p in pupil_list if search_term.lower() in p.get("name", "").lower()]
            if not pupil_list:
                st.warning("No pupils found")
            else:
                st.markdown(f"### {len(pupil_list)} pupil(s)")
                for pupil in pupil_list:
                    with st.expander(f"📌 {pupil['name']} - {pupil['class']} (Fees: UGX {safe_value(pupil.get('term_fees'), 0):,.0f})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Info:**\n- Name: {pupil['name']}\n- Class: {pupil['class']}\n- Type: {pupil.get('pupil_type', 'Community Child')}")
                        with col2:
                            st.markdown(f"**Enrolled:** {pupil.get('enrollment_term', 'Term 1')} {pupil.get('enrollment_year', '2024')}")
                        st.markdown("---")
                        with st.form(key=f"edit_form_{pupil['id']}"):
                            new_name = st.text_input("Name", pupil['name'], key=f"name_{pupil['id']}")
                            new_class = st.selectbox("Class", manager.classes, index=manager.classes.index(pupil['class']) if pupil['class'] in manager.classes else 0, key=f"class_{pupil['id']}")
                            new_type = st.selectbox("Type", manager.pupil_types, index=manager.pupil_types.index(pupil.get('pupil_type', 'Community Child')) if pupil.get('pupil_type', 'Community Child') in manager.pupil_types else 0, key=f"type_{pupil['id']}")
                            default_fees = 0 if new_type == "Shepherd Child" else safe_value(pupil.get('term_fees'), 0)
                            new_fees = st.number_input("Term Fees", value=int(default_fees), step=50000, key=f"fees_{pupil['id']}", disabled=(new_type == "Shepherd Child"))
                            col_edit, col_archive = st.columns(2)
                            with col_edit:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    manager.update_pupil(pupil['id'], new_name, new_class, new_fees, new_type)
                                    st.success("Updated!")
                                    st.rerun()
                            with col_archive:
                                leaving_reason = st.text_area("Archive Reason", placeholder="Reason for leaving", key=f"leaving_{pupil['id']}")
                                if st.form_submit_button("📦 Archive Pupil", use_container_width=True):
                                    if leaving_reason:
                                        manager.archive_pupil(pupil['id'], leaving_reason)
                                        st.warning(f"✅ {pupil['name']} archived")
                                        st.rerun()
                                    else:
                                        st.error("Please provide a reason")

    # ========== ARCHIVED PUPILS ==========
    elif menu == "Archived Pupils" and role == "bursar":
        st.markdown("<h1 style='color: #1E3A5F;'>Archived Pupils</h1>", unsafe_allow_html=True)
        archived_pupils = manager.get_archived_pupils()
        if not archived_pupils:
            st.info("No archived pupils found")
        else:
            for pupil in archived_pupils:
                with st.expander(f"📌 {pupil['name']} - {pupil['class']} (Left: {pupil.get('leaving_date', 'Unknown')[:10]})"):
                    st.markdown(f"**Reason:** {pupil.get('leaving_reason', 'Not specified')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        return_term = st.selectbox("Return Term", ["Term 1", "Term 2", "Term 3"], key=f"return_term_{pupil['id']}")
                    with col2:
                        return_year = st.number_input("Return Year", value=current_year, key=f"return_year_{pupil['id']}")
                    if st.button(f"🔄 Restore Pupil", key=f"restore_{pupil['id']}"):
                        if manager.restore_pupil(pupil['id'], return_term, return_year):
                            st.success(f"✅ {pupil['name']} restored!")
                            st.rerun()

def main():
    if not st.session_state.get("logged_in", False):
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()