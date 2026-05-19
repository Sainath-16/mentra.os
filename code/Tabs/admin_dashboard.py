import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


def app():
    st.title("📊 Admin Dashboard – Stress Analytics")
    st.caption("System-wide monitoring and analysis (MENTRA)")

    # ================= DATABASE =================
    conn = sqlite3.connect("database/mentra.db")
    cursor = conn.cursor()

    total_users = cursor.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    total_predictions = cursor.execute(
        "SELECT COUNT(*) FROM predictions"
    ).fetchone()[0]

    high_stress = cursor.execute(
        "SELECT COUNT(*) FROM predictions WHERE stress_level='High Stress'"
    ).fetchone()[0]

    conn.close()

    # ================= METRIC CARDS =================
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("👥 Total Users", total_users)

    with c2:
        st.metric("🧠 Total Predictions", total_predictions)

    with c3:
        st.metric("🔴 High Stress Cases", high_stress)

    st.divider()

    # ================= LOAD FULL DATA =================
    conn = sqlite3.connect("database/mentra.db")
    df = pd.read_sql_query(
        """
        SELECT u.username, p.stress_level, p.confidence, p.timestamp
        FROM predictions p
        JOIN users u ON u.id = p.user_id
        ORDER BY p.timestamp DESC
        """,
        conn
    )
    conn.close()

    if df.empty:
        st.info("No predictions available yet.")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 🔁 Rename column ONLY for display
    df = df.rename(columns={
        "confidence": "Prediction Probability (Model Confidence)"
    })

    # ================= FILTERS =================
    st.subheader("🔍 Filters")

    col1, col2 = st.columns(2)

    with col1:
        stress_filter = st.multiselect(
            "Filter by Stress Level",
            options=df["stress_level"].unique(),
            default=list(df["stress_level"].unique())
        )

    with col2:
        date_range = st.date_input(
            "Filter by Date Range",
            value=(df["timestamp"].min().date(), df["timestamp"].max().date())
        )

    filtered_df = df[
        (df["stress_level"].isin(stress_filter)) &
        (df["timestamp"].dt.date >= date_range[0]) &
        (df["timestamp"].dt.date <= date_range[1])
    ]

    st.divider()

    # ================= STRESS DISTRIBUTION =================
    st.subheader("📊 Stress Distribution")

    if not filtered_df.empty:
        st.bar_chart(filtered_df["stress_level"].value_counts())

    # ================= REPEATED HIGH STRESS USERS =================
    st.subheader("🚨 Users with Repeated High Stress")

    high_stress_users = (
        df[df["stress_level"] == "High Stress"]
        .groupby("username")
        .size()
        .reset_index(name="High Stress Count")
        .query("`High Stress Count` >= 2")
        .sort_values("High Stress Count", ascending=False)
    )

    if high_stress_users.empty:
        st.success("No users with repeated high stress detected.")
    else:
        st.warning("These users may require immediate attention.")
        st.dataframe(high_stress_users, use_container_width=True)

    st.divider()

    # ================= RECENT PREDICTIONS =================
    st.subheader("🕒 Recent Stress Predictions")

    st.dataframe(
        filtered_df.head(10),
        use_container_width=True
    )

    st.divider()

    # ================= FULL TABLE =================
    st.subheader("📈 All Stress Prediction Records")

    st.dataframe(filtered_df, use_container_width=True)

    # ================= PDF EXPORT =================
    st.divider()
    st.subheader("📄 Export Admin Report")

    if st.button("⬇️ Download PDF Report"):
        file_name = "MENTRA_Admin_Report.pdf"

        doc = SimpleDocTemplate(file_name, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(
            Paragraph("<b>MENTRA – Admin Stress Report</b>", styles["Title"])
        )

        elements.append(
            Paragraph(
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"Total Users: {total_users} | "
                f"Total Predictions: {total_predictions} | "
                f"High Stress Cases: {high_stress}",
                styles["Normal"]
            )
        )

        table_data = [
            filtered_df.columns.tolist()
        ] + filtered_df.astype(str).values.tolist()

        elements.append(Table(table_data))
        doc.build(elements)

        with open(file_name, "rb") as f:
            st.download_button(
                label="📥 Download MENTRA Admin Report",
                data=f,
                file_name=file_name,
                mime="application/pdf"
            )
