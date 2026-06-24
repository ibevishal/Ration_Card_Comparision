import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import io
import csv
import re
from datetime import datetime
import streamlit.web as st_web

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except Exception:
    sync_playwright = None
    PLAYWRIGHT_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except Exception:
    BeautifulSoup = None
    BS4_AVAILABLE = False


BANNER_FILE = "banner.txt"

try:
    with open(BANNER_FILE, "r", encoding="utf-8") as f:
        BANNER_MESSAGE = f.read().strip()
except FileNotFoundError:
    BANNER_MESSAGE = ""


st.set_page_config(page_title="Ration Card Comparison App", layout="wide")


import shutil
from datetime import datetime
import os

def backup_file(file_path, backup_dir="backups"):
    os.makedirs(backup_dir, exist_ok=True)  # create backups folder if needed
    today = datetime.now().strftime("%Y-%m-%d")
    base_name = os.path.basename(file_path)
    backup_name = f"{os.path.splitext(base_name)[0]}_{today}.txt"
    backup_path = os.path.join(backup_dir, backup_name)

    if not os.path.exists(backup_path):
        shutil.copy(file_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    else:
        print(f"✅ Backup already exists: {backup_path}")


# very simple user identification
def load_users(path="users.txt"):
    users = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            users = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass
    return users

def save_user(username, path="users.txt"):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{username}\n")

users = load_users()

backup_file("users.txt")
backup_file("card_owners.txt")






# prompt the user for name
# Login screen disabled: load home page directly
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True
    st.session_state["username"] = st.session_state.get("username", "Guest")

theme = st.sidebar.selectbox("🎨 Choose Theme", ["Gray", "Dark"], index=0)
if theme == "Gray":
    st.markdown(
        """
        <style>
        body {
            background-color: #121212;
            color: #ffffff;
        }
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .st-emotion-cache {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def style_dataframe(df):
    return df.style.set_properties(**{
        'background-color': "#89A8B7",
        'color': "#000000",
        'border-color': "#8B4E92"
    }).set_table_styles([
        {'selector': 'thead', 'props': [('background-color', '#4CAF50'), ('color', 'white')]}
    ])

if "trigger_analysis" not in st.session_state:
    st.session_state.trigger_analysis = False

if "recent_files" not in st.session_state:
    st.session_state.recent_files = []

languages = {
    "English": {
        "title": "Ration Card 😶‍🌫️ Comparison Tool",
        "created_by": "Created with ❤️ by @ibe.vishal",
        "upload_prev": "📤 Upload Previous Month File",
        "upload_curr": "📤 Upload Current Month File",
        "search_placeholder": "Search by Card Number or Name (partial)",
        "summary": "📊 Summary",
        "missing": "❌ Missing Ration Cards",
        "new": "🆕 New Ration Cards",
        "changed": "🔄 Changed Ration Allotments",
        "print": "🖨️ Print this page"
    },
    "Hindi": {
        "title": "राशन कार्ड तुलना उपकरण",
        "created_by": "❤️ द्वारा निर्मित @ibe.vishal",
        "upload_prev": "📤 पिछला माह फ़ाइल अपलोड करें",
        "upload_curr": "📤 वर्तमान माह फ़ाइल अपलोड करें",
        "search_placeholder": "कार्ड संख्या या नाम से खोजें (आंशिक)",
        "summary": "📊 सारांश",
        "missing": "❌ गायब राशन कार्ड",
        "new": "🆕 नए राशन कार्ड",
        "changed": "🔄 राशन आवंटन परिवर्तन",
        "print": "🖨️ प्रिंट करें"
    }
}

selected_lang = st.sidebar.selectbox("🌐 Select Language", list(languages.keys()), index=0)
T = languages[selected_lang]
font_size = st.sidebar.slider("🔠 Font Size", min_value=0, max_value=50, value=17)
st.markdown(
    f"""
    <style>
    /* Apply chosen font size broadly so slider affects UI elements */
    html, body, .stApp, .block-container, .main, .stMarkdown, .streamlit-expanderHeader, .stText, .stButton>button, .stSelectbox, .stMultiSelect, .stTextInput, .stTextArea, .stNumberInput, .stFileUploader {{
        font-size: {font_size}px !important;
        line-height: 1.2 !important;
    }}
    /* Increase heading sizes relative to base font */
    h1 {{ font-size: calc({font_size}px * 1.6) !important; }}
    h2 {{ font-size: calc({font_size}px * 1.4) !important; }}
    h3 {{ font-size: calc({font_size}px * 1.2) !important; }}
    /* Make inputs and selects match the base font size */
    input, textarea, select, option, button {{ font-size: {font_size}px !important; }}
    /* Ensure table text scales */
    table, th, td {{ font-size: {font_size}px !important; }}
    /* Hide file uploaders without removing code */
    .stFileUploader {{ display: none !important; }}
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        background-color: #6b5b6a;
        border-right: 2px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown(
    """
    <a href="https://instagram.com/ibe.vishal" target="_blank"
    style="display: block; padding: 10px 20px; background-color: #E1306C; color: white;
           text-align: center; border-radius: 5px; text-decoration: none; margin-top: 10px;">
    💬 Contact Support on Instagram
    </a>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
button[kind="primary"] {
    background-color: #4CAF50 !important;
    color: white !important;
    font-weight: bold;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)
st.markdown(
    """
    <h1 style="
        text-align:center;
        font-family:sans-serif;
        animation: bounce 2s infinite;
    ">✨ Ration Card Comparison ✨</h1>
    <style>
    @keyframes bounce {
      0%, 100% {transform: translateY(0);}
      50% {transform: translateY(-5px);}
    }
    </style>
    """,
    unsafe_allow_html=True
)


if st.session_state.recent_files:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕘 Recent Comparisons")
    file_options = [
        f"{pair['prev_name']} ➡️ {pair['curr_name']}"
        for pair in st.session_state.recent_files
    ]
    chosen = st.sidebar.selectbox("📂 Previous Comparison", file_options)
    if chosen:
        idx = file_options.index(chosen)
        chosen_pair = st.session_state.recent_files[idx]
        st.session_state.prev_content = chosen_pair["prev_content"]
        st.session_state.curr_content = chosen_pair["curr_content"]
        # restore content source if saved with the recent pair
        st.session_state.prev_content_source = chosen_pair.get("prev_source", "txt")
        st.session_state.curr_content_source = chosen_pair.get("curr_source", "txt")
        st.session_state.trigger_analysis = True

 # === show the banner to everyone ===
if "BANNER_MESSAGE" not in st.session_state:
    st.session_state["BANNER_MESSAGE"] = BANNER_MESSAGE

if st.session_state["BANNER_MESSAGE"]:
    st.info(f"📢 **Admin Message:** {st.session_state['BANNER_MESSAGE']}")

    
st.caption(T["created_by"])



def safe_float(val):
    try:
        if pd.isna(val):
            return 0.0
        return float(str(val).replace(",", "").strip())
    except Exception:
        return 0.0


def find_html_column(df, names):
    lower_map = {str(col).strip().lower(): col for col in df.columns}
    for name in names:
        key = str(name).strip().lower()
        if key in lower_map:
            return lower_map[key]
    # Fallback substring match for header variants
    for name in names:
        key = str(name).strip().lower()
        for candidate, original in lower_map.items():
            if key in candidate:
                return original
    return None


def parse_html_table(html):
    if not BS4_AVAILABLE:
        raise RuntimeError("BeautifulSoup is required to parse HTML tables.")

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"id": "Report"}) or soup.find("table")
    if table is None:
        return pd.DataFrame()

    table_html = str(table)
    try:
        dfs = pd.read_html(table_html)
        if dfs:
            return dfs[0]
    except Exception:
        pass

    rows = []
    for tr in table.find_all("tr"):
        cols = [cell.get_text(strip=True) for cell in tr.find_all(["th", "td"])]
        if not cols or all(not cell for cell in cols):
            continue
        rows.append(cols)

    if not rows:
        return pd.DataFrame()

    # Identify first data row by numeric first column and length > 1
    data_start = None
    for idx, row in enumerate(rows):
        first = row[0].strip()
        if len(row) > 1 and first.isdigit():
            data_start = idx
            break

    if data_start is None:
        # fallback: use first row as header if row lengths are equal
        if len(rows) > 1 and all(len(r) == len(rows[0]) for r in rows[1:]):
            return pd.DataFrame(rows[1:], columns=rows[0])
        return pd.DataFrame(rows)

    header_rows = rows[:data_start]
    data_rows = rows[data_start:]
    
    if not data_rows:
        return pd.DataFrame()
    
    data_len = len(data_rows[0])

    if not header_rows:
        # No headers found; return dataframe with col_X names
        normalized = []
        for row in data_rows:
            if len(row) < data_len:
                row = row + [""] * (data_len - len(row))
            elif len(row) > data_len:
                row = row[:data_len]
            normalized.append(row)
        headers = [f"col_{i}" for i in range(data_len)]
        return pd.DataFrame(normalized, columns=headers)

    # Try single header row first
    if len(header_rows) == 1:
        headers = header_rows[0]
        if len(headers) == data_len:
            # Good match
            pass
        else:
            # Mismatch: use first data row as headers and skip it
            headers = data_rows[0]
            data_rows = data_rows[1:]
    else:
        # Multi-row headers: try to combine smartly
        # If sum of all header row lengths == data_len, concatenate all
        header_lengths = [len(hr) for hr in header_rows]
        if sum(header_lengths) == data_len:
            headers = []
            for hr in header_rows:
                headers.extend(hr)
        # If last two rows combined == data_len, use those
        elif len(header_rows) >= 2 and len(header_rows[-1]) + len(header_rows[-2]) == data_len:
            headers = header_rows[-2] + header_rows[-1]
        # Otherwise use last header row
        else:
            headers = header_rows[-1]
            # If combined with previous row matches, use that
            if len(headers) != data_len and len(header_rows) >= 2:
                prev_combined = header_rows[-2] + headers
                if len(prev_combined) == data_len:
                    headers = prev_combined

    # Final fallback: use col_X if still no match
    if len(headers) != data_len:
        headers = [f"col_{i}" for i in range(data_len)]

    normalized = []
    for row in data_rows:
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))
        elif len(row) > len(headers):
            row = row[:len(headers)]
        normalized.append(row)

    return pd.DataFrame(normalized, columns=headers)


def extract_ration_data_from_html(html):
    df = parse_html_table(html)
    if df.empty:
        return {}

    card_col = find_html_column(df, ["RC No", "RC No.", "RC Number", "Ration Card", "RC No"])
    wheat_col = find_html_column(df, ["Wheat (Kg)", "Wheat Kg", "Wheat"])
    rice_col = find_html_column(df, ["Rice (Kg)", "Rice Kg", "Rice"])
    card_type_col = find_html_column(df, ["Scheme", "Avail Type", "Availability Type", "Scheme Name"])

    # Fallback: if named columns not found, try position-based detection for col_X naming
    # Typical Bihar ePOS table: col_0=index, col_1=RC No, col_2=Scheme, col_6=Wheat, col_7/col_8=Rice
    if not card_col:
        if "col_1" in df.columns:
            card_col = "col_1"
    if not card_type_col:
        if "col_2" in df.columns:
            card_type_col = "col_2"
    if not wheat_col:
        if "col_6" in df.columns:
            wheat_col = "col_6"
    if not rice_col:
        if "col_10" in df.columns:
            rice_col = "col_10"


    # If still no card column found, return empty
    if not card_col:
        return {}

    data = {}
    for idx, row in df.iterrows():
        try:
            card = str(row[card_col]).strip()
            # normalize card: remove whitespace and control characters
            card = re.sub(r"\\s+", "", card)
            card = card.replace("\r", "").replace("\n", "")
            if not card or card.lower() in ("nan", "none"):
                continue

            card_type = (
                str(row[card_type_col]).strip()
                if card_type_col and not pd.isna(row[card_type_col])
                else "Unknown"
            )
            wheat = safe_float(row[wheat_col]) if wheat_col else 0.0
            rice = safe_float(row[rice_col]) if rice_col else 0.0
            data[card] = (card_type, wheat, rice)
        except Exception:
            # skip rows that cannot be parsed into expected columns
            continue

    return data


def extract_ration_numbers_from_html(html):
    return list(extract_ration_data_from_html(html).keys())


@st.cache_data(ttl=300)
def get_fps_list(dist_code):
    if not PLAYWRIGHT_AVAILABLE or not BS4_AVAILABLE:
        raise RuntimeError("playwright and/or bs4 not available in this environment")
    with sync_playwright() as p:
        browser = p.chromium.launch(
    executable_path="/usr/bin/chromium",
    headless=True,
    args=["--no-sandbox"]
)
        page = browser.new_page()
        page.goto(
            "https://epos.bihar.gov.in/FPS_Trans_Abstract.jsp",
            wait_until="networkidle",
        )

        response = page.request.post(
            "https://epos.bihar.gov.in/AjaxExecution.jsp",
            form={
                "select": "true",
                "type": "fps",
                "param": str(dist_code),
            },
        )

        html = response.text()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    fps_data = {}
    for option in soup.find_all("option"):
        value = option.get("value")
        text = option.text.strip()
        if value and value != "0":
            fps_data[text] = value
    return fps_data


@st.cache_data(ttl=300)
def fetch_epos_html(dist_code, fps_id, month, year):
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("playwright not available in this environment")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(
            "https://epos.bihar.gov.in/FPS_Trans_Abstract.jsp",
            wait_until="networkidle",
        )

        response = page.request.post(
            "https://epos.bihar.gov.in/FPS_Trans_Details.jsp",
            form={
                "dist_code": str(dist_code),
                "fps_id": str(fps_id),
                "month": str(month),
                "year": str(year),
            },
        )

        html = response.text()
        browser.close()

    return html


# Choose data source
data_mode = st.radio(
    "Data Source",
    [
        #"Upload TXT Files (Outdated, use ePOS fetch if possible)",
        "Fetch from Bihar ePOS (Beta)"
    ],
    index=0,
)

# Bihar ePOS fetch UI (before upload)
# get_fps_list / fetch_epos_html are defined later in the file in this version.
# To prevent NameError, we guard the button action and FPS listing.
if data_mode == "Fetch from Bihar ePOS (Beta)":
    # Prevent NameError if function definitions are reordered.
    # (The functions exist later, but in case of execution issues we guard the call.)

    dist_code = st.text_input("District Code", value="216")


    month1 = st.selectbox("Previous Month", range(1, 13), index=4)
    month2 = st.selectbox("Current Month", range(1, 13), index=5)

    year = st.number_input("Year", value=2026)



    if dist_code.strip():
        # Ensure Playwright and BeautifulSoup are available before attempting fetch
        if not PLAYWRIGHT_AVAILABLE or not BS4_AVAILABLE:
            st.error("Bihar ePOS fetch disabled: missing dependencies (playwright or bs4).")
            fps_list = {}
        else:
            try:
                fps_list = get_fps_list(dist_code)
            except Exception as e:
                st.error(f"Error retrieving FPS list: {e}")
                fps_list = {}

        # Prepare FPS list and set default selection
        fps_keys = list(fps_list.keys()) if fps_list else ["No FPS Found"]
        default_index = 1096
        selected_fps = st.selectbox("Select FPS", fps_keys, index=default_index)

        if st.button("Fetch Data"):
            if not fps_list:
                st.error("No FPS options found for this District Code.")
            else:
                fps_id = fps_list[selected_fps]
                try:
                    prev_html = fetch_epos_html(dist_code, fps_id, month1, year)
                    curr_html = fetch_epos_html(dist_code, fps_id, month2, year)
                except Exception as e:
                    st.error(f"Error fetching data: {e}")
                    prev_html = ""
                    curr_html = ""

                st.session_state.prev_content = prev_html
                st.session_state.curr_content = curr_html
                st.session_state.prev_content_source = "html"
                st.session_state.curr_content_source = "html"
                # parse immediately and persist parsed dicts for reliable comparison
                try:
                    parsed_prev = extract_ration_data_from_html(prev_html)
                    parsed_curr = extract_ration_data_from_html(curr_html)
                except Exception:
                    parsed_prev = {}
                    parsed_curr = {}
                st.session_state["prev_data"] = parsed_prev
                st.session_state["curr_data"] = parsed_curr
                st.session_state["prev_cards"] = set(parsed_prev.keys())
                st.session_state["curr_cards"] = set(parsed_curr.keys())
                # save recent entry now
                uploaded_pair = {
                    "prev_name": "previous.html",
                    "curr_name": "current.html",
                    "prev_content": prev_html,
                    "curr_content": curr_html,
                    "prev_source": "html",
                    "curr_source": "html",
                }
                st.session_state.recent_files.insert(0, uploaded_pair)
                st.session_state.recent_files = st.session_state.recent_files[:3]
                st.session_state.trigger_analysis = True

                st.success("Data downloaded successfully")
                # Temporary preview for quick verification - COMMENTED OUT
                # try:
                #     if prev_html:
                #         with st.expander("🔍 Preview Previous Month (raw HTML)", expanded=False):
                #             st.code(prev_html[:2000], language="html")
                #         if BS4_AVAILABLE:
                #             df_prev = parse_html_table(prev_html)
                #             if not df_prev.empty:
                #                 st.subheader("Parsed Table — Previous Month (first 5 rows)")
                #                 st.dataframe(df_prev.head(5), use_container_width=True)
                #     if curr_html:
                #         with st.expander("🔍 Preview Current Month (raw HTML)", expanded=False):
                #             st.code(curr_html[:2000], language="html")
                #         if BS4_AVAILABLE:
                #             df_curr = parse_html_table(curr_html)
                #             if not df_curr.empty:
                #                 st.subheader("Parsed Table — Current Month (first 5 rows)")
                #                 st.dataframe(df_curr.head(5), use_container_width=True)
                # except Exception as e:
                #     st.warning(f"Preview generation error: {e}")

# TXT upload UI - COMMENTED OUT
uploaded_file1 = st.file_uploader(
     T["upload_prev"],
     type=["txt"],
     disabled=(data_mode != "Upload TXT Files"),
 )
uploaded_file2 = st.file_uploader(
     T["upload_curr"],
     type=["txt"],
     disabled=(data_mode != "Upload TXT Files"),
 )


if uploaded_file1:
     st.session_state.prev_content = uploaded_file1.getvalue().decode("utf-8")
     st.session_state.prev_content_source = "txt"
if uploaded_file2:
    st.session_state.curr_content = uploaded_file2.getvalue().decode("utf-8")
    st.session_state.curr_content_source = "txt"

if data_mode == "Upload TXT Files":
    # Only treat session content as uploaded TXT if it was actually uploaded as TXT
    file1 = (
        io.BytesIO(st.session_state["prev_content"].encode("utf-8"))
        if st.session_state.get("prev_content") and st.session_state.get("prev_content_source") == "txt"
        else None
    )
    file2 = (
        io.BytesIO(st.session_state["curr_content"].encode("utf-8"))
        if st.session_state.get("curr_content") and st.session_state.get("curr_content_source") == "txt"
        else None
    )
    html_mode = False
else:
    file1 = None
    file2 = None
    html_mode = True

if data_mode == "Upload TXT Files":
    if file1:
        file1.name = "previous.txt"
        # with st.expander("📄 Preview Previous Month File"):
        #     st.text(file1.getvalue().decode("utf-8")[:1000])

    if file2:
        file2.name = "current.txt"
        # with st.expander("📄 Preview Current Month File"):
        #     st.text(file2.getvalue().decode("utf-8")[:1000])

    if not (file1 and file2):
        st.warning("⚠️ Please upload both files to proceed.")
else:
    # if st.session_state.get("prev_content"):
    #     with st.expander("📄 Preview Previous Month HTML"):
    #         st.code(st.session_state["prev_content"][:1000], language="html")
    # if st.session_state.get("curr_content"):
    #     with st.expander("📄 Preview Current Month HTML"):
    #         st.code(st.session_state["curr_content"][:1000], language="html")
    if not (st.session_state.get("prev_content") and st.session_state.get("curr_content")):
        st.warning("⚠️ Please click fetch to proceed.")


#admin part start


import os



# check if .env exists
if os.path.exists(".env"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
        ADMIN_USER = os.getenv("ADMIN_USER", "admin")
        ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")
    except Exception:
        ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
        ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")
else:
    # Use safe defaults if secrets are not configured
    ADMIN_USER = st.secrets.get("ADMIN_USER", "admin")
    ADMIN_PASS = st.secrets.get("ADMIN_PASS", "admin")


# inside your sidebar (or wherever you want)
with st.sidebar.expander("🔒 Admin Login"):
    admin_username = st.text_input("Admin Username", key="admin_user")
    admin_password = st.text_input("Admin Password", type="password", key="admin_pass")
    if st.button("Login as Admin"):
        if admin_username == ADMIN_USER and admin_password == ADMIN_PASS:
            st.session_state["is_admin"] = True
            st.success("✅ Admin logged in successfully")
        else:
            st.error("❌ Wrong admin credentials")

if st.session_state.get("is_admin"):
    st.sidebar.success("🛠️ You are in Admin Mode")
        # === Admin Banner Hard-Coded Editor ===
    st.write("## User Notification Banner")

    # store the banner in session_state from hard-coded variable
    if "banner_message" not in st.session_state:
        st.session_state["banner_message"] = BANNER_MESSAGE

    edited_banner = st.text_area(
        "Edit Banner Message to show to users (leave blank to remove):",
        st.session_state["banner_message"],
        height=100
    )

    if st.button("💾 Update Banner"):
        st.session_state["banner_message"] = edited_banner
        with open(BANNER_FILE, "w", encoding="utf-8") as f:
            f.write(edited_banner.strip())
        st.success("✅ Banner updated and saved")


    st.subheader("🛠️ Admin Panel")

    st.write("## Edit user list (users.txt)")
    if os.path.exists("users.txt"):
        with open("users.txt", "r", encoding="utf-8") as f:
            user_data = f.read()
        edited = st.text_area("Edit users.txt", user_data, height=300)
        if st.button("Save user list"):
            with open("users.txt", "w", encoding="utf-8") as f:
                f.write(edited)
            st.success("✅ User list updated!")

    st.write("## Edit card owners (card_owners.txt)")
    
    if os.path.exists("card_owners.txt"):
        with open("card_owners.txt", "r", encoding="utf-8") as f:
            owners_data = f.read()
        edited = st.text_area("Edit card_owners.txt", owners_data, height=300)
        if st.button("Save card owners"):
            with open("card_owners.txt", "w", encoding="utf-8") as f:
                f.write(edited)
            st.success("✅ Card owners updated!")
            
    if os.path.exists("activity_log.csv"):
        st.subheader("📄 User Activity Log")
        log_df = pd.read_csv("activity_log.csv", names=["Username", "Timestamp", "UserAgent", "IP"])
        st.dataframe(log_df, use_container_width=True)
        
    st.subheader("🗂️ Backup Files")

    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        st.info("No backups yet.")
    else:
        backup_files = sorted(os.listdir(backup_dir), reverse=True)
        if backup_files:
            for backup_file in backup_files:
                backup_path = os.path.join(backup_dir, backup_file)
                with open(backup_path, "rb") as f:
                    st.download_button(
                        f"⬇️ Download {backup_file}",
                        f,
                        file_name=backup_file,
                        mime="text/plain"
                    )
        else:
            st.info("No backup files found in the backups folder.")
 
#admin part end

def extract_ration_data(file):

    data = {}
    lines = file.getvalue().decode("utf-8").splitlines()
    for idx, line in enumerate(lines, start=1):
        parts = line.strip().split()
        if len(parts) >= 8:
            try:
                card = parts[1]
                card_type = parts[2] if len(parts) > 2 else "Unknown"
                date_index = None
                for i, token in enumerate(parts):
                    if re.match(r"^\d{2}-\d{2}-\d{4}$", token):
                        date_index = i
                        break
                numeric = []
                if date_index is not None:
                    for token in parts[date_index + 1 :]:
                        if re.match(r"^[0-9]+(?:\.[0-9]+)?$", token):
                            numeric.append(token)

                if len(numeric) >= 2:
                    wheat = safe_float(numeric[0])
                    rice = safe_float(numeric[1])
                else:
                    wheat = safe_float(parts[6]) if len(parts) > 6 else 0.0
                    rice = safe_float(parts[7]) if len(parts) > 7 else 0.0

                data[card] = (card_type, wheat, rice)
            except Exception:
                st.warning(f"⚠️ Error parsing line {idx}: {line}")
        else:
            st.warning(f"⚠️ Skipped malformed line {idx}: {line}")
    return data

def extract_ration_numbers(file):
    return [
        line.strip().split()[1]
        for line in file.getvalue().decode("utf-8").splitlines()
        if len(line.strip().split()) >= 2
    ]

def load_card_owner_mapping(path="card_owners.txt"):
    mapping = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(maxsplit=1)
                if len(parts) == 2:
                    mapping[parts[0]] = parts[1]
    except FileNotFoundError:
        st.warning("Card owner mapping file not found.")
    return mapping

card_owners = load_card_owner_mapping()

def get_owner(card):
    return card_owners.get(card, "👤 Unknown Owner")

if (file1 and file2) or st.session_state.trigger_analysis:
    st.session_state.trigger_analysis = False
    with st.spinner("🔄 Analyzing files, please wait..."):
        if html_mode:
            # prefer persisted parsed dicts (set at fetch time) to avoid re-parsing failures
            prev_data = st.session_state.get("prev_data") or extract_ration_data_from_html(st.session_state.get("prev_content", ""))
            curr_data = st.session_state.get("curr_data") or extract_ration_data_from_html(st.session_state.get("curr_content", ""))

            list1 = list(prev_data.keys())
            list2 = list(curr_data.keys())

            # st.subheader("📊 Data for checking / Verify from site")
            # st.info(f"✅ Total Ration Cards (Previous Month with same card included): **{len(list1)}**")
            # st.info(f"✅ Total Ration Cards (Current Month with same card included): **{len(list2)}**")

            # ensure prev_data/curr_data variables exist for downstream use
            prev_data = st.session_state.get("prev_data") or prev_data
            curr_data = st.session_state.get("curr_data") or curr_data
            # persist parsed results so they survive reruns and are available elsewhere
            st.session_state["prev_data"] = prev_data
            st.session_state["curr_data"] = curr_data
            st.session_state["prev_cards"] = set(prev_data.keys())
            st.session_state["curr_cards"] = set(curr_data.keys())
            # debug: show small sample to verify parsing didn't fall back to raw HTML
            # try:
            #     st.write("Parsed prev_data sample:", list(prev_data.items())[:5])
            #     st.write("Parsed curr_data sample:", list(curr_data.items())[:5])
            # except Exception:
            #     pass
        else:
            uploaded_pair = {
                "prev_name": file1.name,
                "curr_name": file2.name,
                "prev_content": file1.getvalue().decode("utf-8"),
                "curr_content": file2.getvalue().decode("utf-8")
            }
            st.session_state.recent_files.insert(0, uploaded_pair)
            st.session_state.recent_files = st.session_state.recent_files[:3]

            list1 = extract_ration_numbers(file1)
            list2 = extract_ration_numbers(file2)

            st.subheader("📊 Data for checking / Verify from site")
            st.info(f"✅ Total Ration Cards (Previous Month with same card included): **{len(list1)}**")
            st.info(f"✅ Total Ration Cards (Current Month with same card included): **{len(list2)}**")

            prev_data = extract_ration_data(file1)
            curr_data = extract_ration_data(file2)
            st.session_state["prev_data"] = prev_data
            st.session_state["curr_data"] = curr_data
            st.session_state["prev_cards"] = set(prev_data.keys())
            st.session_state["curr_cards"] = set(curr_data.keys())

        # prefer session_state persisted cards if present
        prev_cards = st.session_state.get("prev_cards", set(prev_data.keys()))
        curr_cards = st.session_state.get("curr_cards", set(curr_data.keys()))

    search_query = st.text_input(f"🔍 {T['search_placeholder']}")

    if search_query:
        st.subheader("🔎 Search Results")
        matching_cards = [
            card for card in (prev_cards | curr_cards)
            if search_query in card or
            (card_owners.get(card) and search_query in card_owners[card])
        ]
        if matching_cards:
            results_df = pd.DataFrame([{
                "Ration Card": card,
                "Card Type": (prev_data.get(card) or curr_data.get(card) or ("Unknown", 0, 0))[0],
                "Card Holder": get_owner(card),
                "Wheat (kg)": (prev_data.get(card) or curr_data.get(card) or ("Unknown", 0, 0))[1],
                "Rice (kg)": (prev_data.get(card) or curr_data.get(card) or ("Unknown", 0, 0))[2]
            } for card in matching_cards])
            st.dataframe(results_df, use_container_width=True)
        else:
            st.warning("No match found.")

    missing_owner_cards = [card for card in (prev_cards | curr_cards) if card_owners.get(card) is None]

    if missing_owner_cards:
        st.subheader("👤 Add Missing Card Owner Names")
        missing_df = pd.DataFrame({
            "Ration Card": missing_owner_cards,
            "Owner Name": ["" for _ in missing_owner_cards]
        })
        edited_df = st.data_editor(missing_df, num_rows="dynamic", use_container_width=True, key="owner_editor")

        if st.button("✅ Save Owner Names"):
            new_entries = 0
            for _, row in edited_df.iterrows():
                card = row["Ration Card"]
                name = row["Owner Name"].strip()
                if name:
                    with open("card_owners.txt", "a", encoding="utf-8") as f:
                        f.write(f"{card} {name}\n")
                    card_owners[card] = name
                    new_entries += 1
            if new_entries:
                st.success(f"✅ Saved {new_entries} new owner(s). Please refresh to update the tables.")
            else:
                st.warning("⚠️ No names were entered to save.")

    st.subheader(T["summary"])
    

    st.success(f"✅ Total Ration Cards (Previous Month): **{len(prev_cards) }**")
    st.success(f"✅ Total Ration Cards (Current Month): **{len(curr_cards) }**")

    left_cards = sorted(prev_cards - curr_cards)
    new_cards = sorted(curr_cards - prev_cards)

    st.subheader(T["missing"])
    st.info(f"🧮 Total Missing: **{len(left_cards)}**")
    if left_cards:
        left_df = pd.DataFrame([{
            "Ration Card": card,
            "Card Type": prev_data[card][0],
            "Card Holder": get_owner(card),
            "Wheat (kg)": prev_data[card][1],
            "Rice (kg)": prev_data[card][2]
        } for card in left_cards])
        st.dataframe(style_dataframe(left_df), use_container_width=True)


    st.subheader(T["new"])
    st.info(f"🧮 Total New: **{len(new_cards)}**")
    if new_cards:
        new_df = pd.DataFrame([{
            "Ration Card": card,
            "Card Type": curr_data[card][0],
            "Card Holder": get_owner(card),
            "Wheat (kg)": curr_data[card][1],
            "Rice (kg)": curr_data[card][2]
        } for card in new_cards])
        st.dataframe(style_dataframe(new_df), use_container_width=True)


    changed_cards = sorted([
        card for card in prev_cards & curr_cards
        if prev_data[card][1:] != curr_data[card][1:]
    ])
    if changed_cards:
        st.subheader(T["changed"])
        st.info(f"🧮 Total Changed: **{len(changed_cards)}**")
        changed_df = pd.DataFrame([{
            "Ration Card": card,
            "Card Type": curr_data[card][0],
            "Card Holder": get_owner(card),
            "Wheat (Previous)": prev_data[card][1],
            "Wheat (Current)": curr_data[card][1],
            "Rice (Previous)": prev_data[card][2],
            "Rice (Current)": curr_data[card][2]
        } for card in changed_cards])
        st.dataframe(style_dataframe(changed_df), use_container_width=True)


if (file1 and file2) or (html_mode and st.session_state.get("prev_data") and st.session_state.get("curr_data")):
    st.subheader("🖨️ Print Options")
    print_choices = st.multiselect(
        "✅ Select which sections to include in the print report",
        options=["Missing Ration Cards", "New Ration Cards", "Changed Ration Allotments"],
        default=["Missing Ration Cards", "New Ration Cards", "Changed Ration Allotments"]
    )

    printable_html = """
    <style>
        h3 { font-family: Arial; margin-top: 30px; }
        .missing { color: red; }
        .new { color: green; }
        .changed { color: orange; }
        table, th, td { border: 1px solid #aaa; border-collapse: collapse; }
        th, td { padding: 8px; font-size: 14px; }
        table { width: 100%; margin-bottom: 30px; background-color: #f9f9f9; }
        @media print {
            button { display: none; }
            body { background: white; }
        }
    </style>
    """

    if "Missing Ration Cards" in print_choices and left_cards:
        printable_html += "<h3 class='missing'>❌ Missing Ration Cards</h3>" + left_df.to_html(index=True, escape=False)

    if "New Ration Cards" in print_choices and new_cards:
        printable_html += "<h3 class='new'>🆕 New Ration Cards</h3>" + new_df.to_html(index=True, escape=False)

    if "Changed Ration Allotments" in print_choices and changed_cards:
        printable_html += "<h3 class='changed'>🔄 Changed Ration Allotments</h3>" + changed_df.to_html(index=True, escape=False)

    components.html(f"""
        <div id="print-section">{printable_html}</div>
        <button onclick="printReport()" style="margin-top: 20px; padding: 15px 30px; font-size: 16px;
                background-color: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer;">
            🖨️ Print Report
        </button>
        <script>
            function printReport() {{
                var printContents = document.getElementById('print-section').innerHTML;
                var originalContents = document.body.innerHTML;
                document.body.innerHTML = printContents;
                 window.print();
                document.body.innerHTML = originalContents;
                window.location.reload();
            }}
        </script>
    """, height=800, scrolling=True)


# Footer instructions
st.markdown("---")
st.subheader("✈️INSTRUCTION🙌")
st.caption("💡 Select the district code { check from AEPDS BIHAR}, choose the months, pick the FPS, then click Fetch.")
st.subheader("FOR DATA VERIFICATION")
st.caption("💡If total of Wheat Sold in Ration Card list :: All Good ignore that Value")
st.caption("💡If total of Wheat Sold not in Ration Card list :: Fetch Data Again something is wrong")

st.markdown(
    """
    <hr>
    <p style="text-align:center;font-size:12px;color:gray;">
    ❤️ Built by Vishal Kumar | <a href="https://instagram.com/ibe.vishal" target="_blank">Instagram</a>
    </p>
    """,
    unsafe_allow_html=True
)
