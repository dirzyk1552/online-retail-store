import streamlit as st
import psycopg2

# Define the Security class
class Security:
    def __init__(self, userid, password):
        self.userid = userid
        self.password = password
        self.role_name = None  # Initialize role_name as None

    def validateCredentials(self):
        """
        Validates the user's credentials and establishes a database connection.
        Returns:
            conn: Database connection object if successful, None otherwise.
        """
        try:
            conn = psycopg2.connect(
                database="CSE682",
                user=self.userid,
                password=self.password,
                host="localhost",
                port="5432"
            )
            return conn
        except Exception as e:
            st.error(f"Error connecting to the database: {e}")
            return None

# Function to fetch user role
def fetch_user_role(conn):
    try:
        query = "SELECT ONLINE_RETAIL.get_current_user_roles();"
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the role name
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching user role: {e}")
        return None

# Login page function
def login_page():
    # Set page title and header
    st.title("Online Retail Store System")
    
    # Login form inputs
    st.subheader("Login")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    # LOGIN button
    if st.button("LOGIN"):
        if username and password:
            # Create a Security object with the provided credentials
            security_obj = Security(userid=username, password=password)
            
            # Validate credentials using the Security object method
            conn = security_obj.validateCredentials()
            
            if conn:
                # Fetch user role
                user_role = fetch_user_role(conn)
                if user_role:
                    # Update the Security object with the fetched role name
                    security_obj.role_name = user_role.lower()  # Normalize to lowercase for consistency
                    
                    # Store login state, role, and connection in session state
                    st.session_state["logged_in"] = True
                    st.session_state["user_role"] = security_obj.role_name
                    st.session_state["db_connection"] = conn  # Save connection for later use
                    
                    st.rerun()  # Refresh page to redirect to the appropriate screen
                else:
                    st.error("Unable to determine user role. Please contact support.")
            else:
                st.error("Failed to connect to the database. Check your credentials.")
        else:
            st.error("Please enter both username and password.")
