import os
import json
import logging
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import mlflow
import mlflow.sklearn
import mlflow.xgboost

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("train")

DATASET_URL = "https://raw.githubusercontent.com/pplonski/datasets-for-start/master/employee_attrition/HR-Employee-Attrition-All.csv"
LOCAL_FALLBACK = "HR-Employee-Attrition-All.csv"

def load_data():
    try:
        df = pd.read_csv(DATASET_URL)
        log.info(f"Loaded dataset from remote source: {DATASET_URL}")
    except Exception as e:
        log.warning(f"Remote fetch failed: {e}. Loading from local fallback.")
        if os.path.exists(LOCAL_FALLBACK):
            df = pd.read_csv(LOCAL_FALLBACK)
        else:
            raise FileNotFoundError("Dataset not found locally or remotely.")
    
    # Validation
    REQUIRED_COLUMNS = {"Attrition", "MonthlyIncome", "Age", "Department", "JobRole",
                         "OverTime", "YearsAtCompany", "YearsSinceLastPromotion"}
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df

def feature_engineering(df):
    df_fe = df.copy()
    
    # 1. Promotion Gap
    df_fe["Promotion_Gap"] = df_fe["YearsSinceLastPromotion"] / (df_fe["TotalWorkingYears"] + 1)
    
    # 2. Compensation Ratio
    df_fe["Compensation_Ratio"] = df_fe["MonthlyIncome"] / (df_fe["JobLevel"] * 1000)
    
    # 3. Tenure Group
    def tenure_group(y):
        if y <= 3:    return "Early Career"
        elif y <= 8:  return "Mid Career"
        elif y <= 15: return "Senior"
        else:         return "Veteran"
    df_fe["Tenure_Group"] = df_fe["YearsAtCompany"].apply(tenure_group)
    
    # 4. Engagement Index
    SAT_COLS = ["JobSatisfaction", "EnvironmentSatisfaction", "RelationshipSatisfaction", "WorkLifeBalance"]
    for col in SAT_COLS:
        df_fe[col + "_norm"] = (df_fe[col] - 1) / 3
    eng_norm_cols = [c + "_norm" for c in SAT_COLS]
    df_fe["Engagement_Index"] = df_fe[eng_norm_cols].mean(axis=1)
    df_fe.drop(columns=eng_norm_cols, inplace=True)
    
    # 5. Burnout Score
    travel_map = {"Non-Travel": 0, "Travel_Rarely": 1, "Travel_Frequently": 2}
    df_fe["Travel_Score"] = df_fe["BusinessTravel"].map(travel_map)
    ot_num = (df_fe["OverTime"] == "Yes").astype(int)
    df_fe["Burnout_Score"] = (
        0.4 * ot_num +
        0.3 * (df_fe["YearsInCurrentRole"] / (df_fe["YearsInCurrentRole"].max() + 1e-9)) +
        0.3 * (df_fe["Travel_Score"] / 2)
    )
    
    # 6. Flight Risk Score
    df_fe["Flight_Risk_Score"] = (
        0.30 * df_fe["Promotion_Gap"].clip(upper=1) +
        0.25 * (1 - df_fe["Engagement_Index"]) +
        0.25 * df_fe["Burnout_Score"] +
        0.20 * (1 - (df_fe["Compensation_Ratio"].clip(upper=2) / 2))
    ).round(4)
    
    return df_fe

def preprocess_and_train():
    df = load_data()
    df_fe = feature_engineering(df)
    
    df_model = df_fe.copy()
    df_model["Attrition"] = (df_model["Attrition"] == "Yes").astype(int)
    
    # Drop constant/id and intermediate columns
    df_model.drop(columns=["Attrition_Num","Education_Label","Age_Band","Travel_Score",
                            "Tenure_Group", "Flight_Risk_Score", "JobSatisfaction", 
                            "EnvironmentSatisfaction", "RelationshipSatisfaction", 
                            "WorkLifeBalance", "EmployeeCount", "StandardHours", 
                            "Over18", "EmployeeNumber"], errors="ignore", inplace=True)
    
    # Label encode binary features
    label_encoders = {}
    for col in ["Gender", "OverTime"]:
        le = LabelEncoder()
        df_model[col] = le.fit_transform(df_model[col])
        label_encoders[col] = le
        
    # One-hot encode remaining categoricals
    cat_cols = [c for c in df_model.select_dtypes(include="object").columns if c != "Attrition"]
    df_model = pd.get_dummies(df_model, columns=cat_cols, drop_first=True)
    
    X = df_model.drop(columns=["Attrition"])
    y = df_model["Attrition"]
    
    # Save encoders and column names map
    os.makedirs("models", exist_ok=True)
    encoders_info = {
        "features": X.columns.tolist(),
        "cat_cols": cat_cols,
        "binary_cols": ["Gender", "OverTime"]
    }
    with open("models/feature_schema.json", "w") as f:
        json.dump(encoders_info, f, indent=2)
        
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)
    
    # Handle Class Imbalance
    smote = SMOTE(random_state=42)
    X_tr_sm, y_tr_sm = smote.fit_resample(X_train_sc, y_train)
    
    # Configure MLflow tracking
    mlflow.set_tracking_uri("sqlite:///mlruns/mlflow.db")
    mlflow.set_experiment("Employee_Attrition_Intelligence")
    
    log.info("Starting MLflow Run...")
    with mlflow.start_run() as run:
        # Define the best model (XGBoost)
        model = XGBClassifier(
            random_state=42, 
            eval_metric="logloss",
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.7
        )
        
        # Train model
        model.fit(X_tr_sm, y_tr_sm)
        
        # Predict & Evaluate
        y_pred = model.predict(X_test_sc)
        y_proba = model.predict_proba(X_test_sc)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred)
        rec = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_proba)
        
        log.info(f"Model Results: ROC-AUC={roc_auc:.4f}, Recall={rec:.4f}, F1-Score={f1:.4f}")
        
        # Log params & metrics to MLflow
        mlflow.log_params(model.get_params())
        mlflow.log_param("test_size", 0.20)
        mlflow.log_param("smote", True)
        
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("precision", prec)
        mlflow.log_metric("recall", rec)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("roc_auc", roc_auc)
        
        # Log model & scaler artifacts locally
        joblib.dump(model, "models/attrition_best_model.joblib")
        joblib.dump(scaler, "models/feature_scaler.joblib")
        
        mlflow.xgboost.log_model(model, "attrition_best_model", registered_model_name="XGBoostAttritionModel")
        log.info("Model registered in MLflow.")
        
if __name__ == "__main__":
    preprocess_and_train()
