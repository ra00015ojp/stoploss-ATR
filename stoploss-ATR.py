import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import time

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="ATR Trailing Stop Calculator",
    page_icon="📈",
    layout="wide"
)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_ticker_data(ticker, period='6mo'):
    """Fetch and cache ticker data to avoid rate limiting."""
    try:
        time.sleep(0.5)  # Small delay between requests
        # Set user agent to avoid some rate limiting
        yf.pdr_override()
        data = yf.download(ticker, period=period, progress=False, show_errors=False, 
                          headers={'User-Agent': 'Mozilla/5.0'})
        return data
    except Exception as e:
        st.warning(f"Could not fetch {ticker}: {str(e)}")
        return pd.DataFrame()

def calculate_atr_trailing_stop(ticker, multiplier, period):
    """Calculate ATR-based trailing stop loss for a given ticker."""
    try:
        data = fetch_ticker_data(ticker, period='6mo')
        
        if data.empty:
            return None
        
        # Calculate ATR
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period, min_periods=1).mean()
        
        # Current values
        current_price = float(data['Close'].iloc[-1])
        current_atr = float(atr.iloc[-1])
        stop_loss = current_price - (multiplier * current_atr)
        
        return {
            'Current Price': current_price,
            f'Current ATR ({period}-day)': current_atr,
            'Suggested Trailing Stop': stop_loss,
            'Percentage Below Current': ((current_price - stop_loss) / current_price) * 100
        }
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

# Title and description
st.title("📈 ATR Trailing Stop Loss Calculator")
st.markdown("""
This app calculates ATR (Average True Range) based trailing stop losses for your portfolio.
Customize the parameters and tickers below to analyze your positions.
""")

# Sidebar for parameters
st.sidebar.header("Parameters")
multiplier = st.sidebar.slider("ATR Multiplier", min_value=1.0, max_value=10.0, value=4.0, step=0.5)
period = st.sidebar.slider("ATR Period (days)", min_value=7, max_value=100, value=28, step=1)

# Default tickers
default_tickers = [
    ('SGLN.L', 'Physical Gold ETF'),
    ('IWRD.L', 'iShares World ETF'),
    ('VWRL.L', 'Vanguard World ETF'),
    ('IUKD.L', 'UKD ETF'),
    ('BCOG.L', 'Commodities ETF')
]

st.sidebar.header("Manage Tickers")

# Initialize session state for tickers
if 'tickers' not in st.session_state:
    st.session_state.tickers = default_tickers.copy()

# Add new ticker
with st.sidebar.expander("Add New Ticker"):
    new_ticker = st.text_input("Ticker Symbol", key="new_ticker")
    new_description = st.text_input("Description", key="new_desc")
    if st.button("Add Ticker"):
        if new_ticker and new_description:
            st.session_state.tickers.append((new_ticker.upper(), new_description))
            st.success(f"Added {new_ticker}")
            st.rerun()

# Display and manage current tickers
st.sidebar.subheader("Current Tickers")
tickers_to_remove = []
for i, (ticker, desc) in enumerate(st.session_state.tickers):
    col1, col2 = st.sidebar.columns([3, 1])
    col1.text(f"{ticker}: {desc}")
    if col2.button("❌", key=f"remove_{i}"):
        tickers_to_remove.append(i)

# Remove tickers
for i in sorted(tickers_to_remove, reverse=True):
    st.session_state.tickers.pop(i)
    st.rerun()

if st.sidebar.button("Reset to Defaults"):
    st.session_state.tickers = default_tickers.copy()
    st.rerun()

# Main content
st.header("Analysis Results")

if st.button("🔄 Calculate ATR Trailing Stops", type="primary"):
    with st.spinner("Fetching data and calculating..."):
        results = []
        progress_bar = st.progress(0)
        
        for idx, (ticker, description) in enumerate(st.session_state.tickers):
            result = calculate_atr_trailing_stop(ticker, multiplier, period)
            if result is not None:
                result['Asset'] = description
                result['Ticker'] = ticker
                results.append(result)
            progress_bar.progress((idx + 1) / len(st.session_state.tickers))
            time.sleep(0.3)  # Add delay between tickers
        
        progress_bar.empty()
        
        if results:
            # Create DataFrame
            df = pd.DataFrame(results)
            df.set_index('Asset', inplace=True)
            
            # Reorder columns
            columns = ['Ticker', 'Current Price', f'Current ATR ({period}-day)', 
                      'Suggested Trailing Stop', 'Percentage Below Current']
            df = df[columns]
            
            # Round numerical values
            df = df.round(2)
            
            # Display results
            st.success(f"Analysis complete! Analyzed {len(results)} assets.")
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Assets", len(results))
            with col2:
                avg_stop = df['Percentage Below Current'].mean()
                st.metric("Avg Stop Distance", f"{avg_stop:.2f}%")
            with col3:
                st.metric("ATR Period", f"{period} days")
            
            st.subheader("Detailed Results")
            st.dataframe(df, use_container_width=True)
            
            # Download button
            run_date = datetime.now().strftime('%Y-%m-%d')
            csv = df.to_csv()
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f'stock_atr_analysis_{run_date}.csv',
                mime='text/csv'
            )
            
            # Visualization
            st.subheader("Stop Loss Distances")
            st.bar_chart(df['Percentage Below Current'])
            
        else:
            st.error("No data could be retrieved. Please check your ticker symbols.")

# Footer
st.markdown("---")
st.markdown("""
**How it works:** This calculator uses the Average True Range (ATR) indicator to determine 
appropriate stop loss levels. The ATR measures market volatility, and multiplying it by a factor 
(default 4x) gives you a trailing stop that adapts to market conditions.
""")
