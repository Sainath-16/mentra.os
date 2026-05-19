import streamlit as st

def app():

    # ================= HERO =================
    st.markdown(
    """
<div class="hero-card">
    <h1 class="hero-title">MENTRA 🧠</h1>
    <h3 class="hero-subtitle">AI-Driven Student Stress Assessment Platform</h3>
    <p class="hero-text">
        Supporting student mental well-being through
        <b>early stress detection</b> and
        <b>transparent, explainable AI insights</b>.
    </p>
</div>
""",
    unsafe_allow_html=True
)

    st.divider()

    # ================= AT A GLANCE =================
    st.markdown("## 📊 System Overview")

    g1, g2, g3, g4 = st.columns(4)

    def glance_card(title, value):
        st.markdown(
            f"""
            <div class="section-card" style="text-align:center;">
                <p style="font-size:14px; color:#64748b; margin-bottom:4px;">
                    {title}
                </p>
                <p style="font-size:22px; font-weight:600; color:#4f46e5;">
                    {value}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with g1:
        glance_card("Primary Users", "Students")

    with g2:
        glance_card("Stress Categories", "Low • Moderate • High")

    with g3:
        glance_card("Prediction Engine", "Machine Learning (Random Forest)")

    with g4:
        glance_card("Explainability Layer", "SHAP (XAI)")

    st.divider()

    # ================= ABOUT MENTRA =================
    st.markdown(
        """
        <div class="section-card">
            <h2>🌿 About MENTRA</h2>
            <p>
                <b>MENTRA</b> is an intelligent stress analysis system designed
                specifically for students. It evaluates multiple dimensions
                of student life including psychological, academic, social,
                and environmental factors.
            </p>
            <p>
                The goal of MENTRA is not only to predict stress levels, but also
                to help users <b>understand the reasons behind the prediction</b>,
                enabling awareness, early intervention, and informed support.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ================= FEATURES =================
    st.markdown("## ✨ Core Features")

    f1, f2, f3 = st.columns(3)

    with f1:
        st.markdown(
            """
            <div class="section-card feature-card">
                <h3>🧠 Intelligent Stress Prediction</h3>
                <p>
                    Uses a trained machine learning model to analyze
                    stress-related indicators and classify stress levels
                    accurately.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f2:
        st.markdown(
            """
            <div class="section-card feature-card">
                <h3>🔍 Explainable Predictions</h3>
                <p>
                    SHAP-based explanations clearly display
                    <b>which factors influenced the prediction</b>,
                    ensuring transparency and trust.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with f3:
        st.markdown(
            """
            <div class="section-card feature-card">
                <h3>🛡️ Role-Based Dashboards</h3>
                <p>
                    Separate dashboards for students and administrators
                    enable personalized insights, analytics, and monitoring
                    while maintaining data security.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ================= WORKFLOW =================
    st.markdown(
        """
        <div class="section-card">
            <h2>⚙️ How MENTRA Works</h2>
            <ol style="font-size:15px; line-height:1.7;">
                <li>Student completes an interactive stress assessment</li>
                <li>Inputs are processed by the trained AI model</li>
                <li>The system predicts the current stress level</li>
                <li>Explainable AI highlights dominant contributing factors</li>
                <li>Results are stored securely for trend analysis</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ================= CTA =================
    st.markdown(
        """
        <div class="section-card" style="text-align:center;">
            <h2>🚀 Get Started with MENTRA</h2>
            <p style="color:#475569;">
                Use the sidebar to assess stress levels, explore dashboards,
                analyze trends, and download detailed reports.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
