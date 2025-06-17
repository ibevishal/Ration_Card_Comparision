import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Ration Card Comparison App", layout="centered")

st.title("Ration Card😶‍🌫️Comparison Tool")
st.caption("Created with ❤️ by @ibe.vishal")
st.write("Upload `.txt` files to compare Ration allotments between two months.")

# Upload previous and current month files
file1 = st.file_uploader("📤 Upload Previous Month File", type=["txt"])
file2 = st.file_uploader("📤 Upload Current Month File", type=["txt"])

if file1:
    with st.expander("📄 Preview Previous Month File"):
        st.text(file1.getvalue().decode("utf-8")[:1000])  # Preview first 1000 chars

if file2:
    with st.expander("📄 Preview Current Month File"):
        st.text(file2.getvalue().decode("utf-8")[:1000])

if not (file1 and file2):
    st.warning("⚠️ Please upload both files to proceed.")

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

# Main processing
if file1 and file2:
    list1 = extract_ration_numbers(file1)
    list2 = extract_ration_numbers(file2)

    st.subheader("📊 Data for checking / Verify from site")
    st.info(f"✅ Total Ration Cards (Previous Month with same card included): **{len(list1)}**")
    st.info(f"✅ Total Ration Cards (Current Month with same card included): **{len(list2)}**")

    prev_data = extract_ration_data(file1)
    curr_data = extract_ration_data(file2)

    prev_cards = set(prev_data.keys())
    curr_cards = set(curr_data.keys())

    st.subheader("📊 Summary ")
    st.success(f"✅ Total Ration Cards (Previous Month): **{len(prev_cards)}**")
    st.success(f"✅ Total Ration Cards (Current Month): **{len(curr_cards)}**")

    left_cards = sorted(prev_cards - curr_cards)
    new_cards = sorted(curr_cards - prev_cards)

    st.subheader("❌ Ration Cards Missing in Current Month")
    st.info(f"🧮 Total Missing: **{len(left_cards)}**")
    if left_cards:
        left_df = pd.DataFrame([
            {
                "Ration Card": card,
                "Card Type": prev_data[card][0],
                "Wheat (kg)": prev_data[card][1],
                "Rice (kg)": prev_data[card][2]
            }
            for card in left_cards
        ])
        st.dataframe(left_df, use_container_width=True)

    st.subheader("🆕 New Ration Cards Added This Month")
    st.info(f"🧮 Total New: **{len(new_cards)}**")
    if new_cards:
        new_df = pd.DataFrame([
            {
                "Ration Card": card,
                "Card Type": curr_data[card][0],
                "Wheat (kg)": curr_data[card][1],
                "Rice (kg)": curr_data[card][2]
            }
            for card in new_cards
        ])
        st.dataframe(new_df, use_container_width=True)

    changed_cards = sorted([
        card for card in prev_cards & curr_cards
        if prev_data[card][1:] != curr_data[card][1:]
    ])

    if changed_cards:
        st.subheader("🔄 Ration Allotment Changed")
        st.info(f"🧮 Total Changed: **{len(changed_cards)}**")
        changed_df = pd.DataFrame([
            {
                "Ration Card": card,
                "Card Type": curr_data[card][0],
                "Wheat (Previous)": prev_data[card][1],
                "Wheat (Current)": curr_data[card][1],
                "Rice (Previous)": prev_data[card][2],
                "Rice (Current)": curr_data[card][2]
            }
            for card in changed_cards
        ])
        st.dataframe(changed_df, use_container_width=True)

        changed_details = [
            f"{card} ➤ Wheat: {prev_data[card][1]} ➝ {curr_data[card][1]} {'🔼' if float(curr_data[card][1]) > float(prev_data[card][1]) else '🔽'} | "
            f"Rice: {prev_data[card][2]} ➝ {curr_data[card][2]} {'🔼' if float(curr_data[card][2]) > float(prev_data[card][2]) else '🔽'}"
            for card in changed_cards
        ]
    else:
        changed_details = []

    # Generate download report
    # output_sections = []
    # if left_cards:
    #     output_sections.append("❌ Missing Ration Cards in Current Month:\n" + "\n".join(left_df.astype(str).apply(lambda row: f"{row['Ration Card']} ➤ {row['Card Type']} Wheat: {row['Wheat (kg)']} kg, Rice: {row['Rice (kg)']} kg", axis=1)))
    # if new_cards:
    #     output_sections.append("🆕 New Ration Cards Added This Month:\n" + "\n".join(new_df.astype(str).apply(lambda row: f"{row['Ration Card']} ➤ {row['Card Type']} Wheat: {row['Wheat (kg)']} kg, Rice: {row['Rice (kg)']} kg", axis=1)))
    # if changed_cards:
    #     output_sections.append("🔄 Ration Allotment Changes:\n" + "\n".join(changed_details))

    # full_output = "\n\n".join(output_sections)

    # if full_output:
    #     st.download_button(
    #         label="🖨️ Download Full Comparison Report (TXT)",
    #         data=full_output,
    #         file_name="ration_card_comparison_report.txt",
    #         mime="text/plain"
    #     )



if file1 and file2:
    # Combine all three tables into one printable HTML block
    printable_html = """
    <style>
        h3 {
            font-family: Arial, sans-serif;
            margin-top: 30px;
        }
        .missing { color: red; }
        .new { color: green; }
        .changed { color: orange; }

        table, th, td {
            border: 1px solid #aaa;
            border-collapse: collapse;
        }
        th, td {
            padding: 8px;
            font-size: 14px;
        }
        table {
            width: 100%;
            margin-bottom: 30px;
            background-color: #f9f9f9;
        }
    </style>
    """

    if left_cards:
        printable_html += "<h3 class='missing'>❌ Missing Ration Cards</h3>"
        printable_html += left_df.to_html(index=True, escape=False)

    if new_cards:
        printable_html += "<h3 class='new'>🆕 New Ration Cards</h3>"
        printable_html += new_df.to_html(index=True, escape=False)

    if changed_cards:
        printable_html += "<h3 class='changed'>🔄 Changed Ration Allotments</h3>"
        printable_html += changed_df.to_html(index=True, escape=False)

    # Embed HTML and JS for printing
    components.html(f"""
        <div id="print-section">
            {printable_html}
        </div>
        <button onclick="printReport()" style="
            margin-top: 20px;
            padding: 15px 30px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        ">🖨️ Print Report</button>
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
st.caption("💡 Ensure your `.txt` files are properly / directly extracted from the original site")
st.caption("Step-1 : Search for 'sales register' under 'FPS tab' in 'AEPDS site' and get you data ")
st.caption("Step-2 : Copy data from starting ration card include s.no (❌ without heading)")

file_path = "example.txt"
with open(file_path, "rb") as file:
    st.download_button(
        label="⬇️ Download example.txt",
        data=file,
        file_name="example.txt",
        mime="text/plain"
    )

st.caption("Step-3 : Create text file and paste it in text file")
st.caption("Step-4 : Upload the text file on our site/app")

st.markdown("---")
st.caption("❤️VISHAL KUMAR✌️")
st.caption("Help : insta- @ibe.vishal")
