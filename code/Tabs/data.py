# Import necessary modules
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def app():
    st.title("MENTRA – Dataset Information")

    st.markdown(
        """
        This page provides an overview and visual analysis of the dataset used to train the
        **MENTRA Student Stress Prediction Model**.
        """
    )

    # ---------------- Load Dataset ----------------
    try:
        df = pd.read_csv("StressLevelDataset.csv")
    except FileNotFoundError:
        st.error("❌ StressLevelDataset.csv not found in project directory.")
        return

    # ---------------- Dataset Preview ----------------
    st.subheader("📄 Dataset Preview")
    with st.expander("View first 10 rows"):
        st.dataframe(df.head(10), use_container_width=True)

    # ---------------- Dataset Shape ----------------
    st.subheader("📊 Dataset Shape")
    col1, col2 = st.columns(2)
    col1.metric("Number of Rows", df.shape[0])
    col2.metric("Number of Columns", df.shape[1])

    # ---------------- Stress Level Distribution ----------------
    st.subheader("📈 Stress Level Distribution")
    stress_counts = df["stress_level"].value_counts().sort_index()
    st.bar_chart(stress_counts)

    # ---------------- Correlation Heatmap ----------------
    st.subheader("📊 Feature Correlation Heatmap")

    st.markdown(
        """
        The heatmap below visualizes the correlation between different features.
        Strong correlations indicate factors that may significantly influence
        student stress levels.
        """
    )

    corr = df.corr()

    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(
        corr,
        cmap="coolwarm",
        linewidths=0.5,
        ax=ax
    )
    st.pyplot(fig)

    # ---------------- Statistical Summary ----------------
    st.subheader("📌 Statistical Summary")
    with st.expander("View summary statistics"):
        st.dataframe(df.describe())

    # ---------------- Column Details ----------------
    st.subheader("🧾 Column Information")

    col_name, col_dtype, col_data = st.columns(3)

    with col_name:
        if st.checkbox("Show Column Names"):
            st.write(list(df.columns))

    with col_dtype:
        if st.checkbox("Show Data Types"):
            st.dataframe(df.dtypes.astype(str), use_container_width=True)

    with col_data:
        if st.checkbox("View Column Data"):
            selected_col = st.selectbox("Select Column", df.columns)
            st.dataframe(df[selected_col])

    # ---------------- Dataset Description ----------------
    st.subheader("ℹ️ About the Dataset")
    st.markdown(
        """
        - The dataset contains **psychological, academic, lifestyle, and environmental features**
        - Target variable: **stress_level**
        - Stress Levels:
            - **0 → Low Stress**  
            - **1 → Moderate Stress**  
            - **2 → High Stress**  
        - Used for training a **Random Forest Classifier**
        """
    )
 