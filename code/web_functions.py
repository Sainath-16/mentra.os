# Import necessary modules
import numpy as np
import pandas as pd
import pickle
import streamlit as st
import hashlib



# ---------------------------------------------------
# Load trained Random Forest model (from Colab)
# ---------------------------------------------------
@st.cache_resource
def load_model():
    with open("mentra_rf_model.pkl", "rb") as f:
        model = pickle.load(f)
    return model


# ---------------------------------------------------
# Load dataset (ONLY for visualization / heatmap)
# ---------------------------------------------------
@st.cache_data
def load_dataset():
    df = pd.read_csv("StressLevelDataset.csv")
    return df


# ---------------------------------------------------
# Predict stress level
# ---------------------------------------------------
def predict_stress(model, features):
    """
    features: list of input values in SAME ORDER
    used during model training
    """
    input_array = np.array(features).reshape(1, -1)
    prediction = model.predict(input_array)
    return prediction[0]
def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return hash_password(password) == hashed_password

