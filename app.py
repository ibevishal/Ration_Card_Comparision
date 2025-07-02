import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import io
import csv
from datetime import datetime
import streamlit.web as st_web

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
username = st.sidebar.text_input("👤 Please enter your name to continue")

if not st.session_state.get("logged_in"):
    if st.sidebar.button("Continue"):
        if username:
            if username not in users:
                save_user(username)
            st.session_state["logged_in"] = True
            user_agent = st.session_state.get("_client_info", {}).get("user_agent", "unknown")
            client_ip = st.session_state.get("_client_info", {}).get("remote_ip", "unknown")

            # fallback for browser string if Streamlit _client_info missing
            if hasattr(st_web, '_current_client'):
                client = st_web._current_client()
                user_agent = getattr(client, "browser", "unknown")
                client_ip = getattr(client, "ip", "unknown")

            def log_user_activity(username):
                with open("activity_log.csv", "a", newline='', encoding="utf-8") as logfile:
                    writer = csv.writer(logfile)
                    writer.writerow([
                        username,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        user_agent,
                        client_ip
                    ])

            # save the activity log
            log_user_activity(username)
            st.session_state["username"] = username
            st.rerun()  # restart the app with session active
        else:
            st.sidebar.warning("⚠️ Please enter your name.")
        st.stop()


# check session
if not st.session_state.get("logged_in"):
    st.warning("🔒 Please enter your name to continue.")
    st.stop()

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
font_size = st.sidebar.slider("🔠 Font Size", min_value=12, max_value=24, value=14)
st.markdown(
    f"""
    <style>
    .stApp {{
        font-size: {font_size}px !important;
    }}
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
        st.session_state.trigger_analysis = True

 # === show the banner to everyone ===
if "BANNER_MESSAGE" not in st.session_state:
    st.session_state["BANNER_MESSAGE"] = BANNER_MESSAGE

if st.session_state["BANNER_MESSAGE"]:
    st.info(f"📢 **Admin Message:** {st.session_state['BANNER_MESSAGE']}")

    
st.caption(T["created_by"])
st.write("Upload `.txt` files to compare Ration allotments between two months.")

uploaded_file1 = st.file_uploader(T["upload_prev"], type=["txt"])
uploaded_file2 = st.file_uploader(T["upload_curr"], type=["txt"])

if uploaded_file1:
    st.session_state.prev_content = uploaded_file1.getvalue().decode("utf-8")
if uploaded_file2:
    st.session_state.curr_content = uploaded_file2.getvalue().decode("utf-8")

file1 = io.BytesIO(st.session_state["prev_content"].encode("utf-8")) if st.session_state.get("prev_content") else None
file2 = io.BytesIO(st.session_state["curr_content"].encode("utf-8")) if st.session_state.get("curr_content") else None

if file1:
    file1.name = "previous.txt"
    with st.expander("📄 Preview Previous Month File"):
        st.text(file1.getvalue().decode("utf-8")[:1000])

if file2:
    file2.name = "current.txt"
    with st.expander("📄 Preview Current Month File"):
        st.text(file2.getvalue().decode("utf-8")[:1000])

if not (file1 and file2):
    st.warning("⚠️ Please upload both files to proceed.")

#admin part start


import os



# check if .env exists
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()
    ADMIN_USER = os.getenv("ADMIN_USER")
    ADMIN_PASS = os.getenv("ADMIN_PASS")

else:
    ADMIN_USER = st.secrets["ADMIN_USER"]
    ADMIN_PASS = st.secrets["ADMIN_PASS"]


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
def safe_float(val):
    try:
        return float(val)
    except ValueError:
        return 0.0

def extract_ration_data(file):
    data = {}
    lines = file.getvalue().decode("utf-8").splitlines()
    for idx, line in enumerate(lines, start=1):
        parts = line.strip().split()
        if len(parts) >= 12:
            try:
                card = parts[1]
                card_type = parts[2]
                wheat = safe_float(parts[6])
                rice = safe_float(parts[10])
                data[card] = (card_type, wheat, rice)
            except IndexError:
                st.warning(f"⚠️ Error parsing line {idx}: {line}")
        else:
            st.warning(f"⚠️ Skipped malformed line {idx}: {line}")
    return data

def extract_ration_numbers(file):
    return [line.strip().split()[1] for line in file.getvalue().decode("utf-8").splitlines() if len(line.strip().split()) >= 2]

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

        prev_cards = set(prev_data.keys())
        curr_cards = set(curr_data.keys())

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
                "Card Type": prev_data.get(card, curr_data.get(card, ["Unknown"]))[0],
                "Card Holder": get_owner(card),
                "Wheat (kg)": (prev_data.get(card) or curr_data.get(card) or [None, 0, 0])[1],
                "Rice (kg)": (prev_data.get(card) or curr_data.get(card) or [None, 0, 0])[2]
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
    

    st.success(f"✅ Total Ration Cards (Previous Month): **{len(prev_cards)}**")
    st.success(f"✅ Total Ration Cards (Current Month): **{len(curr_cards)}**")

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


if file1 and file2:
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
st.caption("💡 Ensure your `.txt` files are properly extracted from the original site.")
st.caption("Step-1: Get 'sales register' under 'FPS tab' in 'AEPDS site'.")
st.caption("Step-2: Copy data starting with ration card (without header).")

file_path = "example.txt"
with open(file_path, "rb") as file:
    st.download_button("⬇️ Download example.txt", file, file_name="example.txt", mime="text/plain")

st.caption("Step-3: Save data to text file.")
st.caption("Step-4: Upload the text file on this app.")

st.markdown(
    """
    <hr>
    <p style="text-align:center;font-size:12px;color:gray;">
    ❤️ Built by Vishal Kumar | <a href="https://instagram.com/ibe.vishal" target="_blank">Instagram</a>
    </p>
    """,
    unsafe_allow_html=True
)
