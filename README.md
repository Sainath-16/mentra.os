# Mentra.os
MENTRA.OS is an intelligent, full-stack web platform designed to shift student mental health management from a delayed, reactive process into a proactive daily routine. By utilizing "cognitive telemetry," the platform continuously tracks and analyzes a user's psychological, physiological, and academic inputs to forecast their cognitive load before burnout occurs.
Built on a highly scalable, decoupled architecture, the system pairs a responsive Next.js frontend with a robust Python (FastAPI) backend. At its core, Mentra relies on a Scikit-learn Random Forest classification algorithm to predict stress levels (Low, Moderate, High) across 20 engineered features, achieving an overall accuracy of 88.6% with heavily optimized recall for critical stress states.
To solve the issue of AI mistrust, the platform completely eliminates "black-box" predictions by integrating Explainable AI (SHAP). Instead of just delivering a raw stress score, Mentra transparently reveals the specific lifestyle factors—such as sleep quality or study load—driving the prediction, providing users with actionable, personalized insights. Complete with secure JWT authentication, longitudinal data tracking via SQLite, and automated PDF wellness reporting, MENTRA.OS is a comprehensive tool for modern, data-driven mental wellness.

Frontend: Next.js, React, HTML5, CSS3
Backend: Python, FastAPI
Machine Learning: Scikit-learn (Random Forest), SHAP (Explainable AI), Pandas, NumPy
Database & Security: SQLite, JWT (JSON Web Tokens), Password Hashing
Tools: ReportLab (PDF Generation)
