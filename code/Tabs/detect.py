import streamlit as st
import numpy as np
import shap
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from web_functions import load_model, predict_stress

SHAP_CLASS_NAMES = ["Low Stress", "Moderate Stress", "High Stress"]

# =========================================================
# Label mappings
# =========================================================
STRESS_LABELS = {
    0: "🟢 Low Stress",
    1: "🟡 Moderate Stress",
    2: "🔴 High Stress"
}

# =========================================================
# TEXT-BASED SCALES
# =========================================================
NEGATIVE_SCALE = {
    "Not at all": 0,
    "Very Low": 1,
    "Low": 2,
    "Moderate": 3,
    "High": 4,
    "Very High": 5
}

POSITIVE_SCALE = {
    "Very Poor": 0,
    "Poor": 1,
    "Below Average": 2,
    "Average": 3,
    "Good": 4,
    "Excellent": 5
}

# =========================================================
# SHAP Reason Helper (UNCHANGED)
# =========================================================
def get_stress_reasons(shap_vals, feature_names, feature_values, top_k=3):
    shap_vals = shap_vals.reshape(-1)
    contributions = list(zip(feature_names, shap_vals, feature_values))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    reasons = []
    for name, shap_val, value in contributions:
        if shap_val > 0 and value >= 3:
            reasons.append(name)
        if len(reasons) == top_k:
            break
    return reasons

# =========================================================
# Styled Slider
# =========================================================
def styled_slider(label, scale, key):
    choice = st.select_slider(
        label,
        options=list(scale.keys()),
        value=list(scale.keys())[0],
        key=key
    )
    value = scale[choice]

    if value <= 1:
        indicator = "🟢 Very Low"
    elif value == 2:
        indicator = "🟡 Mild"
    elif value == 3:
        indicator = "🟠 Moderate"
    else:
        indicator = "🔴 High"

    st.caption(f"{indicator} — **{choice}**")
    return value

# =========================================================
# Positive Feature Fix (UNCHANGED)
# =========================================================
def reverse_scale(value):
    return 5 - value

# =========================================================
# MAIN APP
# =========================================================
def app():
    model = load_model()

    st.title("🧠 Student Stress Prediction")
    st.caption("Select the options that best describe your current condition.")

    # Psychological Factors
    st.markdown("### 🧩 Psychological Factors")
    anxiety = styled_slider("How often do you feel nervous or worried?", NEGATIVE_SCALE, "anxiety")
    esteem = styled_slider("How confident and positive do you feel about yourself?", POSITIVE_SCALE, "esteem")
    history = styled_slider("Do you have a past history of mental health difficulties?", NEGATIVE_SCALE, "history")
    depression = styled_slider("How often do you feel sad or lose interest in activities?", NEGATIVE_SCALE, "depression")
    headache = styled_slider("How frequently do you experience headaches?", NEGATIVE_SCALE, "headache")

    # Physical & Environmental
    st.markdown("### 🌍 Physical & Environmental Factors")
    sleep = styled_slider("How would you rate your sleep quality?", POSITIVE_SCALE, "sleep")
    noise = styled_slider("How noisy is your study or living environment?", NEGATIVE_SCALE, "noise")
    breath = styled_slider("Do you experience breathing difficulty under stress?", NEGATIVE_SCALE, "breath")
    living = styled_slider("How comfortable is your living environment?", POSITIVE_SCALE, "living")
    safety = styled_slider("How safe do you feel in your surroundings?", POSITIVE_SCALE, "safety")
    needs = styled_slider("How well are your basic needs met?", POSITIVE_SCALE, "needs")

    # Academic & Social
    st.markdown("### 📚 Academic & Social Factors")
    academic = styled_slider("How satisfied are you with your academic performance?", POSITIVE_SCALE, "academic")
    study = styled_slider("How heavy is your current study workload?", NEGATIVE_SCALE, "study")
    teacher = styled_slider("How would you rate your relationship with teachers?", POSITIVE_SCALE, "teacher")
    career = styled_slider("How stressed are you about your future career?", NEGATIVE_SCALE, "career")
    support = styled_slider("How much social support do you receive?", POSITIVE_SCALE, "support")
    peer = styled_slider("How much peer pressure do you experience?", NEGATIVE_SCALE, "peer")
    extra = styled_slider("How involved are you in extracurricular activities?", POSITIVE_SCALE, "extra")
    bully = styled_slider("Have you experienced bullying or harassment?", NEGATIVE_SCALE, "bully")

    # Feature Vector (UNCHANGED)
    features = [
        anxiety, reverse_scale(esteem), history, depression, headache,
        3,
        reverse_scale(sleep), breath, noise, reverse_scale(living),
        reverse_scale(safety), reverse_scale(needs),
        reverse_scale(academic), study, reverse_scale(teacher),
        career, reverse_scale(support), peer, reverse_scale(extra), bully
    ]

    feature_names = [
        "Anxiety Level", "Self Esteem", "Mental Health History", "Depression",
        "Headache", "Physical Stress Response", "Sleep Quality",
        "Breathing Difficulty", "Noise Level", "Living Conditions",
        "Safety Feeling", "Basic Needs Satisfaction",
        "Academic Performance", "Study Load", "Teacher–Student Relationship",
        "Future Career Concerns", "Social Support",
        "Peer Pressure", "Extracurricular Activities", "Bullying Experience"
    ]

    st.divider()

    if st.button("🔍 Predict Stress Level"):
        X = np.array(features).reshape(1, -1)
        prediction = predict_stress(model, features)
        stress_label = STRESS_LABELS[prediction]

        probs = model.predict_proba(X)[0] * 100
        dominant = SHAP_CLASS_NAMES[np.argmax(probs)]
        probability = np.max(probs)

        st.success(f"🎯 **Predicted Stress Level:** {stress_label}")
        st.success(f"🏆 **Dominant Class:** {dominant} ({probability:.2f}%)")

        # ---------------- SAVE TO DB (FIXES DASHBOARD) ----------------
        if "user_id" in st.session_state:
            conn = sqlite3.connect("database/mentra.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO predictions (user_id, stress_level, confidence, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (
                    st.session_state.user_id,
                    stress_label.replace("🟢 ", "").replace("🟡 ", "").replace("🔴 ", ""),
                    probability,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            conn.commit()
            conn.close()

        # ---------------- SHAP ----------------
        st.subheader("🧠 Explainable AI (SHAP)")
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        shap_vals_for_class = (
            shap_values[prediction]
            if isinstance(shap_values, list)
            else shap_values[:, :, prediction]
        )

        with st.expander("📊 SHAP Feature Importance"):
            hide_idx = feature_names.index("Physical Stress Response")
            keep_indices = [i for i in range(len(feature_names)) if i != hide_idx]

            fig, ax = plt.subplots(figsize=(8, 5))
            shap.summary_plot(
                shap_vals_for_class[:, keep_indices],
                X[:, keep_indices],
                feature_names=[feature_names[i] for i in keep_indices],
                plot_type="bar",
                show=False
            )
            st.pyplot(fig)

        # ---------------- NLP ----------------
        reasons = get_stress_reasons(shap_vals_for_class, feature_names, features)
        if reasons:
            st.info(f"🧠 **Explanation:** Stress mainly influenced by **{', '.join(reasons)}**.")
        else:
            st.info("🧠 **Explanation:** Stress influenced by multiple moderate factors.")
