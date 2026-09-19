import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import io
import csv
import re
from datetime import datetime
import streamlit.web as st_web
import os
import ssl
import requests

# Disable SSL verification globally
ssl._create_default_https_context = ssl._create_unverified_context

# Patch for older TLS versions
import certifi
try:
    import ssl as ssl_module
    # Allow all TLS versions
    ssl_module.OPENSSL_VERSION
except:
    pass

# Disable SSL warnings
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

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
    normalized = {}
    for col in df.columns:
        text = str(col).strip().lower()
        normalized[text] = col
        compact = re.sub(r"[^a-z0-9]+", "", text)
        if compact:
            normalized[compact] = col
    for name in names:
        key = str(name).strip().lower()
        if key in normalized:
            return normalized[key]
        compact = re.sub(r"[^a-z0-9]+", "", key)
        if compact in normalized:
            return normalized[compact]
    for name in names:
        key = str(name).strip().lower()
        for candidate, original in list(normalized.items()):
            if candidate and (candidate in key or key in candidate):
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

    card_col = find_html_column(df, ["RC No", "RC No.", "RC Number", "Ration Card", "RC"])
    wheat_col = find_html_column(df, ["Wheat (Kg)", "Wheat Kg", "Wheat", "Qty in Kgs Wheat", "Wheat Qty"])
    rice_col = find_html_column(df, ["Rice (Kg)", "Rice Kg", "Rice", "F Rice", "Qty in Kgs F Rice", "F Rice Qty"])
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
        for candidate in ["col_7", "col_8", "col_10"]:
            if candidate in df.columns:
                rice_col = candidate
                break


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


def _epos_candidate_urls(base_path):
    """Support both legacy .jsp pages and the newer extensionless endpoint names."""
    return [
        f"https://epos.bihar.gov.in/{base_path}",
        f"https://epos.bihar.gov.in/{base_path}.jsp",
    ]


@st.cache_data(ttl=300)
def get_fps_list(dist_code):
    if not PLAYWRIGHT_AVAILABLE or not BS4_AVAILABLE:
        raise RuntimeError("playwright and/or bs4 not available in this environment")
    with sync_playwright() as p:
        browser = p.chromium.launch(
    headless=True,
    args=[
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
    ],
)

        page = browser.new_page(ignore_https_errors=True)

        abstract_url = None
        for candidate in _epos_candidate_urls("FPS_Trans_Abstract"):
            try:
                page.goto(candidate, wait_until="domcontentloaded", timeout=60000)
                abstract_url = candidate
                break
            except Exception:
                continue
        if abstract_url is None:
            raise RuntimeError("Could not reach the Bihar ePOS abstract page.")

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
    import requests
    from requests.adapters import HTTPAdapter
    import urllib3
    import subprocess

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    detail_urls = [
        "https://epos.bihar.gov.in/FPS_Trans_Details",
        "https://epos.bihar.gov.in/FPS_Trans_Details.jsp",
        "http://epos.bihar.gov.in/FPS_Trans_Details",
        "http://epos.bihar.gov.in/FPS_Trans_Details.jsp",
    ]

    # Try using curl first (more lenient with SSL issues)
    for url in detail_urls:
        try:
            cmd = [
                'curl',
                '-k',
                '-s',
                '-X', 'POST',
                url,
                '-d', f'dist_code={dist_code}&fps_id={fps_id}&month={month}&year={year}',
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                '--connect-timeout', '30',
                '--max-time', '60'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=70)
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except Exception:
            continue

    class UnverifiedAdapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs['ssl_context'] = None
            return super().init_poolmanager(*args, **kwargs)

    session = requests.Session()
    session.mount('https://', UnverifiedAdapter())
    session.mount('http://', UnverifiedAdapter())

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    last_error = None
    for url in detail_urls:
        try:
            response = session.post(
                url,
                data={
                    "dist_code": str(dist_code),
                    "fps_id": str(fps_id),
                    "month": str(month),
                    "year": str(year),
                },
                timeout=30,
                verify=False,
                allow_redirects=True,
            )
            if response.status_code == 200 and response.text:
                return response.text
            last_error = Exception(f"HTTP {response.status_code}")
        except Exception as exc:
            last_error = exc
    if last_error is not None:
        raise Exception(f"Failed to fetch Bihar ePOS data: {last_error}")
    raise Exception("Failed to fetch Bihar ePOS data: unknown error")


EPOS_BASE_URL = "https://epos.bihar.gov.in"
EPOS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Mobile Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://epos.bihar.gov.in/FPS_Trans_Abstract",
    "X-Requested-With": "XMLHttpRequest",
}


def parse_html_options(html: str):
    """Parse HTML option tags into a standard list of {value, label}."""
    if not html:
        return []

    def is_placeholder(value, label):
        normalized_label = re.sub(r"[^a-z0-9]+", "", label.lower())
        return value in {"", "0"} and normalized_label in {
            "select",
            "selection",
            "chooseselect",
            "pleaseselect",
            "pleasechoose",
        }

    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        options = []
        for option in soup.find_all("option"):
            value = (option.get("value") or "").strip()
            label = option.get_text(" ", strip=True)
            if (value or label) and not is_placeholder(value, label):
                options.append({"value": value, "label": label})
        if options:
            return options

    pattern = re.compile(r"<option[^>]*value=['\"]?([^'\"\s>]+)['\"]?[^>]*>(.*?)</option>", re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(html)
    items = []
    for value, label_html in matches:
        label = re.sub(r"<.*?>", " ", label_html)
        label = re.sub(r"\s+", " ", label).strip()
        if (value or label) and not is_placeholder(value.strip(), label):
            items.append({"value": value.strip(), "label": label})
    return items


def fetch_epos_select_options(endpoint: str, params: dict | None = None):
    """Fetch an ePOS dropdown list using the current backend route pattern."""
    url = f"{EPOS_BASE_URL}{endpoint}"
    response = requests.get(url, params=params or {}, timeout=30, verify=False, headers=EPOS_HEADERS)
    response.raise_for_status()
    html = response.text

    items = parse_html_options(html)
    if items:
        return items

    # If the backend responds with plain text or a payload instead of option tags, keep the raw text.
    text = html.strip()
    if text:
        return [{"value": "", "label": text[:120]}]

    raise RuntimeError(f"No option data was returned for {endpoint}")


def fetch_epos_report(payload: dict, retries: int = 3):
    """POST JSON payload to the correct Bihar ePOS report endpoint with retry logic and SSL error handling."""
    # The actual live endpoint discovered from browser network inspection
    url = f"{EPOS_BASE_URL}/Epos_Spring/fps/fpstransactionwitoutcatptcha"
    
    session = requests.Session()
    # Disable SSL verification and allow unverified HTTPS connections
    session.verify = False
    
    for attempt in range(retries):
        try:
            response = session.post(
                url,
                json=payload,
                timeout=120,
                headers={
                    **EPOS_HEADERS,
                    "Content-Type": "application/json",
                    "Accept": "application/json,text/plain,*/*",
                },
            )
            
            # Accept any 2xx or 3xx status code
            if 200 <= response.status_code < 400:
                try:
                    data = response.json()
                    # Return data as-is (could be list or dict)
                    return data
                except Exception:
                    return {"raw_text": response.text[:500]}
            else:
                raise requests.exceptions.HTTPError(f"HTTP {response.status_code}")
                
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError) as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                st.warning(f"⏱️ Connection issue (attempt {attempt + 1}/{retries}): {type(e).__name__}. Waiting {wait_time}s before retry...")
                import time
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                st.warning(f"⚠️ Error on attempt {attempt + 1}/{retries}: {str(e)[:100]}. Retrying...")
            else:
                raise
    
    raise RuntimeError("Failed after all retry attempts")


def parse_epos_report_to_cards(report_data):
    """Parse Bihar ePOS report JSON (transaction list) into card mapping: {card_id: [type, wheat, rice]}."""
    card_map = {}
    
    # The API returns a direct array at root level, not wrapped in a data key
    if isinstance(report_data, dict):
        # If dict, try to extract array from common keys
        data_array = None
        for key in ["data", "result", "records", "items"]:
            if key in report_data and isinstance(report_data[key], list):
                data_array = report_data[key]
                break
        if not data_array:
            return {}
    elif isinstance(report_data, list):
        # Already an array
        data_array = report_data
    else:
        return {}
    
    # Process each transaction record
    for transaction in data_array:
        if not isinstance(transaction, dict):
            continue
        
        # Extract ration card number
        card_id = transaction.get("existingRcNumber") or transaction.get("card_no") or transaction.get("ration_card_no")
        if not card_id:
            continue
        
        card_id = str(card_id).strip()
        
        # Extract card type from scheme
        card_type = transaction.get("schemeShortName") or transaction.get("card_type") or "APL"
        card_type = str(card_type).strip()
        
        # Extract wheat and rice quantities from commodityList
        wheat_qty = 0.0
        rice_qty = 0.0
        
        commodity_list = transaction.get("commodityList", [])
        if isinstance(commodity_list, list):
            for commodity in commodity_list:
                if not isinstance(commodity, dict):
                    continue
                
                comm_name = commodity.get("comm_name_en", "").lower()
                sale_qty = commodity.get("sale_qty") or commodity.get("saleQty") or 0.0
                
                try:
                    sale_qty = float(sale_qty) if sale_qty else 0.0
                except (ValueError, TypeError):
                    sale_qty = 0.0
                
                # Match commodity names
                if "wheat" in comm_name:
                    wheat_qty = sale_qty
                elif "rice" in comm_name:
                    rice_qty = sale_qty
        
        # Only add if we have valid data
        if card_id:
            card_map[card_id] = [card_type, wheat_qty, rice_qty]
    
    return card_map


def render_epos_automation_mode():
    """Fetch previous and current month data from Bihar ePOS and compare them."""
    st.subheader("Automation from Bihar ePOS")
    st.caption("Fetch and compare data for previous month vs current month from the live Bihar ePOS backend.")
    
    st.session_state.setdefault("epos_districts", [])
    st.session_state.setdefault("epos_afso", [])
    st.session_state.setdefault("epos_fps", [])
    st.session_state.setdefault("epos_prev_data", {})
    st.session_state.setdefault("epos_curr_data", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Step 1: Select Location")
        
        if st.button("Load district list", key="load_districts_auto"):
            try:
                st.session_state["epos_districts"] = fetch_epos_select_options("/Epos_Spring/Common/getDistricts")
                st.success("District list loaded.")
            except Exception as exc:
                st.error(f"District list could not be loaded: {exc}")
                st.session_state["epos_districts"] = []
        
        district_options = st.session_state.get("epos_districts", [])
        if district_options:
            district_labels = [item.get("label") or item.get("value") or "Select" for item in district_options]
            district_values = [item.get("value") for item in district_options]
            selected_district_label = st.selectbox("District", district_labels, index=0)
            dist_code = district_values[district_labels.index(selected_district_label)]
        else:
            dist_code = st.text_input("District Code", value="216")
        
        if st.button("Load AFSO list", key="load_afso_auto"):
            try:
                st.session_state["epos_afso"] = fetch_epos_select_options("/Epos_Spring/Common/getAfso", {"dist_code": str(dist_code)})
                st.success("AFSO list loaded.")
            except Exception as exc:
                st.error(f"AFSO list could not be loaded: {exc}")
                st.session_state["epos_afso"] = []
        
        afso_options = st.session_state.get("epos_afso", [])
        if afso_options:
            afso_labels = [item.get("label") or item.get("value") or "Select" for item in afso_options]
            afso_values = [item.get("value") for item in afso_options]
            selected_afso_label = st.selectbox("AFSO", afso_labels, index=0)
            afso_code = afso_values[afso_labels.index(selected_afso_label)]
        else:
            afso_code = st.text_input("AFSO Code", value="01205")
        
        if st.button("Load FPS list", key="load_fps_auto"):
            try:
                st.session_state["epos_fps"] = fetch_epos_select_options("/Epos_Spring/Common/getFPSs", {"dist_code": str(dist_code), "afso_code": str(afso_code)})
                st.success("FPS list loaded.")
            except Exception as exc:
                st.error(f"FPS list could not be loaded: {exc}")
                st.session_state["epos_fps"] = []
        
        fps_options = st.session_state.get("epos_fps", [])
        if fps_options:
            fps_labels = [item.get("label") or item.get("value") or "Select" for item in fps_options]
            fps_values = [item.get("value") for item in fps_options]
            selected_fps_label = st.selectbox("FPS", fps_labels, index=0)
            fps_id = fps_values[fps_labels.index(selected_fps_label)]
        else:
            fps_id = st.text_input("FPS ID", value="")
    
    with col2:
        st.markdown("### Step 2: Select Date Range")
        
        col2a, col2b = st.columns(2)
        with col2a:
            prev_month = st.selectbox("Previous Month", list(range(1, 13)), index=6, key="prev_month_auto")
            prev_year = st.number_input("Previous Year", min_value=2024, max_value=2035, value=2026, step=1, key="prev_year_auto")
        
        with col2b:
            curr_month = st.selectbox("Current Month", list(range(1, 13)), index=7, key="curr_month_auto")
            curr_year = st.number_input("Current Year", min_value=2024, max_value=2035, value=2026, step=1, key="curr_year_auto")
    
    st.markdown("### Step 3: Fetch & Compare")
    
    if st.button("Fetch both months and compare", key="fetch_and_compare"):
        st.info("⏳ Fetching data for both months... this may take 2-3 minutes.")
        
        prev_payload = {
            "month": prev_month,
            "year": prev_year,
            "dist_code": str(dist_code),
            "afso_code": str(afso_code),
            "fps_id": str(fps_id) if fps_id else "",
            "comm_id": "",
        }
        
        curr_payload = {
            "month": curr_month,
            "year": curr_year,
            "dist_code": str(dist_code),
            "afso_code": str(afso_code),
            "fps_id": str(fps_id) if fps_id else "",
            "comm_id": "",
        }
        
        try:
            with st.spinner("Fetching previous month data..."):
                prev_report = fetch_epos_report(prev_payload)
                # Report can be list or dict - both are valid
                prev_data_parsed = parse_epos_report_to_cards(prev_report) if prev_report else {}
                st.session_state["epos_prev_data"] = prev_data_parsed
                st.session_state["epos_prev_raw"] = prev_report
            
            with st.spinner("Fetching current month data..."):
                curr_report = fetch_epos_report(curr_payload)
                # Report can be list or dict - both are valid
                curr_data_parsed = parse_epos_report_to_cards(curr_report) if curr_report else {}
                st.session_state["epos_curr_data"] = curr_data_parsed
                st.session_state["epos_curr_raw"] = curr_report
            
            prev_data = st.session_state["epos_prev_data"]
            curr_data = st.session_state["epos_curr_data"]
            
            st.success("✅ Data fetch completed!")
            
            # # Show raw response for debugging
            # with st.expander("📋 Raw API Response (for debugging)"):
            #     col_d1, col_d2 = st.columns(2)
            #     with col_d1:
            #         st.write("**Previous Month Raw Response:**")
            #         st.json(st.session_state.get("epos_prev_raw", {})[:200] if isinstance(st.session_state.get("epos_prev_raw"), str) else st.session_state.get("epos_prev_raw", {}))
            #     with col_d2:
            #         st.write("**Current Month Raw Response:**")
            #         st.json(st.session_state.get("epos_curr_raw", {})[:200] if isinstance(st.session_state.get("epos_curr_raw"), str) else st.session_state.get("epos_curr_raw", {}))
            
            if not prev_data:
                st.warning(f"⚠️ No cards found in previous month response. Raw response: {st.session_state.get('epos_prev_raw', {})}")
                st.info("The API may have returned data in a different format than expected. Check the raw response above.")
                return
            
            if not curr_data:
                st.warning(f"⚠️ No cards found in current month response. Raw response: {st.session_state.get('epos_curr_raw', {})}")
                st.info("The API may have returned data in a different format than expected. Check the raw response above.")
                return
            
            st.success(f"✅ Data fetched successfully!")
            st.session_state["trigger_analysis"] = True
            
        except Exception as exc:
            st.error(f"❌ Failed to fetch data: {exc}")
            st.warning("💡 The Bihar ePOS server may be slow or unreachable. Try again or use the Upload mode.")



def render_upload_mode_ui():
    """Upload mode for Excel / CSV / TXT files."""
    txt_types = ["txt", "csv", "xlsx", "xls"]
    uploaded_file1 = st.file_uploader(T["upload_prev"], type=txt_types, disabled=False)
    uploaded_file2 = st.file_uploader(T["upload_curr"], type=txt_types, disabled=False)

    if uploaded_file1:
        file1_ext = uploaded_file1.name.lower().split(".")[-1]
        if file1_ext in {"xlsx", "xls", "csv"}:
            st.session_state.prev_content = uploaded_file1.getvalue()
            st.session_state.prev_content_source = "excel"
        else:
            st.session_state.prev_content = uploaded_file1.getvalue().decode("utf-8")
            st.session_state.prev_content_source = "txt"
    if uploaded_file2:
        file2_ext = uploaded_file2.name.lower().split(".")[-1]
        if file2_ext in {"xlsx", "xls", "csv"}:
            st.session_state.curr_content = uploaded_file2.getvalue()
            st.session_state.curr_content_source = "excel"
        else:
            st.session_state.curr_content = uploaded_file2.getvalue().decode("utf-8")
            st.session_state.curr_content_source = "txt"

    if uploaded_file1 is None:
        st.session_state.pop("prev_content", None)
        st.session_state.pop("prev_content_source", None)
    if uploaded_file2 is None:
        st.session_state.pop("curr_content", None)
        st.session_state.pop("curr_content_source", None)

    if uploaded_file1:
        uploaded_file1.name = uploaded_file1.name or "previous.xlsx"
    if uploaded_file2:
        uploaded_file2.name = uploaded_file2.name or "current.xlsx"

    if not (uploaded_file1 and uploaded_file2):
        st.session_state["trigger_analysis"] = False
        st.session_state.pop("prev_data", None)
        st.session_state.pop("curr_data", None)
        st.session_state.pop("prev_cards", None)
        st.session_state.pop("curr_cards", None)
        st.warning("⚠️ Please upload both Excel files to proceed.")

    return uploaded_file1, uploaded_file2, False


# Data source selection: upload remains the working flow; live automation is a new separate mode.
data_mode = st.radio(
    "Data Source",
    [
        "Upload Excel Files (Monthly export)",
        "Automation from Bihar ePOS (WIP)"
    ],
    index=0,
)


if data_mode == "Automation from Bihar ePOS (WIP)":
    render_epos_automation_mode()
    file1, file2, html_mode = None, None, False
else:
    st.subheader("Upload files (TXT / Excel)")
    file1, file2, html_mode = render_upload_mode_ui()

    if not (file1 and file2):
        st.warning("⚠️ Please upload both Excel files to proceed.")


#admin part start
# # check if .env exists
# if os.path.exists(".env"):
#     try:
#         from dotenv import load_dotenv
#         load_dotenv()
#         ADMIN_USER = os.getenv("ADMIN_USER", "admin")
#         ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")
#     except Exception:
#         ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
#         ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")
# else:
#     # Use safe defaults if secrets are not configured
#     ADMIN_USER = st.secrets.get("ADMIN_USER", "admin")
#     ADMIN_PASS = st.secrets.get("ADMIN_PASS", "admin")

#below is for render 
from dotenv import load_dotenv

# Loads .env locally if it exists.
# On Render, values come from Environment Variables.
load_dotenv()

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin")


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
 
#admin part end

def normalize_card_value(value):
    if value is None or pd.isna(value):
        return ""
    value = str(value).strip()
    value = re.sub(r"[^0-9A-Za-z]", "", value)
    return value


def normalize_header(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def extract_card_number_from_values(values):
    for value in values:
        if value is None or pd.isna(value):
            continue
        text = str(value).strip()
        digits = re.sub(r"[^0-9]", "", text)
        if 12 <= len(digits) <= 25 and digits.isdigit():
            return digits
    return ""


def extract_quantity_values_from_values(values):
    numbers = []
    for value in values:
        if value is None or pd.isna(value):
            continue
        text = str(value)
        matches = re.findall(r"\d+(?:\.\d+)?", text)
        for match in matches:
            try:
                numbers.append(float(match))
            except ValueError:
                continue
    # keep only realistic ration quantities and ignore date numbers like day/month/year
    filtered = []
    for n in numbers:
        if 0 <= n <= 500:
            filtered.append(n)
    return filtered


def read_excel_or_text_file(file):
    if file is None:
        return pd.DataFrame()

    name = getattr(file, "name", "").lower()
    data = file.getvalue()
    text = data.decode("utf-8", errors="replace")
    text_trim = text.lstrip()

    if text_trim.startswith("<") and ("<table" in text_trim.lower() or "<html" in text_trim.lower()):
        try:
            html_tables = pd.read_html(text)
            if html_tables:
                return html_tables[0]
        except Exception:
            pass
        try:
            return parse_html_table(text)
        except Exception:
            pass

    try:
        if name.endswith(".xlsx") or name.endswith(".xls"):
            try:
                return pd.read_excel(io.BytesIO(data), engine="openpyxl" if name.endswith(".xlsx") else "xlrd")
            except Exception:
                try:
                    return pd.read_excel(io.BytesIO(data), engine="openpyxl")
                except Exception:
                    return pd.DataFrame()
        if name.endswith(".csv"):
            try:
                return pd.read_csv(io.StringIO(text), sep=None, engine="python")
            except Exception:
                return pd.read_csv(io.StringIO(text), sep=';')
        return pd.read_fwf(io.StringIO(text, newline=""))
    except Exception:
        try:
            try:
                return pd.read_csv(io.StringIO(text), sep=None, engine="python")
            except Exception:
                return pd.read_csv(io.StringIO(text), sep=';')
        except Exception:
            return pd.DataFrame()


def extract_ration_data(file):
    if file is None:
        return {}

    name = getattr(file, "name", "").lower()
    data = file.getvalue()

    if name.endswith(".xlsx") or name.endswith(".xls") or name.endswith(".csv"):
        df = read_excel_or_text_file(file)
        if df.empty:
            return {}

        df = df.dropna(how="all").copy()
        df.columns = [str(c).strip() for c in df.columns]

        all_values = df.to_numpy().flatten().tolist()
        card_candidates = []
        for value in all_values:
            if value is None or pd.isna(value):
                continue
            text = str(value).strip()
            digits = re.sub(r"[^0-9]", "", text)
            if 12 <= len(digits) <= 25 and digits.isdigit():
                card_candidates.append(digits)

        if not card_candidates:
            return {}

        cols = {normalize_header(c): c for c in df.columns}

        def find_column(aliases):
            aliases_norm = [normalize_header(a) for a in aliases]
            for alias in aliases_norm:
                if alias in cols:
                    return cols[alias]
            for c in df.columns:
                key = normalize_header(c)
                if any(alias in key for alias in aliases_norm):
                    return c
            return None

        card_col = find_column(["rc no", "ration card no", "ration card", "card no", "rc", "cardnumber", "rationcard", "rationcardno"])
        wheat_col = find_column(["wheat", "wheatkg", "qty in kgs", "qtyinkgs", "qtyinkg", "wheat qty", "qtykgwheat"])
        rice_col = find_column(["rice", "f rice", "ricekg", "qty in kgs rice", "rice qty", "f rice qty", "qtykgrice"])
        card_type_col = find_column(["scheme", "scheme name", "avail type", "type", "schemecode"])

        parsed = {}
        for _, row in df.iterrows():
            try:
                row_values = row.tolist()
                card = ""
                if card_col is not None:
                    card = normalize_card_value(row.get(card_col, ""))
                if not card:
                    card = extract_card_number_from_values(row_values)
                if not card:
                    continue

                if card_type_col is not None:
                    raw_type = row.get(card_type_col, "Unknown")
                    card_type = str(raw_type).strip() if raw_type is not None and not pd.isna(raw_type) else "Unknown"
                else:
                    card_type = "Unknown"

                if wheat_col is not None:
                    wheat = safe_float(row.get(wheat_col, 0))
                else:
                    qtys = extract_quantity_values_from_values(row_values)
                    wheat = qtys[0] if qtys else 0.0

                if rice_col is not None:
                    rice = safe_float(row.get(rice_col, 0))
                else:
                    rice = 0.0

                parsed[card] = (card_type, wheat, rice)
            except Exception:
                continue

        if parsed:
            return parsed

        # final generic fallback: pick the first long numeric token in each row as card and the first few numeric quantities as wheat/rice values.
        for _, row in df.iterrows():
            row_values = row.tolist()
            card = extract_card_number_from_values(row_values)
            if not card:
                continue
            qtys = extract_quantity_values_from_values(row_values)
            wheat = qtys[0] if qtys else 0.0
            rice = qtys[1] if len(qtys) > 1 else 0.0
            parsed[card] = ("Unknown", wheat, rice)
        return parsed

    parsed = {}
    lines = data.decode("utf-8", errors="replace").splitlines()
    for idx, line in enumerate(lines, start=1):
        raw = line.strip()
        if not raw:
            continue

        parts = raw.split()
        if len(parts) < 5:
            continue

        card = None
        card_index = None
        for i, token in enumerate(parts):
            cleaned = re.sub(r"[^0-9]", "", token)
            if len(cleaned) >= 12 and len(cleaned) <= 25 and token and token.replace(".", "").isdigit():
                card = cleaned
                card_index = i
                break

        if card is None:
            continue

        try:
            card_type = parts[2] if len(parts) > 2 else "Unknown"
            date_index = None
            for i, token in enumerate(parts):
                if re.match(r"^\d{2}-\d{2}-\d{4}$", token) or re.match(r"^\d{4}-\d{2}-\d{2}$", token):
                    date_index = i
                    break

            numeric = []
            if date_index is not None:
                for token in parts[date_index + 1:]:
                    if re.match(r"^[0-9]+(?:\.[0-9]+)?$", token):
                        numeric.append(safe_float(token))
            if len(numeric) >= 2:
                wheat = numeric[0]
                rice = numeric[1]
            else:
                # Fallback: choose the first two numeric values after the date or after the card column.
                fallback_tokens = []
                for token in parts[max(0, card_index + 1):]:
                    if re.match(r"^[0-9]+(?:\.[0-9]+)?$", token):
                        fallback_tokens.append(safe_float(token))
                wheat = fallback_tokens[0] if len(fallback_tokens) > 0 else 0.0
                rice = fallback_tokens[1] if len(fallback_tokens) > 1 else 0.0

            parsed[card] = (card_type, wheat, rice)
        except Exception:
            st.warning(f"⚠️ Error parsing line {idx}: {line}")
            continue

    return parsed


def extract_ration_numbers(file):
    if file is None:
        return []

    # Prefer the same data extraction used for actual comparison; this keeps upload totals
    # in sync with parsed card data even when the export is HTML-disguised as .xls.
    parsed = extract_ration_data(file)
    if parsed:
        return list(parsed.keys())

    name = getattr(file, "name", "").lower()
    if name.endswith(".xlsx") or name.endswith(".xls") or name.endswith(".csv"):
        df = read_excel_or_text_file(file)
        if df.empty:
            return []

        columns = {normalize_header(c): c for c in df.columns}
        def find_column(aliases):
            aliases_norm = [normalize_header(a) for a in aliases]
            for alias in aliases_norm:
                if alias in columns:
                    return columns[alias]
            for c in df.columns:
                key = normalize_header(c)
                if any(alias in key for alias in aliases_norm):
                    return c
            return None

        card_col = find_column(["rc no", "ration card no", "ration card", "card no", "rc", "cardnumber", "rationcard", "rationcardno"])
        if card_col is None:
            # fallback: scan each row for a 12-25 digit token and preserve it as a card id
            cards = []
            for _, row in df.iterrows():
                for value in row.tolist():
                    card = normalize_card_value(value)
                    if len(card) >= 12 and len(card) <= 25:
                        cards.append(card)
                        break
            return cards
        cards = []
        for value in df[card_col].dropna().tolist():
            card = normalize_card_value(value)
            if card:
                cards.append(card)
        return cards

    cards = []
    for line in file.getvalue().decode("utf-8", errors="replace").splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        for token in parts:
            cleaned = re.sub(r"[^0-9]", "", token)
            if len(cleaned) >= 12 and len(cleaned) <= 25 and cleaned.isdigit():
                cards.append(cleaned)
                break
    return cards

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

can_run_analysis = (
    (data_mode == "Upload Excel Files (Monthly export)" and file1 is not None and file2 is not None)
    or (data_mode == "Automation from Bihar ePOS (WIP)" and st.session_state.get("epos_prev_data") and st.session_state.get("epos_curr_data"))
    or (data_mode != "Upload Excel Files (Monthly export)" and st.session_state.get("prev_content") and st.session_state.get("curr_content"))
    or st.session_state.get("trigger_analysis", False)
)

if can_run_analysis:
    st.session_state["trigger_analysis"] = False
    with st.spinner("🔄 Analyzing data, please wait..."):
        # Determine data source: automation, HTML export, or Excel file
        if data_mode == "Automation from Bihar ePOS (WIP)":
            prev_data = st.session_state.get("epos_prev_data", {})
            curr_data = st.session_state.get("epos_curr_data", {})
            html_mode = False
        elif html_mode:
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
        elif data_mode == "Automation from Bihar ePOS (WIP)":
            # Automation mode: use fetched data directly
            st.success("✅ Data fetched from Bihar ePOS successfully!")
            st.session_state["prev_data"] = prev_data
            st.session_state["curr_data"] = curr_data
            st.session_state["prev_cards"] = set(prev_data.keys())
            st.session_state["curr_cards"] = set(curr_data.keys())
        else:
            uploaded_pair = {
                "prev_name": file1.name,
                "curr_name": file2.name,
                "prev_content": file1.getvalue(),
                "curr_content": file2.getvalue(),
                "prev_source": "excel",
                "curr_source": "excel",
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

    search_query = st.text_input(f"🔍 {T['search_placeholder']}", key="search_input")

    if search_query:
        suggestion_cards = []
        for card in sorted(prev_cards | curr_cards):
            owner = card_owners.get(card, "")
            if search_query.lower() in card.lower() or (owner and search_query.lower() in owner.lower()):
                suggestion_cards.append((card, owner))

        if suggestion_cards:
            st.caption("Suggestions")
            suggestion_limit = min(len(suggestion_cards), 8)
            suggestion_cols = st.columns(min(4, suggestion_limit))
            for idx, (card, owner) in enumerate(suggestion_cards[:suggestion_limit]):
                label = f"{card} ({owner})" if owner else card
                with suggestion_cols[idx % len(suggestion_cols)]:
                    if st.button(label, key=f"suggest_{card}_{idx}"):
                        st.session_state["search_input"] = card
                        search_query = card

        st.subheader("🔎 Search Results")
        matching_cards = [
            card for card in (prev_cards | curr_cards)
            if search_query.lower() in card.lower() or
            (card_owners.get(card) and search_query.lower() in card_owners[card].lower())
        ]
        if matching_cards:
            search_rows = []
            for card in matching_cards:
                in_prev = card in prev_cards
                in_curr = card in curr_cards
                if in_prev and in_curr:
                    status = "✅ Present in both"
                elif in_prev:
                    status = "✅ Previous only"
                elif in_curr:
                    status = "✅ Current only"
                else:
                    status = "❌ Not found"

                card_data = prev_data.get(card) or curr_data.get(card) or ("Unknown", 0, 0)
                search_rows.append({
                    "Ration Card": card,
                    "Status": status,
                    "Prev Month": "✅" if in_prev else "❌",
                    "Current Month": "✅" if in_curr else "❌",
                    "Card Type": card_data[0],
                    "Card Holder": get_owner(card),
                    "Wheat (kg)": card_data[1],
                    "Rice (kg)": card_data[2]
                })

            results_df = pd.DataFrame(search_rows)
            st.dataframe(results_df, use_container_width=True)
        else:
            st.warning("No match found.")

    missing_owner_cards = [card for card in (prev_cards | curr_cards) if card_owners.get(card) is None]

    if missing_owner_cards:
        with st.expander("👤 Add Missing Card Owner Names", expanded=False):
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

    prev_total = len(prev_cards) if prev_cards is not None else 0
    curr_total = len(curr_cards) if curr_cards is not None else 0

    st.success(f"✅ Total Ration Cards (Previous Month): **{prev_total}**")
    st.success(f"✅ Total Ration Cards (Current Month): **{curr_total}**")

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


if "left_cards" in locals() and "new_cards" in locals() and "changed_cards" in locals():
    st.subheader("🖨️ Print / Save as PDF")
    st.caption("Choose the sections, then use your device print dialog to print or save the report as a PDF.")

    print_choices = st.multiselect(
        "✅ Sections to include",
        options=["Missing Ration Cards", "New Ration Cards", "Changed Ration Allotments"],
        default=["Missing Ration Cards", "New Ration Cards", "Changed Ration Allotments"],
        key="print_choices"
    )

    printable_html = """
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; padding: 16px; color: #202124; font-family: Arial, sans-serif; }
        h1 { margin: 0 0 6px; font-size: 24px; }
        h2 { margin: 22px 0 8px; padding-bottom: 5px; border-bottom: 2px solid #4CAF50; font-size: 18px; }
        p { margin: 4px 0 14px; }
        .summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 14px 0 20px; }
        .summary div { padding: 9px; background: #eef6ef; border: 1px solid #c8dfca; }
        .table-wrap { width: 100%%; overflow-x: auto; margin-bottom: 18px; }
        table { width: 100%%; min-width: 560px; border-collapse: collapse; background: #fff; }
        th, td { padding: 7px; border: 1px solid #aaa; text-align: left; font-size: 12px; overflow-wrap: anywhere; }
        th { background: #4CAF50; color: white; }
        .empty { padding: 10px; border: 1px solid #ddd; color: #666; }
        @media (max-width: 600px) {
            body { padding: 10px; }
            h1 { font-size: 20px; }
            th, td { padding: 5px; font-size: 10px; }
        }
        @media print {
            body { padding: 0; }
            .table-wrap { overflow: visible; }
            table { min-width: 0; }
            h2 { break-after: avoid; }
            tr { break-inside: avoid; }
        }
    </style>
    <h1>Ration Card Comparison Report</h1>
    <p>Generated on: %s</p>
    <div class="summary">
        <div><strong>Previous Month:</strong> %s cards</div>
        <div><strong>Current Month:</strong> %s cards</div>
        <div><strong>Missing:</strong> %s cards</div>
        <div><strong>New:</strong> %s cards</div>
        <div><strong>Changed:</strong> %s cards</div>
    </div>
    """ % (datetime.now().strftime("%d %b %Y, %I:%M %p"), len(prev_cards), len(curr_cards), len(left_cards), len(new_cards), len(changed_cards))

    def add_print_table(title, dataframe, card_count):
        if card_count:
            return f"<h2>{title}</h2><div class='table-wrap'>{dataframe.to_html(index=False, escape=True)}</div>"
        return f"<h2>{title}</h2><div class='empty'>No records in this section.</div>"

    if "Missing Ration Cards" in print_choices:
        printable_html += add_print_table("Missing Ration Cards", left_df if left_cards else pd.DataFrame(), len(left_cards))
    if "New Ration Cards" in print_choices:
        printable_html += add_print_table("New Ration Cards", new_df if new_cards else pd.DataFrame(), len(new_cards))
    if "Changed Ration Allotments" in print_choices:
        printable_html += add_print_table("Changed Ration Allotments", changed_df if changed_cards else pd.DataFrame(), len(changed_cards))

    printable_html = printable_html.replace("`", "\\`").replace("${", "\\${")
    components.html(f"""
        <div style="padding: 4px 0; color: #555;">Preview is formatted for phone and laptop printing.</div>
        <button onclick="printReport()" style="width: 100%; max-width: 320px; padding: 13px 18px; font-size: 16px;
                background-color: #4CAF50; color: white; border: none; border-radius: 6px; cursor: pointer;">
            🖨️ Print / Save PDF
        </button>
        <script>
            const reportHtml = `{printable_html}`;
            function printReport() {{
                const printWindow = window.open('', '_blank');
                if (!printWindow) {{
                    alert('Please allow pop-ups for this app, then try again.');
                    return;
                }}
                printWindow.document.open();
                printWindow.document.write('<!doctype html><html><head><title>Ration Card Comparison Report</title></head><body>' + reportHtml + '</body></html>');
                printWindow.document.close();
                printWindow.onload = function() {{
                    printWindow.focus();
                    printWindow.print();
                }};
            }}
        </script>
    """, height=110, scrolling=False)


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
