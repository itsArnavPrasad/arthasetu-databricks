import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, confusion_matrix, roc_auc_score, roc_curve)
from sklearn.preprocessing import LabelBinarizer
import xgboost as xgb
import warnings
import os
import json

def create_pipeline():
    warnings.filterwarnings('ignore')
    
    # =========================================================
    # 1. READ DATA
    # =========================================================
    print("Reading datasets...")
    df = pd.read_csv("synthetic_transactions.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    loans = pd.read_csv("loan_data.csv")
    
    print(f"  Transactions: {len(df)} rows")
    print(f"  Loan records: {len(loans)} rows")
    
    # =========================================================
    # 2. BEHAVIORAL FEATURE ENGINEERING (existing)
    # =========================================================
    print("\nEngineering behavioral features...")
    
    user_agg = df.groupby("user_id").agg(
        total_transactions=('amount', 'count'),
        avg_transaction_amount=('amount', 'mean'),
        avg_balance=('balance', 'mean'),
        min_balance=('balance', 'min'),
        max_balance=('balance', 'max'),
        balance_std=('balance', 'std')
    ).fillna(0)
    
    is_credit = df['transaction_type'] == 'credit'
    is_debit = df['transaction_type'] == 'debit'
    
    df['is_small_credit'] = is_credit & (df['amount'] < 5000)
    df['is_large_debit'] = is_debit & (df['amount'] > 10000)
    
    cond_agg = df.groupby("user_id").agg(
        small_credit_count=('is_small_credit', 'sum'),
        large_debit_count=('is_large_debit', 'sum'),
        cash_count=('channel', lambda x: (x == 'cash').sum()),
        upi_count=('channel', lambda x: (x.str.contains('UPI', case=False, na=False)).sum()),
        label_user_type=('label_user_type', 'last')
    )
    
    cond_agg['cash_vs_upi_ratio'] = cond_agg['cash_count'] / cond_agg['upi_count'].replace(0, 1)
    cond_agg = cond_agg.drop(columns=['cash_count', 'upi_count'])
    
    df['year_month'] = df['date'].dt.to_period('M')
    monthly_inflow = df[is_credit].groupby(['user_id', 'year_month'])['amount'].sum().reset_index(name='m_inflow')
    monthly_outflow = df[is_debit].groupby(['user_id', 'year_month'])['amount'].sum().reset_index(name='m_outflow')
    monthly_txns = df.groupby(['user_id', 'year_month']).size().reset_index(name='m_txns')
    
    monthly = pd.merge(monthly_txns, monthly_inflow, on=['user_id', 'year_month'], how='left')
    monthly = pd.merge(monthly, monthly_outflow, on=['user_id', 'year_month'], how='left').fillna(0)
    
    monthly_agg = monthly.groupby('user_id').agg(
        monthly_inflow=('m_inflow', 'mean'),
        monthly_outflow=('m_outflow', 'mean'),
        inflow_variance=('m_inflow', 'var'),
        txn_frequency=('m_txns', 'mean')
    ).fillna(0)
    monthly_agg['inflow_outflow_ratio'] = monthly_agg['monthly_inflow'] / monthly_agg['monthly_outflow'].replace(0, 1)
    
    df_sorted = df.sort_values(['user_id', 'date'])
    df_sorted['credit_time'] = pd.NaT
    is_credit_sorted = df_sorted['transaction_type'] == 'credit'
    df_sorted.loc[is_credit_sorted, 'credit_time'] = df_sorted.loc[is_credit_sorted, 'date']
    df_sorted['last_credit_time'] = df_sorted.groupby('user_id')['credit_time'].ffill()
    
    df_debits = df_sorted[df_sorted['transaction_type'] == 'debit'].copy()
    df_debits['time_gap_hrs'] = (df_debits['date'] - df_debits['last_credit_time']).dt.total_seconds() / 3600.0
    gap_agg = df_debits.groupby('user_id').agg(credit_debit_time_gap=('time_gap_hrs', 'mean')).fillna(0)
    
    df_sorted['date_day'] = df_sorted['date'].dt.date
    daily_balance = df_sorted.drop_duplicates(subset=['user_id', 'date_day'], keep='last').copy()
    daily_balance['is_zero'] = daily_balance['balance'] < 1000
    daily_balance['island'] = (~daily_balance['is_zero']).groupby(daily_balance['user_id']).cumsum()
    island_counts = daily_balance[daily_balance['is_zero']].groupby(['user_id', 'island']).size()
    zero_agg = island_counts.groupby('user_id').max().rename('consecutive_zero_balance_days').to_frame() if len(island_counts) > 0 else pd.DataFrame(columns=['consecutive_zero_balance_days'])
    
    behavioral_features = user_agg.join(cond_agg).join(monthly_agg).join(gap_agg).join(zero_agg).fillna(0)
    
    # =========================================================
    # 3. DEBT FEATURE ENGINEERING (NEW)
    # =========================================================
    print("Engineering debt features...")
    
    loan_agg = loans.groupby("user_id").agg(
        total_loan_amount=('loan_amount', 'sum'),
        total_amount_repaid=('amount_repaid', 'sum'),
        total_outstanding=('outstanding_amount', 'sum'),
        missed_payment_count=('missed_payments', 'sum'),
        avg_days_past_due=('days_past_due', 'mean'),
        max_days_past_due=('days_past_due', 'max'),
        avg_interest_rate=('interest_rate', 'mean'),
        num_loans=('loan_id', 'count'),
        default_flag=('default_flag', 'max'),  # user-level: defaulted if any loan defaulted
    )
    
    # Merge behavioral + debt
    final_features = behavioral_features.join(loan_agg, how='left').fillna(0)
    
    # Derived debt features
    final_features['debt_to_income_ratio'] = final_features['total_loan_amount'] / final_features['monthly_inflow'].replace(0, 1) / 12
    final_features['repayment_ratio'] = final_features['total_amount_repaid'] / final_features['total_loan_amount'].replace(0, 1)
    final_features['outstanding_to_balance_ratio'] = final_features['total_outstanding'] / final_features['avg_balance'].replace(0, 1)
    
    # Debt growth rate: outstanding / (loan_amount - amount_repaid) as a proxy
    net_owed = final_features['total_loan_amount'] - final_features['total_amount_repaid']
    final_features['debt_growth_rate'] = (final_features['total_outstanding'] - net_owed) / net_owed.replace(0, 1)
    
    print(f"Feature engineering completed for {len(final_features)} users.")
    
    # =========================================================
    # 4. MODEL 1: BEHAVIORAL CLASSIFICATION (Random Forest)
    # =========================================================
    behavioral_cols = [
        "total_transactions", "txn_frequency", "avg_transaction_amount",
        "monthly_inflow", "monthly_outflow", "inflow_outflow_ratio", "inflow_variance",
        "avg_balance", "min_balance", "max_balance", "balance_std",
        "small_credit_count", "large_debit_count", "credit_debit_time_gap",
        "consecutive_zero_balance_days", "cash_vs_upi_ratio"
    ]
    
    X_behav = final_features[behavioral_cols]
    y_behav = final_features['label_user_type']
    
    X_b_train, X_b_test, y_b_train, y_b_test = train_test_split(
        X_behav, y_behav, test_size=0.2, stratify=y_behav, random_state=42)
    
    print("\n" + "="*55)
    print("  MODEL 1: BEHAVIORAL CLASSIFICATION (Random Forest)")
    print("="*55)
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    rf.fit(X_b_train, y_b_train)
    y_b_pred = rf.predict(X_b_test)
    
    acc = accuracy_score(y_b_test, y_b_pred)
    prec = precision_score(y_b_test, y_b_pred, average='weighted')
    rec = recall_score(y_b_test, y_b_pred, average='weighted')
    f1 = f1_score(y_b_test, y_b_pred, average='weighted')
    
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    
    print("\nConfusion Matrix:")
    labels = rf.classes_
    cm = confusion_matrix(y_b_test, y_b_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print(cm_df)
    
    print("\nFeature Importances (Behavioral):")
    rf_imp = sorted(zip(behavioral_cols, rf.feature_importances_), key=lambda x: x[1], reverse=True)
    for feat, imp in rf_imp:
        print(f"  {feat}: {imp:.4f}")
    
    # =========================================================
    # 5. MODEL 2: DEFAULT PREDICTION (XGBoost)
    # =========================================================
    default_cols = behavioral_cols + [
        "debt_to_income_ratio", "repayment_ratio", "missed_payment_count",
        "avg_days_past_due", "debt_growth_rate", "outstanding_to_balance_ratio",
        "total_loan_amount", "total_outstanding", "avg_interest_rate", "num_loans"
    ]
    
    X_def = final_features[default_cols]
    y_def = final_features['default_flag'].astype(int)
    
    X_d_train, X_d_test, y_d_train, y_d_test = train_test_split(
        X_def, y_def, test_size=0.2, stratify=y_def, random_state=42)
    
    print("\n" + "="*55)
    print("  MODEL 2: DEFAULT PREDICTION (XGBoost)")
    print("="*55)
    
    xgb_model = xgb.XGBClassifier(
        n_estimators=150, max_depth=6, learning_rate=0.1,
        scale_pos_weight=(len(y_d_train) - y_d_train.sum()) / max(1, y_d_train.sum()),
        random_state=42, eval_metric='logloss', use_label_encoder=False
    )
    xgb_model.fit(X_d_train, y_d_train)
    
    y_d_pred = xgb_model.predict(X_d_test)
    y_d_proba = xgb_model.predict_proba(X_d_test)[:, 1]
    
    d_acc = accuracy_score(y_d_test, y_d_pred)
    d_prec = precision_score(y_d_test, y_d_pred)
    d_rec = recall_score(y_d_test, y_d_pred)
    d_f1 = f1_score(y_d_test, y_d_pred)
    d_auc = roc_auc_score(y_d_test, y_d_proba)
    
    print(f"Accuracy:  {d_acc:.4f}")
    print(f"Precision: {d_prec:.4f}")
    print(f"Recall:    {d_rec:.4f}")
    print(f"F1-Score:  {d_f1:.4f}")
    print(f"ROC-AUC:   {d_auc:.4f}")
    
    print("\nConfusion Matrix (Default):")
    cm_d = confusion_matrix(y_d_test, y_d_pred)
    cm_d_df = pd.DataFrame(cm_d, index=["No Default", "Default"], columns=["Pred: No Default", "Pred: Default"])
    print(cm_d_df)
    
    print("\nFeature Importances (Default Prediction):")
    xgb_imp = sorted(zip(default_cols, xgb_model.feature_importances_), key=lambda x: x[1], reverse=True)
    for feat, imp in xgb_imp:
        print(f"  {feat}: {imp:.4f}")
    
    # =========================================================
    # 6. PER-USER OUTPUT: Classification + Default Risk + Tier
    # =========================================================
    print("\n" + "="*55)
    print("  PER-USER RISK ASSESSMENT")
    print("="*55)
    
    # Full predictions
    all_behav_pred = rf.predict(X_behav)
    all_default_proba = xgb_model.predict_proba(X_def)[:, 1]
    
    final_features['behavioral_class'] = all_behav_pred
    final_features['default_probability'] = all_default_proba
    
    def risk_tier(prob):
        if prob < 0.3:
            return "low_risk"
        elif prob < 0.6:
            return "medium_risk"
        else:
            return "high_risk"
    
    final_features['risk_tier'] = final_features['default_probability'].apply(risk_tier)
    
    # Print summary
    print("\nRisk Tier Distribution:")
    print(final_features['risk_tier'].value_counts().to_string())
    
    # =========================================================
    # 7. EXPLAINABILITY: Top 3 reasons for high-risk users
    # =========================================================
    print("\n" + "="*55)
    print("  EXPLAINABILITY: HIGH RISK USER ANALYSIS")
    print("="*55)
    
    imp_dict = dict(zip(default_cols, xgb_model.feature_importances_))
    pop_mean = X_def.mean()
    pop_std = X_def.std()
    
    high_risk_users = final_features[final_features['risk_tier'] == 'high_risk'].head(5)
    
    for uid, row in high_risk_users.iterrows():
        reasons = []
        for feat in default_cols:
            val = row[feat] if feat in row.index else X_def.loc[uid, feat]
            m = pop_mean[feat]
            s = pop_std[feat]
            z = (val - m) / s if s > 0 else 0
            score = abs(z) * imp_dict[feat]
            reasons.append({"feature": feat, "score": score, "val": val, "mean": m, "z": z})
        
        top_3 = sorted(reasons, key=lambda x: x["score"], reverse=True)[:3]
        
        print(f"\n{uid} | Class: {row['behavioral_class']} | Default Prob: {row['default_probability']:.3f} | Tier: {row['risk_tier']}")
        for idx, r in enumerate(top_3):
            direction = "Higher" if r['z'] > 0 else "Lower"
            print(f"  {idx+1}. {r['feature']:<30}: {r['val']:.2f}  ({direction} than avg {r['mean']:.2f})")
    
    # =========================================================
    # 8. SAVE OUTPUTS
    # =========================================================
    os.makedirs("output", exist_ok=True)
    
    # Save user-level results
    output_cols = ['label_user_type', 'behavioral_class', 'default_flag', 'default_probability', 'risk_tier',
                   'total_loan_amount', 'total_amount_repaid', 'total_outstanding', 'missed_payment_count',
                   'debt_to_income_ratio', 'repayment_ratio']
    final_features[output_cols].to_csv("output/user_risk_assessment.csv")
    
    # Save model evaluation metrics
    metrics = {
        "behavioral_classifier": {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1},
        "default_predictor": {"accuracy": d_acc, "precision": d_prec, "recall": d_rec, "f1": d_f1, "roc_auc": d_auc}
    }
    with open("output/evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Save feature importances
    pd.DataFrame(rf_imp, columns=["feature", "importance"]).to_csv("output/rf_feature_importance.csv", index=False)
    pd.DataFrame(xgb_imp, columns=["feature", "importance"]).to_csv("output/xgb_feature_importance.csv", index=False)
    
    print(f"\nAll outputs saved to output/ directory.")
    print("  - user_risk_assessment.csv")
    print("  - evaluation_metrics.json")
    print("  - rf_feature_importance.csv")
    print("  - xgb_feature_importance.csv")

if __name__ == "__main__":
    create_pipeline()
