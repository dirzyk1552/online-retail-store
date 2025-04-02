import datetime
import streamlit as st
import pandas as pd
import io


# Function to fetch manager data
def fetch_manager_data(conn):
    try:
        query = "SELECT * FROM ONLINE_RETAIL.TEST_MANAGER;"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

        
# Function to retrieve revenue over date range
def get_revenue(conn, start_date, end_date):
    try:
        cursor = conn.cursor()
        query = f"""select sum(product_price*quantity) as "Revenue"
        from ONLINE_RETAIL.cart_info
        where insert_ts::date between '{start_date}' and '{end_date}';"""
        df = pd.read_sql_query(query, conn)
        print_revenue(df)
    except Exception as e:
        st.error(f"Error retrieving revenue: {e}")
        

# Function to retrieve sales of most popular products
def get_bestsellers(conn, start_date, end_date, filter):
    try:
        cursor = conn.cursor()
        query = f"""select product_name as "Product", sum(product_price*quantity) as "Total Sales"
        from ONLINE_RETAIL.cart_info
        where insert_ts::date between '{start_date}' and '{end_date}'
        group by "Product"
        order by "Total Sales" desc
        limit {filter}
        ;"""
        df = pd.read_sql_query(query, conn)
        print_salesinfo(df)
    except Exception as e:
        st.error(f"Error retrieving bestsellers: {e}")
        

# Function to generate sales report
def get_salesreport(conn):
    try:
        cursor = conn.cursor()
        query = """select insert_ts::date as "Date of Purchase" ,product_name as "Product", sum(quantity) as "Quantity Sold", sum(product_price*quantity) as "Total Sales"
        from ONLINE_RETAIL.cart_info
        group by "Date of Purchase", "Product"
        order by "Date of Purchase" desc
        ;"""
        df = pd.read_sql_query(query, conn)
        print_salesinfo(df)
        
    except Exception as e:
        st.error(f"Error generating sales report: {e}")
        
        
#Function to format and print revenue
def print_revenue(revenue_df):
    for index, row in revenue_df.iterrows():
        st.write(f"**Revenue over selected time interval:**  {row[0]}")
        
        
#Function to format and print popular products and sales report
def print_salesinfo(report_df):
    st.table(report_df)
    
 
# Function to enter start and end dates, and if applicable popularity filter, for reports
def enter_salesinfo_fields(conn, info_type):
    if info_type != "Sales Report":
        start_date = st.date_input("Start Date", value="today", min_value=None, max_value=None, key=None, help=None, on_change=None, args=None, kwargs=None, format="YYYY-MM-DD", disabled=False, label_visibility="visible")
        end_date = st.date_input("End Date", value="today", min_value=None, max_value=None, key=None, help=None, on_change=None, args=None, kwargs=None, format="YYYY-MM-DD", disabled=False, label_visibility="visible")
    if info_type == "Bestsellers":
        filter = st.number_input("Number of itmes to display", min_value=1, value=1)
        if(st.button("Retrieve Info")):
            get_bestsellers(conn, start_date, end_date, filter)
    elif info_type == "Revenue":
        if(st.button("Retrieve Info")):
            get_revenue(conn, start_date, end_date)
    else:
        if(st.button("Retrieve Info")):
            get_salesreport(conn)
        
 
# manager screen function
def manager_screen():
    # Display header for Manager Screen
    st.title("Manager Screen")
    
    # Fetch and display manager data
    conn = st.session_state.get("db_connection")  # Retrieve connection from session state
    if conn:
        #manager_data = fetch_manager_data(conn)
        #if manager_data is not None:
            #st.dataframe(manager_data)
        
        #Options for reports; note the blank string inputted for a blank row
        info_options = ["Revenue", "Bestsellers", "Sales Report"]
        #Menu for report options
        st.header("View revenue, bestselling products, or sales report ")
        info_choice = st.selectbox("Get information on", options = info_options)
        
        enter_salesinfo_fields(conn, info_choice)
        
        # Close connection when done (optional)
        if st.button("Logout"):
            conn.close()
            del st.session_state["logged_in"]  # Clear login state
            del st.session_state["db_connection"]  # Clear connection from session state
            st.rerun()  # Redirect back to Login Screen

