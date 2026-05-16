import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import time

# 1. പേജ് സെറ്റപ്പ്
st.set_page_config(page_title="SwingPro Nifty 500", layout="wide")

# Nifty 500 ലിസ്റ്റ് ഉള്ള ഗൂഗിൾ ഷീറ്റ് (ഇത് തൽക്കാലം എൻ്റെ കൈയിലുള്ള ഒരു ലിങ്ക് ആണ്, നിങ്ങൾക്ക് മാറ്റാം)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSsnZ6oD_zaP3JLOVaAbR1ZTzn2TVQ26agPr_G89Iey669ijjuJnwgbiaJDtdBiF1ixVyZ0gtfTA1e8/pub?output=csv"

def get_cpr(df):
    prev_day = df.iloc[-2]
    pivot = (prev_day['High'] + prev_day['Low'] + prev_day['Close']) / 3
    bc = (prev_day['High'] + prev_day['Low']) / 2
    tc = (pivot - bc) + pivot
    return pivot, bc, tc

def analyze_stock(symbol):
    try:
        ticker = f"{symbol}.NS"
        # സമയം ലാഭിക്കാൻ കഴിഞ്ഞ 1 വർഷത്തെ ഡാറ്റ മാത്രം എടുക്കുന്നു
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if len(df) < 100: return None

        ltp = round(df['Close'].iloc[-1], 2)
        rsi = ta.rsi(df['Close'], length=14).iloc[-1]
        ema_200 = ta.ema(df['Close'], length=200).iloc[-1]
        
        # MACD
        macd_df = ta.macd(df['Close'])
        macd_line = macd_df['MACD_12_26_9'].iloc[-1]
        macd_sig = macd_df['MACDs_12_26_9'].iloc[-1]
        
        # CPR
        pivot, bc, tc = get_cpr(df)

        signal = "⚪ WAIT"
        reason = "Neutral"

        # സിഗ്നൽ ലോജിക്
        if ltp > ema_200 and rsi > 50 and macd_line > macd_sig:
            if ltp > tc:
                signal = "🟢 STRONG BUY"
                reason = "Bullish + Above CPR"
            else:
                signal = "🟡 WATCH"
                reason = "Above 200 EMA, Near CPR"
        elif ltp < ema_200:
            signal = "🔴 AVOID"
            reason = "Below 200 EMA"

        return {
            "Stock": symbol,
            "Signal": signal,
            "LTP": float(ltp),
            "RSI": round(float(rsi), 2),
            "Reason": reason
        }
    except:
        return None

# --- UI SECTION ---
st.markdown("<h1 style='text-align: center; color: #00C853;'>SwingPro Nifty 500 ⚡</h1>", unsafe_allow_html=True)

if st.button('🚀 Start Nifty 500 Full Scan'):
    try:
        sheet_df = pd.read_csv(URL)
        symbols = sheet_df['Symbol'].tolist()
        
        # Nifty 500 മുഴുവൻ സ്കാൻ ചെയ്യാൻ
        target_symbols = symbols[:500] 
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, s in enumerate(target_symbols):
            status_text.text(f"Scanning {i+1}/{len(target_symbols)}: {s}")
            status = analyze_stock(s)
            if status:
                results.append(status)
            progress_bar.progress((i + 1) / len(target_symbols))
        
        status_text.success("Scan Completed! ✅")
        
        if results:
            final_df = pd.DataFrame(results)
            
            # ഫിൽട്ടർ ഓപ്ഷൻ: STRONG BUY മാത്രം കാണാൻ
            st.subheader("📊 Bullish Opportunities")
            bullish_df = final_df[final_df['Signal'] == "🟢 STRONG BUY"]
            st.table(bullish_df)
            
            with st.expander("Show All Scanned Data"):
                st.dataframe(final_df)
    except Exception as e:
        st.error(f"Error: {e}")