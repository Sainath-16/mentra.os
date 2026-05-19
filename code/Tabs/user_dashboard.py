import streamlit as st
import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
import tempfile
import os  # Added to safely check if the logo file exists
st.warning(f"Looking for logo at: {os.path.abspath('assets/mentra_logo.jpg')}")

def generate_pdf_report(username, records):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ==========================================
    # 1. LOGO (Safely loaded)
    # ==========================================
    logo_path = "assets/mentra_logo.jpg"
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            x=width / 2 - 1 * inch,
            y=height - 1.8 * inch,
            width=2 * inch,
            preserveAspectRatio=True,
            mask='auto'
        )
        y_start = height - 2.5 * inch
    else:
        y_start = height - 1.5 * inch

    # ==========================================
    # 2. HEADER & TITLE ("etc" polish)
    # ==========================================
    c.setFillColorRGB(0.31, 0.27, 0.90)  # MENTRA Indigo color
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, y_start, "MENTRA Stress Report")
    
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 11)
    c.drawCentredString(width / 2, y_start - 0.3 * inch, "Smarter insights, calmer minds.")

    # Meta info
    c.setFillColorRGB(0, 0, 0)  # Reset to black
    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, y_start - 1.0 * inch, f"User: {username}")
    c.drawString(1 * inch, y_start - 1.3 * inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ==========================================
    # 3. TABLE
    # ==========================================
    y = y_start - 2.0 * inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1 * inch, y, "Stress Level")
    c.drawString(3 * inch, y, "Prediction Probability (%)")
    c.drawString(5 * inch, y, "Date")

    # Table rows
    c.setFont("Helvetica", 10)
    y -= 0.3 * inch

    for stress, probability, date in records:
        if y < 1 * inch:
            c.showPage()
            y = height - 1 * inch
            c.setFont("Helvetica", 10)

        # Color-code the stress text
        if "Low" in stress:
            c.setFillColorRGB(0.08, 0.63, 0.29)  # Green
        elif "Moderate" in stress:
            c.setFillColorRGB(0.96, 0.62, 0.04)  # Orange
        else:
            c.setFillColorRGB(0.86, 0.15, 0.15)  # Red
            
        c.drawString(1 * inch, y, str(stress))
        
        # Reset to black for probability and date
        c.setFillColorRGB(0, 0, 0)
        c.drawString(3 * inch, y, f"{probability:.2f}")
        c.drawString(5 * inch, y, str(date))
        y -= 0.25 * inch

    # ==========================================
    # 4. FOOTER
    # ==========================================
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width / 2, 0.5 * inch, "MENTRA - Confidential Student Health Record")

    c.save()
    buffer.seek(0)
    return buffer


def generate_stress_trend_chart(records):
    df = pd.DataFrame(records, columns=["stress", "probability", "timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    stress_map = {
        "Low Stress": 1,
        "Moderate Stress": 2,
        "High Stress": 3
    }
    df["stress_value"] = df["stress"].map(stress_map)
    df = df.sort_values("timestamp")

    plt.figure(figsize=(6, 3))
    plt.plot(df["timestamp"], df["stress_value"], marker="o")
    plt.yticks([1, 2, 3], ["Low", "Moderate", "High"])
    plt.xlabel("Date")
    plt.ylabel("Stress Level")
    plt.title("Stress Trend Over Time")
    plt.grid(alpha=0.3)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    plt.tight_layout()
    plt.savefig(temp_file.name, dpi=200)
    plt.close()

    return temp_file.name


def app():
    st.title("📊 User Dashboard")

    username = st.session_state.username
    user_id = st.session_state.user_id

    st.markdown(f"""
    <div class="section-card">
        <h3>👋 Welcome, {username}</h3>
        <p>Here’s a summary of your stress activity.</p>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- DATABASE ----------------
    conn = sqlite3.connect("database/mentra.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT stress_level, confidence, timestamp
        FROM predictions
        WHERE user_id = ?
        ORDER BY timestamp DESC
    """, (user_id,))

    records = cursor.fetchall()
    conn.close()

    if records:
        latest_stress, latest_prob, latest_date = records[0]

        avg_probability = sum(r[1] for r in records) / len(records)
        total_predictions = len(records)

        stress_color = {
            "Low Stress": "#16a34a",
            "Moderate Stress": "#f59e0b",
            "High Stress": "#dc2626"
        }.get(latest_stress, "#4f46e5")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="section-card" style="border-left:6px solid {stress_color}">
                <h4>🧠 Current Stress</h4>
                <h2 style="color:{stress_color}; margin:0;">
                    {latest_stress}
                </h2>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="section-card">
                <h4>📅 Last Prediction</h4>
                <h2 style="margin:0;">
                    {latest_date.split(" ")[0]}
                </h2>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="section-card">
                <h4>📊 Avg Prediction Probability</h4>
                <h2 style="margin:0;">
                    {avg_probability:.1f}%
                </h2>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class="section-card">
                <h4>📈 Total Predictions</h4>
                <h2 style="margin:0;">
                    {total_predictions}
                </h2>
            </div>
            """, unsafe_allow_html=True)

        st.subheader("📋 Stress History")
        st.dataframe(
            {
                "Stress Level": [r[0] for r in records],
                "Prediction Probability (%)": [round(r[1], 2) for r in records],
                "Date": [r[2] for r in records]
            },
            use_container_width=True
        )

    else:
        st.info("You have not made any stress predictions yet.")

    st.divider()

    st.subheader("📄 Download Stress Report")
    pdf_buffer = generate_pdf_report(username, records)

    st.download_button(
        label="⬇️ Download PDF Report",
        data=pdf_buffer,
        file_name=f"MENTRA_Stress_Report_{username}.pdf",
        mime="application/pdf"
    )

    if st.button("🧠 Predict Stress Now", key="predict_btn"):
        st.session_state.page = "🧠 Stress Prediction"
        st.rerun()