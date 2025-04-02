import streamlit as st
import psycopg2
from PIL import Image
import io


# -------------------------
# Fetch all products + quantity
# -------------------------
def fetch_products(conn):
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                p.product_id,
                p.product_type,
                p.product_name,
                p.product_desc,
                p.product_price,
                p.product_image,
                i.product_quantity
            FROM 
                ONLINE_RETAIL.product_info p
            JOIN 
                ONLINE_RETAIL.inventory_info i
            ON 
                p.product_id = i.product_id
        """
        cursor.execute(query)
        return cursor.fetchall()

    except Exception as e:
        st.error(f"Error fetching products: {e}")
        conn.rollback()
        return []

# -------------------------
# Add new product
# -------------------------
def add_product(conn, product_type, prod_id, product_name, product_desc, product_keywords, product_price, product_quantity, product_image_file):
    try:
        cursor = conn.cursor()

        image_bytes = product_image_file.getvalue() if product_image_file else None

        # Insert into product_info
        cursor.execute("""
            INSERT INTO ONLINE_RETAIL.product_info 
            (product_id, product_type, product_name, product_desc, product_keywords, product_price, product_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING product_id;
        """, (prod_id, product_type, product_name, product_desc, product_keywords, product_price, psycopg2.Binary(image_bytes)))

        product_id = cursor.fetchone()[0]

        # Insert into inventory_info
        cursor.execute("""
            INSERT INTO ONLINE_RETAIL.inventory_info
            (product_id, product_quantity)
            VALUES (%s, %s)
        """, (product_id, product_quantity))

        conn.commit()

        # ✅ Success Message
        st.success(f"Product '{product_name}' added successfully!")
        st.info("Product added successfully!")  # ✅ Added confirmation message

    except Exception as e:
        st.error(f"Error adding new product: {e}")
        conn.rollback()

# -------------------------
# Update product details
# -------------------------
def update_product(conn, product_id, product_price, product_quantity, product_desc):
    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE ONLINE_RETAIL.product_info
            SET product_price = %s, product_desc = %s
            WHERE product_id = %s
        """, (product_price, product_desc, product_id))

        cursor.execute("""
            UPDATE ONLINE_RETAIL.inventory_info
            SET product_quantity = %s
            WHERE product_id = %s
        """, (product_quantity, product_id))

        conn.commit()
        st.success("Product updated successfully!")

    except Exception as e:
        st.error(f"Error updating product: {e}")
        conn.rollback()

# -------------------------
# Delete a product
# -------------------------
def delete_product(conn, product_id):
    try:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ONLINE_RETAIL.inventory_info WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM ONLINE_RETAIL.product_info WHERE product_id = %s", (product_id,))

        conn.commit()
        st.success("Product deleted successfully!")
        return True

    except Exception as e:
        st.error(f"Error deleting product: {e}")
        conn.rollback()
        return False

# -------------------------
# Retailer Portal Screen
# -------------------------
def retailer_screen():
    conn = st.session_state.get("db_connection")
    if not conn:
        st.error("Database connection not found. Please login again.")
        return

    st.title("Retailer Portal")

    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = None

    products = fetch_products(conn)

    actions = ["Add New Product"] + [f"{prod[2]} (ID: {prod[0]})" for prod in products]

    selected_action = st.selectbox("Select an Action or Product", actions)

    # ADD PRODUCT SCREEN
    if selected_action == "Add New Product":
        st.header("Add New Product")

        product_type = st.selectbox("Product Type", ["Furniture", "Shoes", "Bag"])
        product_name = st.text_input("Product Name")
        prod_id = st.text_input("Product Id")
        product_desc = st.text_area("Product Description")
        product_keywords = st.text_input("Product Keywords (comma-separated)")
        product_price = st.number_input("Product Price", min_value=0.0, step=0.01)
        product_quantity = st.number_input("Product Quantity", min_value=0, step=1)
        product_image_file = st.file_uploader("Upload Product Image", type=["jpg", "jpeg", "png"])


        
        
        if st.button("Add Product"):          
            if not product_name:
                st.error("Product Name is required.")
            else:
                try:
                    add_product(conn, product_type, prod_id, product_name, product_desc, product_keywords, product_price, product_quantity, product_image_file)
                    st.session_state.refresh = True
                except Exception as e:
                    st.error(f"Error in add_product: {e}")
            
    # EDIT / DELETE EXISTING PRODUCTS
    else:
        product_id = int(selected_action.split("(ID: ")[1].strip(")"))
        product = next((p for p in products if p[0] == product_id), None)

        if product:
            st.header(f"{product[2]}")

            if product[5]:
                try:
                    image = Image.open(io.BytesIO(product[5]))
                    st.image(image, width=300)
                except:
                    st.warning("Could not load product image.")
            else:
                st.warning("No image available.")

            st.markdown(f"**Product Type:** {product[1]}")
            st.markdown(f"**Product Description:** {product[3]}")
            st.markdown(f"**Product Price:** ${product[4]:.2f}")
            st.markdown(f"**Product Quantity:** {product[6]}")

            st.subheader("Edit Product Information")
            new_price = st.number_input("Update Price", value=float(product[4]), min_value=0.0, step=0.01, key=f"price_{product_id}")
            new_quantity = st.number_input("Update Quantity", value=int(product[6]), min_value=0, step=1, key=f"quantity_{product_id}")
            new_desc = st.text_area("Update Description", value=product[3], key=f"desc_{product_id}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Update Product"):
                    update_product(conn, product_id, new_price, new_quantity, new_desc)
                    st.session_state.refresh = True

            with col2:
                if st.session_state.confirm_delete != product_id:
                    if st.button("Delete Product"):
                        st.session_state.confirm_delete = product_id
                        st.warning("Click 'Confirm Delete' to confirm.")

                elif st.button("Confirm Delete"):
                    success = delete_product(conn, product_id)
                    if success:
                        st.session_state.confirm_delete = None
                        st.session_state.refresh = True

    # Force a refresh if we updated/deleted something
    if st.session_state.get("refresh", False):
        st.session_state.refresh = False
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        if hasattr(st, "experimental_rerun"):
            st.experimental_rerun()
        else:
            st.rerun()
