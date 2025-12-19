import streamlit as st

st.title("🚀 Deployment Test")
st.write("If you see this, deployment works!")

# Test imports
try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    st.success("✅ All packages imported successfully!")
    
    # Quick test
    ticker = yf.Ticker("AAPL")
    info = ticker.info
    st.write(f"Test fetch: {info.get('shortName', 'N/A')}")
    
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    st.write("Check your requirements.txt")
