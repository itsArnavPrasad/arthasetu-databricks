import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import warnings

def predict_prices():
    warnings.filterwarnings('ignore')
    file_path = "raw_data/seasonalPrice/Season_Price_Arrival_5_years.csv"
    
    print(f"Loading data from {file_path}...\n")
    df = pd.read_csv(file_path)
    
    # Create a mapping for Year string to a time index
    # E.g., '2021-22' -> 1, '2022-23' -> 2, ..., '2025-26' -> 5
    unique_years = sorted(df['Year'].unique())
    year_map = {y: i+1 for i, y in enumerate(unique_years)}
    df['Time_Index'] = df['Year'].map(year_map)
    
    # We want to predict for 2026-27
    target_year_str = "2026-27"
    target_time_index = len(unique_years) + 1
    
    prediction_records = []
    
    # Process each commodity
    commodities = sorted(df['Commodity'].unique())
    
    for commodity in commodities:
        comp_df = df[df['Commodity'] == commodity].sort_values("Time_Index")
        
        # --- KHARIF PRED ---
        kharif_df = comp_df.dropna(subset=['Kharif_Season_Price_Rs_Per_Quintal'])
        kharif_pred = np.nan
        kharif_trend = ""
        kharif_last = np.nan
        if len(kharif_df) >= 2:
            X = kharif_df[['Time_Index']].values
            y = kharif_df['Kharif_Season_Price_Rs_Per_Quintal'].values
            
            lr = LinearRegression()
            lr.fit(X, y)
            kharif_pred = lr.predict([[target_time_index]])[0]
            if kharif_pred < 0: kharif_pred = 0
            
            slope = lr.coef_[0]
            kharif_trend = "(+)" if slope > 0 else ("(-)" if slope < 0 else "(Flat)")
            kharif_last = y[-1]
            
        # --- RABI PRED ---
        rabi_df = comp_df.dropna(subset=['Rabi_Season_Price_Rs_Per_Quintal'])
        rabi_pred = np.nan
        rabi_trend = ""
        rabi_last = np.nan
        if len(rabi_df) >= 2:
            X = rabi_df[['Time_Index']].values
            y = rabi_df['Rabi_Season_Price_Rs_Per_Quintal'].values
            
            lr = LinearRegression()
            lr.fit(X, y)
            rabi_pred = lr.predict([[target_time_index]])[0]
            if rabi_pred < 0: rabi_pred = 0
                
            slope = lr.coef_[0]
            rabi_trend = "(+)" if slope > 0 else ("(-)" if slope < 0 else "(Flat)")
            rabi_last = y[-1]
            
        # Only add if it has at least one prediction
        if pd.notna(kharif_pred) or pd.notna(rabi_pred):
            prediction_records.append({
                "Commodity": commodity,
                "Kharif_2025_26": kharif_last,
                "Kharif_Pred_2026_27": kharif_pred,
                "K_Trend": kharif_trend,
                "Rabi_2025_26": rabi_last,
                "Rabi_Pred_2026_27": rabi_pred,
                "R_Trend": rabi_trend
            })
            
    # Display results
    print(f"==========================================================================================")
    print(f" CROP MARKET PRICE FORECAST FOR {target_year_str} (in Rs. Per Quintal)")
    print(f"==========================================================================================")
    print(f"{'Commodity':<30} | {'Kharif Pred (Trend)':<25} | {'Rabi Pred (Trend)':<25}")
    print("-" * 88)
    
    for rec in prediction_records:
        comm = rec["Commodity"]
        
        # Formatting Kharif
        if pd.notna(rec["Kharif_Pred_2026_27"]):
            k_str = f"{rec['Kharif_Pred_2026_27']:.2f} {rec['K_Trend']}"
        else:
            k_str = "N/A"
            
        # Formatting Rabi
        if pd.notna(rec["Rabi_Pred_2026_27"]):
            r_str = f"{rec['Rabi_Pred_2026_27']:.2f} {rec['R_Trend']}"
        else:
            r_str = "N/A"
            
        print(f"{comm:<30} | {k_str:<25} | {r_str:<25}")
        
    print("-" * 88)
    print("N/A implies the crop is not grown/tracked during that specific season.")

if __name__ == "__main__":
    predict_prices()
