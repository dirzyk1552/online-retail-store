import streamlit as st
from login import login_page
from customer_screen import customer_screen
from retailer_screen import retailer_screen
from manager_screen import manager_screen
from administrator_screen import administrator_screen

# Initialize session state for login tracking and role management
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "user_role" not in st.session_state:
    st.session_state["user_role"] = None

# Show appropriate screen based on login status and role
if not st.session_state["logged_in"]:
    login_page()
else:
    user_role = st.session_state["user_role"]
    
    if user_role == "customer_role":
        customer_screen()
    elif user_role == "retailer_role":
        retailer_screen()
    elif user_role == "manager_role":
        manager_screen()
    elif user_role == "administrator_role":
        administrator_screen()
    else:
        st.error("Unknown role detected. Please contact support.")
