import streamlit as st

st.set_page_config(page_title="Ration Card Comparison App Best way to find your left ration coustomer")

st.title("❤️Comparison Tool by @ibevishal")
st.write("Upload your `.txt` files only to compare ration card numbers between two months.")


file1 = st.file_uploader("Upload Previous Month File ", type=["txt"])
file2 = st.file_uploader("Upload Current Month File ", type=["txt"])

def extract_ration_numbers(file):
    ration_list = []
    for line in file.getvalue().decode("utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            ration_list.append(parts[1])
    return ration_list

# Process when both files are uploaded
if file1 and file2:
    list1 = extract_ration_numbers(file1)
    list2 = extract_ration_numbers(file2)

    st.subheader(" Summary scroll to see full detail")
    st.write(f"Total Ration Cards (Previous Month): **{len(list1)}**")
    st.write(f"Total Ration Cards (Current Month): **{len(list2)}**")

    unique_in_list1 = sorted([x for x in list1 if x not in list2])
    unique_in_list2 = sorted([x for x in list2 if x not in list1])

    st.subheader(" Ration Cards Left for allotement ")
    st.write(f"Count: **{len(unique_in_list1)}**")
    if unique_in_list1:
        st.text_area("Ration Numbers:", "\n".join(unique_in_list1), height=200)

    st.subheader("🆕 New Ration Cards This Month")
    st.write(f"Count: **{len(unique_in_list2)}**")
    if unique_in_list2:
        st.text_area("Ration Numbers:", "\n".join(unique_in_list2), height=200)



# to run python -m streamlit run app.py
