import streamlit as st

st.set_page_config(page_title="Ration Card Comparison App", layout="centered")

st.title("Ration Card😶‍🌫️Comparison Tool")
st.caption("Created with ❤️ by @ibe.vishal")
st.write("Upload `.txt` files to compare Ration allotments between two months.")

# Upload previous and current month files
file1 = st.file_uploader("📤 Upload Previous Month File", type=["txt"])
file2 = st.file_uploader("📤 Upload Current Month File", type=["txt"])

# Function to extract data as dictionary {CardNumber: (CardType, Wheat, Rice)}
def extract_ration_data(file):
    data = {}
    for line in file.getvalue().decode("utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) >= 12:
            card = parts[1]
            card_type = parts[2]
            wheat = parts[6]
            rice = parts[10]
            data[card] = (card_type, wheat, rice)
    return data

def extract_ration_numbers(file):
    ration_listt = []
    for line in file.getvalue().decode("utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            ration_listt.append(parts[1])
    return ration_listt

# for verify only
if file1 and file2:
    list1 = extract_ration_numbers(file1)
    list2 = extract_ration_numbers(file2)
    
    st.subheader("📊 Data for checking / Verify from site")
    st.info(f"✅ Total Ration Cards (Previous Month with same card included): **{len(list1)}**")
    st.info(f"✅ Total Ration Cards (Current Month with same card included): **{len(list2)}**")


if file1 and file2:
    prev_data = extract_ration_data(file1)
    curr_data = extract_ration_data(file2) 

    prev_cards = set(prev_data.keys())
    curr_cards = set(curr_data.keys())

    st.subheader("📊 Summary scroll for more")
    st.success(f"✅ Total Ration Cards (Previous Month): **{len(prev_cards)}**")
    st.success(f"✅ Total Ration Cards (Current Month): **{len(curr_cards)}**")

    # Cards missing this month (were in previous)
    left_cards = sorted(prev_cards - curr_cards)
    # New cards this month (not in previous)
    new_cards = sorted(curr_cards - prev_cards)

    st.subheader("❌ Ration Cards Missing in Current Month")
    st.info(f"🧮 Total Missing: **{len(left_cards)}**")
    if left_cards:
        left_details = [
            f"{card}   ➤  {prev_data[card][0]}   👀    Wheat: {prev_data[card][1]} kg   🍵   Rice: {prev_data[card][2]} kg"
            for card in left_cards
        ]
        st.text_area("Details:", "\n".join(left_details), height=500)

    st.subheader("🆕 New Ration Cards Added This Month")
    st.info(f"🧮 Total New: **{len(new_cards)}**")
    if new_cards:
        new_details = [
            f"{card}   ➤   {curr_data[card][0]}   👀    Wheat: {curr_data[card][1]} kg   🍵   Rice: {curr_data[card][2]} kg"
            for card in new_cards
        ]
        st.text_area("Details:", "\n".join(new_details), height=500)

st.markdown("---")
st.caption("💡 Ensure your `.txt` files are properly / directly extracted from the original site")
st.caption("✈️STEP OF PROPER USE🙌")
st.caption("Step-1 : Search for 'sales register' under 'FPS tab' in 'AEPDS site' and get you data ")
st.caption("Step-2 : Copy data from starting ration card include s.no (❌ without  heading)")
file_path = "example.txt"
# Open and make it downloadable
with open(file_path, "rb") as file:
    st.download_button(
        label="⬇️ Download example.txt",
        data=file,
        file_name="example.txt",  # This is the name it will be downloaded as
        mime="text/plain"
    )
st.caption("Step-3 : Create text file and paste it in text file")
st.caption("Step-4 : Upload the text file on our site/app")

st.markdown("---")
st.caption("❤️VISHAL KUMAR✌️")
st.caption("Help : insta- @ibe.vishal")


#python -m streamlit run app.py to run