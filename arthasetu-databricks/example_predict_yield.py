import pandas as pd
import argparse
import os

def predict_district_yield(district_name):
    # Load predictions
    file_path = "output/predicted_2018_yields.csv"
    if not os.path.exists(file_path):
        print(f"Predictions not found at {file_path}. Please run train_yield_model.py first.")
        return
        
    df = pd.read_csv(file_path)
    
    # Filter for district case insensitively
    dist_df = df[df['Dist Name'].str.lower() == district_name.lower()]
    
    if dist_df.empty:
        print(f"No data available for district: '{district_name}'.")
        print("Please check spelling or verify if the district exists in the dataset.")
        return
        
    print(f"\n========================================================")
    print(f" EXPECTED 2018 CROP YIELDS FOR DISTRICT: {district_name.upper()}")
    print(f"========================================================")
    
    dist_df = dist_df.sort_values(by="Expected_2018_Yield", ascending=False)
    
    # Use standard python string formatting
    print(f"\n{'-'*65}")
    print(f"{'Crop':<25} | {'Hist. Avg (13-17)':<18} | {'Forecasted 2018 Yield':<20}")
    print(f"{'-'*65}")
    
    for _, row in dist_df.iterrows():
        crop = row['Crop']
        avg_yield = row['Historical_Avg_Yield_13_17']
        pred_2018 = row['Expected_2018_Yield']
        trend = row['Trend_Slope']
        
        # Format the trend safely
        if pd.isna(trend) or trend == 0:
            trend_str = " (Flat)"
        elif trend > 0:
            trend_str = " (+)"
        else:
            trend_str = " (-)"
            
        print(f"{crop:<25} | {avg_yield:<18.2f} | {pred_2018:.2f}{trend_str:<18}")
    
    print(f"{'-'*65}")
    print("\nNote: Yield values are in Kg per ha.")
    print("Trend indicates recent historical slope (+ for increasing, - for decreasing).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict upcoming crop yields for a stated district.")
    parser.add_argument("--district", required=True, type=str, help="Name of the district to predict.")
    args = parser.parse_args()
    
    predict_district_yield(args.district)
