import streamlit as st
import subprocess

st.title("Confluence Data Lifecycle Manager")

st.write("Manage Keep / Archive / Delete workflow")

if st.button("Start Data Management"):
    result = subprocess.run(["python", "start_data_management.py"])
    if result.returncode == 0:
        st.success("Excel file generated successfully.")
    else:
        st.error("Process failed.")

if st.button("Complete Data Management"):
    result = subprocess.run(["python", "complete_data_management.py"])
    if result.returncode == 0:
        st.success("Data management completed.")
    else:
        st.error("Process failed.")
