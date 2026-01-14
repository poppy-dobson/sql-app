import streamlit as st

st.title("[insert good title here]")

st.write("""
insert good description too
""")

uploaded_db_file = st.file_uploader("Upload an sqlite .db file", type=".db", key="db_upload")