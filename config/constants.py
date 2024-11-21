import pandas as pd

# Custom color scheme
COLORS = {
    "primary": "#6B46C1",
    "background": "#F3F4F6",
    "text": "#1F2937",
    "border": "#E5E7EB",
}

CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #F3F4F6;
    }
    
    .sector-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        transition: all 0.2s ease-in-out;
    }
    
    .sector-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .upload-button {
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding-left: 2rem;
        padding-right: 2rem;
    }
</style>
"""
