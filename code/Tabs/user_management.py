import streamlit as st
import sqlite3
import pandas as pd

def app():
    st.title("👥 User Management")

    conn = sqlite3.connect("database/mentra.db")
    cursor = conn.cursor()

    # Display ALL accounts (Admins and Users) in the table so the admin can see everyone
    users_df = pd.read_sql_query(
        "SELECT id, username, role, created_at FROM users",
        conn
    )

    st.dataframe(users_df, use_container_width=True)

    st.subheader("🗑️ Remove User")
    
    # --- SECURITY FIX: Filter to ONLY include regular users ---
    regular_users_df = users_df[users_df["role"] == "user"]
    user_ids = regular_users_df["id"].tolist()

    # Safety check: If there are no regular users, hide the delete tools
    if len(user_ids) == 0:
        st.info("There are currently no regular users to delete.")
    else:
        # The dropdown now ONLY contains IDs of regular users
        user_to_delete = st.selectbox("Select User ID", user_ids)

        if st.button("Delete User"):
            # 1. Delete their predictions first (Prevents ghost data!)
            cursor.execute("DELETE FROM predictions WHERE user_id = ?", (user_to_delete,))
            
            # 2. Delete the user account
            cursor.execute("DELETE FROM users WHERE id = ?", (user_to_delete,))
            
            conn.commit()
            st.success("User and all associated data deleted successfully.")
            st.rerun()

    conn.close()