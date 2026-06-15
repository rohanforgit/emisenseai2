import os
import streamlit as st

def select_ai_settings():
    """
    Renders Groq config sidebar interface in Streamlit and returns (api_key, model_name).
    Takes the Groq API key solely as input from the user (ignoring the .env file / environment).
    """
    st.sidebar.subheader("🤖 Groq AI Config")
    
    # Predefined popular Groq model options
    models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    
    # Retrieve default model name if defined in environment or .env
    default_model = os.environ.get("GROQ_MODEL")
    if not default_model and os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line:
                        k, v = line.strip().split("=", 1)
                        if k.strip() in ["GROQ_MODEL", "GROQ_MODEL_NAME"]:
                            default_model = v.strip().strip('"').strip("'")
                            break
        except Exception:
            pass
            
    if not default_model:
        default_model = "llama-3.3-70b-versatile"
        
    if default_model not in models:
        models.insert(0, default_model)
        
    selected_model = st.sidebar.selectbox("AI Model", models, index=models.index(default_model))
    
    # Prompt the user for the Groq API key. Ignore any key in .env/environment.
    api_key_input = st.sidebar.text_input(
        "Groq API Key",
        value="",
        type="password",
        help="Enter your Groq API Key (starts with gsk_). Leave blank for rule-based local advisor."
    )
    
    return api_key_input, selected_model
