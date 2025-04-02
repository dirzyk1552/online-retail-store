import streamlit as st
import pandas as pd
from PIL import Image
import io

# Define the UIController class
class UIController:
    def __init__(self, conn):
        self.conn = conn

    def fetch_cart_details(self):
        """
        Fetches details from the cart.
        Returns:
            pd.DataFrame: DataFrame containing cart details.
        """
        try:
            query = "SELECT product_name, quantity, product_price FROM ONLINE_RETAIL.cart_info;"
            df = pd.read_sql_query(query, self.conn)
            return df
        except Exception as e:
            st.error(f"Error fetching cart details: {e}")
            return None

    def fetch_available_products(self):
        """
        Fetches available products with quantity > 0.
        Returns:
            pd.DataFrame: DataFrame containing available products.
        """
        try:
            query = """
            SELECT p.product_id, p.product_type, p.product_name, p.product_desc, p.product_keywords,
                   p.product_image, p.product_price
            FROM ONLINE_RETAIL.product_info p
            JOIN ONLINE_RETAIL.inventory_info i
            ON p.product_id = i.product_id
            WHERE i.product_quantity > 0;
            """
            df = pd.read_sql_query(query, self.conn)
            return df
        except Exception as e:
            st.error(f"Error fetching available products: {e}")
            return None

# Function to get the current user from the database
def get_current_user(conn):
    try:
        query = "SELECT CURRENT_USER;"
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            return result[0]  # Return the current user
        else:
            st.error("Unable to fetch current user.")
            return None
    except Exception as e:
        st.error(f"Error fetching current user: {e}")
        return None

# Function to insert selected items into the cart_info_stg table
def add_to_cart(conn, cart_items, user_id):
    try:
        cursor = conn.cursor()
        # Insert each item into the cart_info_stg table
        for item in cart_items:
            query = """
            INSERT INTO ONLINE_RETAIL.cart_info_stg (user_id, product_id, product_name, quantity, product_price)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, (user_id, item["product_id"], item["product_name"], item["quantity"], item["product_price"]))
        
        # Call the merge_and_truncate_cart_info() function
        merge_query = "SELECT ONLINE_RETAIL.merge_and_truncate_cart_info();"
        cursor.execute(merge_query)
        
        conn.commit()  # Commit the transaction
        st.success("Items added to the cart successfully!")
        
        # Trigger a rerun to refresh the cart details
        st.rerun()
    except Exception as e:
        conn.rollback()  # Rollback in case of an error
        st.error(f"Error adding items to the cart: {e}")

# Function to display products in a shopping experience format with selection and quantity input
def display_products_with_cart(products_df):
    st.subheader("Available Products")
    
    # List to store selected items and their quantities
    cart_items = []
    
    # Loop through each product and display its details
    for index, row in products_df.iterrows():
        with st.container():
            # Handle binary image data (if product_image is binary)
            if isinstance(row["product_image"], memoryview):
                try:
                    # Convert memoryview to bytes and then load it as an image
                    image_bytes = row["product_image"].tobytes()
                    image = Image.open(io.BytesIO(image_bytes))
                    st.image(image, width=200)  # Display the image with a fixed width
                except Exception as e:
                    st.error(f"Error displaying image for product {row['product_name']}: {e}")
            elif isinstance(row["product_image"], str):  # If it's a URL or path
                st.image(row["product_image"], width=200)

            # Display product details
            st.write(f"**Product Name:** {row['product_name']}")
            st.write(f"**Description:** {row['product_desc']}")
            st.write(f"**Price:** ${row['product_price']:.2f}")
            st.write(f"**Type:** {row['product_type']}")

            # Add checkbox for selection and input for quantity
            selected = st.checkbox(f"Select {row['product_name']}", key=f"select_{row['product_id']}")
            if selected:
                quantity = st.number_input(
                    f"Quantity for {row['product_name']}", min_value=1, max_value=100, value=1,
                    key=f"quantity_{row['product_id']}"
                )
                # Add selected item and quantity to the cart_items list
                cart_items.append({
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "quantity": quantity,
                    "product_price": row["product_price"]
                })
            
            st.write("---")  # Add a horizontal line between products
    
    return cart_items

# Customer screen function
def customer_screen():
    # Display header for Customer Screen
    st.title("Cart Details")
    
    # Retrieve connection from session state
    conn = st.session_state.get("db_connection")  # Do not close this connection during reruns
    
    if conn:
        try:
            # Initialize UIController with the database connection
            ui_controller = UIController(conn)
            
            # Fetch current user ID from the database
            user_id = get_current_user(conn)
            if not user_id:
                return  # Stop execution if user ID cannot be fetched
            
            # Fetch and display cart details using UIController method
            cart_details = ui_controller.fetch_cart_details()
            if cart_details is not None:
                st.subheader("Cart Details")
                st.dataframe(cart_details)
            
            # Fetch available products using UIController method
            available_products = ui_controller.fetch_available_products()
            if available_products is not None:
                # Add dropdown filter for product types
                product_types = available_products["product_type"].dropna().unique()  # Get distinct product types
                selected_type = st.selectbox("Filter by Product Type", options=["All"] + list(product_types))
                
                # Filter products based on the selected type
                if selected_type != "All":
                    filtered_products = available_products[available_products["product_type"] == selected_type]
                else:
                    filtered_products = available_products
                
                # Display filtered products with selection and quantity input for cart functionality
                cart_items = display_products_with_cart(filtered_products)
                
                # Add "Add to Cart" button
                if len(cart_items) > 0 and st.button("Add to Cart"):
                    add_to_cart(conn, cart_items, user_id)
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Database connection not found. Please log in again.")
    
    # Logout button
    if st.button("Logout"):
        del st.session_state["logged_in"]  # Clear login state
        del st.session_state["db_connection"]  # Clear database connection from session state
        st.rerun()  # Redirect back to Login Screen

