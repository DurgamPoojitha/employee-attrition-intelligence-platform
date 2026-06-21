import os
import json
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

app = FastAPI(
    title="Workforce Attrition Intelligence API",
    description="Enterprise API for predicting employee attrition risk, estimating replacement costs, and generating custom retention plans.",
    version="1.0.0"
)

# Global variables for model artifacts
model = None
scaler = None
feature_schema = None

@app.on_event("startup")
def load_artifacts():
    global model, scaler, feature_schema
    model_path = "models/attrition_best_model.joblib"
    scaler_path = "models/feature_scaler.joblib"
    schema_path = "models/feature_schema.json"
    
    if not os.path.exists(model_path) or not os.path.exists(scaler_path) or not os.path.exists(schema_path):
        raise FileNotFoundError(
            "Model artifacts missing. Run train.py first to generate models/ directories."
        )
        
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    with open(schema_path, "r") as f:
        feature_schema = json.load(f)

# Pydantic schema for employee features with sensible default values
class EmployeeInput(BaseModel):
    Age: int = Field(36, ge=18, le=70)
    BusinessTravel: str = Field("Travel_Rarely", description="Options: Travel_Rarely, Travel_Frequently, Non-Travel")
    DailyRate: int = Field(800)
    Department: str = Field("Research & Development", description="Options: Research & Development, Sales, Human Resources")
    DistanceFromHome: int = Field(9)
    Education: int = Field(3, ge=1, le=5)
    EducationField: str = Field("Life Sciences")
    EnvironmentSatisfaction: int = Field(3, ge=1, le=4)
    Gender: str = Field("Male", description="Options: Male, Female")
    HourlyRate: int = Field(66)
    JobInvolvement: int = Field(3, ge=1, le=4)
    JobLevel: int = Field(2, ge=1, le=5)
    JobRole: str = Field("Research Scientist")
    JobSatisfaction: int = Field(3, ge=1, le=4)
    MaritalStatus: str = Field("Married", description="Options: Single, Married, Divorced")
    MonthlyIncome: int = Field(5000)
    MonthlyRate: int = Field(14000)
    NumCompaniesWorked: int = Field(2)
    OverTime: str = Field("No", description="Options: Yes, No")
    PercentSalaryHike: int = Field(15)
    PerformanceRating: int = Field(3, ge=1, le=4)
    RelationshipSatisfaction: int = Field(3, ge=1, le=4)
    StockOptionLevel: int = Field(1, ge=0, le=3)
    TotalWorkingYears: int = Field(10)
    TrainingTimesLastYear: int = Field(3)
    WorkLifeBalance: int = Field(3, ge=1, le=4)
    YearsAtCompany: int = Field(5)
    YearsInCurrentRole: int = Field(4)
    YearsSinceLastPromotion: int = Field(1)
    YearsWithCurrManager: int = Field(3)

def compute_retention_plan(features: Dict[str, Any], risk_score: float) -> List[Dict[str, str]]:
    recs = []
    overtime = str(features.get("OverTime", "No")).lower() == "yes"
    promo_gap = features.get("YearsSinceLastPromotion", 0)
    comp_ratio = features.get("MonthlyIncome", 5000) / (features.get("JobLevel", 2) * 1000)
    job_sat = features.get("JobSatisfaction", 3)
    env_sat = features.get("EnvironmentSatisfaction", 3)
    rel_sat = features.get("RelationshipSatisfaction", 3)
    wlb = features.get("WorkLifeBalance", 3)
    
    # Calculate Engagement Index
    eng_index = np.mean([(job_sat-1)/3, (env_sat-1)/3, (rel_sat-1)/3, (wlb-1)/3])
    
    if overtime:
        recs.append({
            "Action": "Workload Redistribution",
            "Detail": "Overtime cap + 1.5x comp-time. Review task allocation now.",
            "Priority": "HIGH",
            "Impact": "+12% retention probability"
        })
    if promo_gap >= 3:
        recs.append({
            "Action": "Promotion Review",
            "Detail": f"{promo_gap:.0f} years without promotion. Initiate career path conversation.",
            "Priority": "HIGH",
            "Impact": "+10% retention probability"
        })
    if comp_ratio < 1.0:
        recs.append({
            "Action": "Compensation Assessment",
            "Detail": f"Income ratio is {comp_ratio:.2f} (below peer median). Benchmark salary against target range.",
            "Priority": "HIGH",
            "Impact": "+15% retention probability"
        })
    if eng_index < 0.45:
        recs.append({
            "Action": "Engagement Programme",
            "Detail": "Low satisfaction composite. Assign peer buddy + professional development budget.",
            "Priority": "MEDIUM",
            "Impact": "+8% retention probability"
        })
    if features.get("BusinessTravel") == "Travel_Frequently":
        recs.append({
            "Action": "Travel Policy Review",
            "Detail": "Frequent business travel. Evaluate remote-first options to lower burnout.",
            "Priority": "MEDIUM",
            "Impact": "+6% retention probability"
        })
    if features.get("YearsAtCompany", 5) <= 2:
        recs.append({
            "Action": "Early Tenure Buddy Programme",
            "Detail": "Structured onboarding + peer buddy for employees in first 2 years.",
            "Priority": "MEDIUM",
            "Impact": "+7% retention probability"
        })
    if not recs:
        recs.append({
            "Action": "Routine Check-in",
            "Detail": "Low current risk. Maintain via standard 1-on-1 career pathing.",
            "Priority": "LOW",
            "Impact": "Maintain current retention"
        })
    return recs

def compute_replacement_cost(monthly_income: int, job_level: int, years_at_company: int) -> Dict[str, float]:
    annual = monthly_income * 12
    recruit_pct = 0.20 if job_level <= 2 else (0.35 if job_level <= 3 else 0.50)
    recruitment = annual * recruit_pct
    training = annual * 0.10
    ramp_months = min(3 + job_level, 6)
    productivity = monthly_income * ramp_months * 0.50
    knowledge = annual * min(years_at_company * 0.02, 0.20)
    
    total = recruitment + training + productivity + knowledge
    return {
        "RecruitmentCost": round(recruitment, 2),
        "TrainingCost": round(training, 2),
        "ProductivityLoss": round(productivity, 2),
        "KnowledgeDrainCost": round(knowledge, 2),
        "TotalReplacementCost": round(total, 2)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "features_count": len(feature_schema["features"]) if feature_schema else 0
    }

@app.post("/predict")
def predict(employee: EmployeeInput):
    if model is None or scaler is None or feature_schema is None:
        raise HTTPException(status_code=503, detail="Model pipeline is not loaded.")
        
    # Convert input to dictionary
    raw_data = employee.dict()
    df_raw = pd.DataFrame([raw_data])
    
    # Run Feature Engineering
    df_fe = df_raw.copy()
    df_fe["Promotion_Gap"] = df_fe["YearsSinceLastPromotion"] / (df_fe["TotalWorkingYears"] + 1)
    df_fe["Compensation_Ratio"] = df_fe["MonthlyIncome"] / (df_fe["JobLevel"] * 1000)
    
    # Calculate Engagement Index
    SAT_COLS = ["JobSatisfaction", "EnvironmentSatisfaction", "RelationshipSatisfaction", "WorkLifeBalance"]
    for col in SAT_COLS:
        df_fe[col + "_norm"] = (df_fe[col] - 1) / 3
    eng_norm_cols = [c + "_norm" for c in SAT_COLS]
    df_fe["Engagement_Index"] = df_fe[eng_norm_cols].mean(axis=1)
    df_fe.drop(columns=eng_norm_cols, inplace=True)
    
    # Burnout Score
    travel_map = {"Non-Travel": 0, "Travel_Rarely": 1, "Travel_Frequently": 2}
    df_fe["Travel_Score"] = df_fe["BusinessTravel"].map(travel_map)
    ot_num = (df_fe["OverTime"] == "Yes").astype(int)
    df_fe["Burnout_Score"] = (
        0.4 * ot_num +
        0.3 * (df_fe["YearsInCurrentRole"] / (df_fe["YearsInCurrentRole"].max() + 1e-9)) +
        0.3 * (df_fe["Travel_Score"] / 2)
    )
    
    # Drop constant/id and intermediate columns
    df_fe.drop(columns=["Attrition_Num","Education_Label","Age_Band","Travel_Score",
                        "Tenure_Group", "Flight_Risk_Score", "JobSatisfaction", 
                        "EnvironmentSatisfaction", "RelationshipSatisfaction", 
                        "WorkLifeBalance", "EmployeeCount", "StandardHours", 
                        "Over18", "EmployeeNumber"], errors="ignore", inplace=True)
    
    # Label encode binary categoricals (matching train mapping)
    df_fe["Gender"] = df_fe["Gender"].map({"Female": 0, "Male": 1}).fillna(1).astype(int)
    df_fe["OverTime"] = df_fe["OverTime"].map({"No": 0, "Yes": 1}).fillna(0).astype(int)
    
    # One-hot encode remaining categoricals
    cat_cols = feature_schema["cat_cols"]
    df_model = pd.get_dummies(df_fe, columns=cat_cols, drop_first=True)
    
    # Align features to match schema
    schema_features = feature_schema["features"]
    df_model = df_model.reindex(columns=schema_features, fill_value=0)
    
    # Scale features
    X_sc = scaler.transform(df_model)
    
    # Get model prediction probability
    risk_score_proba = float(model.predict_proba(X_sc)[0][1])
    risk_score_pct = round(risk_score_proba * 100, 2)
    
    # Map to risk category
    if risk_score_pct >= 75.0:
        risk_category = "Critical Risk"
    elif risk_score_pct >= 45.0:
        risk_category = "High Risk"
    elif risk_score_pct >= 25.0:
        risk_category = "Medium Risk"
    else:
        risk_category = "Low Risk"
        
    # Generate retention recommendations
    retention_plan = compute_retention_plan(raw_data, risk_score_pct)
    
    # Estimate financial impact
    costs = compute_replacement_cost(
        employee.MonthlyIncome, 
        employee.JobLevel, 
        employee.YearsAtCompany
    )
    
    return {
        "FlightRiskProbability": f"{risk_score_pct}%",
        "RiskCategory": risk_category,
        "EstimatedFinancialRisk": f"${costs['TotalReplacementCost']:,.2f}",
        "CostBreakdown": {
            "RecruitmentCost": f"${costs['RecruitmentCost']:,.2f}",
            "TrainingCost": f"${costs['TrainingCost']:,.2f}",
            "ProductivityLoss": f"${costs['ProductivityLoss']:,.2f}",
            "KnowledgeDrainCost": f"${costs['KnowledgeDrainCost']:,.2f}"
        },
        "RetentionPlan": retention_plan
    }
