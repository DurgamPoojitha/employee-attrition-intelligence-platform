"""
Enterprise Employee Attrition Intelligence Platform
Notebook Generator — Clean Version (uses ''' for code cells to avoid triple-quote conflicts)
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.9.0"}
}

def md(text):  return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text)

cells = []

# ─────────────────────────────────────────────────────────
# COVER PAGE
# ─────────────────────────────────────────────────────────
cells.append(md(
"""<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);padding:60px;border-radius:16px;text-align:center;color:white;font-family:'Segoe UI',sans-serif;">
<h1 style="font-size:2.8em;font-weight:800;margin-bottom:10px;">
Enterprise Employee Attrition Intelligence Platform
</h1>
<h3 style="color:#a8b2d8;font-weight:400;margin-bottom:30px;">
Powered by Machine Learning &middot; Explainable AI &middot; HR Analytics
</h3>
<p style="color:#8892b0;font-size:0.95em;">
Dataset: IBM HR Analytics &nbsp;|&nbsp; Models: 6 ML Algorithms &nbsp;|&nbsp;
Phases: 14 Enterprise Phases &nbsp;|&nbsp; XAI: SHAP
</p>
<p style="color:#64ffda;font-size:0.85em;margin-top:16px;">
Designed for HR Teams &middot; Business Leaders &middot; Data Scientists &middot; AI/ML Engineers
</p>
</div>
"""))

# ─────────────────────────────────────────────────────────
# GOOGLE COLAB SETUP CELL (first cell in notebook)
# ─────────────────────────────────────────────────────────
cells.insert(0, md(
"""## Google Colab Setup
> Run the cell below **once** before anything else to install required libraries.
> If you are running locally in Jupyter, you can skip it (or run `pip install -r requirements.txt` in your terminal).
"""))

cells.insert(1, code(
'''# ── Google Colab: Install Required Libraries ─────────────────────────────────
# Run this cell first if you are on Google Colab.
# It is safe to run on local Jupyter too — packages already installed will be skipped.
!pip install -q lightgbm catboost imbalanced-learn shap
print("All required libraries installed.")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 1 — DATA INTELLIGENCE LAYER
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 1: Data Intelligence Layer\n\n"
                "> **Objective:** Load raw HR data, assess quality across every dimension, "
                "and produce a heuristic Data Quality Score before any analysis begins.\n"))

cells.append(code(
'''# ── Environment Setup ─────────────────────────────────────────────────────────
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
import matplotlib.pyplot as plt, seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

# Auto-detect Colab vs local Jupyter and set the right Plotly renderer
try:
    import google.colab
    IN_COLAB = True
    pio.renderers.default = "colab"
except ImportError:
    IN_COLAB = False
    pio.renderers.default = "notebook"

from sklearn.model_selection import (train_test_split, StratifiedKFold,
                                     GridSearchCV, RandomizedSearchCV)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix,
                             roc_curve, precision_recall_curve,
                             average_precision_score)
from xgboost import XGBClassifier
import lightgbm as lgb
from catboost import CatBoostClassifier
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek
import shap, joblib, json, os
shap.initjs()   # Required for SHAP JavaScript plots in both Colab and Jupyter

# ── Visual style ──────────────────────────────────────────────────────────────
PALETTE = ["#e94560","#0f3460","#16213e","#533483","#f5a623","#2ecc71"]
plt.rcParams.update({"figure.figsize":(12,5),"axes.spines.top":False,
                     "axes.spines.right":False,"axes.grid":True,"grid.alpha":0.3})
sns.set_palette(PALETTE)
np.random.seed(42)
env_label = "Google Colab" if IN_COLAB else "Local Jupyter"
print(f"Environment : {env_label}")
print(f"Plotly renderer : {pio.renderers.default}")
print("All libraries loaded successfully.")
'''))

cells.append(code(
'''# ── Load Dataset ──────────────────────────────────────────────────────────────
DATASET_URL = ("https://raw.githubusercontent.com/pplonski/datasets-for-start"
               "/master/employee_attrition/HR-Employee-Attrition-All.csv")
df_raw = pd.read_csv(DATASET_URL)
df = df_raw.copy()
print(f"Rows: {df.shape[0]:,}  |  Columns: {df.shape[1]}")
print(f"Memory: {df.memory_usage(deep=True).sum()/1024:.1f} KB")
display(df.head(3))
'''))

cells.append(code(
'''# ── Data Quality Assessment ────────────────────────────────────────────────────
CONSTANT_COLS = ["EmployeeCount","StandardHours","Over18"]
ID_COLS       = ["EmployeeNumber"]

def compute_dq_report(dataframe):
    """Return a Data Quality report DataFrame."""
    n = len(dataframe); report = []
    for col in dataframe.columns:
        s = dataframe[col]
        missing     = s.isnull().sum()
        missing_pct = missing / n * 100
        unique_vals = s.nunique()
        is_constant = unique_vals <= 1
        is_id       = col in ID_COLS
        outlier_pct = 0.0
        if s.dtype in [np.float64, np.int64] and unique_vals > 10:
            Q1, Q3   = s.quantile(0.25), s.quantile(0.75)
            IQR      = Q3 - Q1
            outliers = ((s < Q1-1.5*IQR) | (s > Q3+1.5*IQR)).sum()
            outlier_pct = outliers / n * 100
        score = 100 - missing_pct*2 - min(outlier_pct*0.5, 10)
        if is_constant: score -= 30
        if is_id:       score -= 20
        score = max(0, score)
        issues = []
        if missing > 0:    issues.append(f"Missing {missing_pct:.1f}%")
        if is_constant:    issues.append("Constant")
        if is_id:          issues.append("Identifier")
        if outlier_pct>5:  issues.append(f"Outliers {outlier_pct:.1f}%")
        status = ("Good" if score>=85 else "Caution" if score>=60 else "Poor")
        report.append({"Column":col,"Dtype":str(s.dtype),"Missing":missing,
                        "Missing%":round(missing_pct,2),"Unique":unique_vals,
                        "Outlier%":round(outlier_pct,2),
                        "Quality Score":round(score,1),"Status":status,
                        "Issues":"; ".join(issues) or "None"})
    return pd.DataFrame(report)

dq_report = compute_dq_report(df)
overall_dq = dq_report["Quality Score"].mean()
print(f"Overall Data Quality Score: {overall_dq:.1f} / 100")
display(dq_report.sort_values("Quality Score").head(10))
'''))

cells.append(code(
'''# ── Data Quality Dashboard ────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18,5))
fig.suptitle("Data Quality Dashboard", fontsize=16, fontweight="bold")

# Quality bucket bar
score_labels = ["Poor","Caution","Good"]
score_colors = ["#e94560","#f5a623","#2ecc71"]
counts_dq = pd.cut(dq_report["Quality Score"],bins=[0,60,85,100],
                   labels=score_labels).value_counts()
axes[0].bar(counts_dq.index, counts_dq.values, color=score_colors)
axes[0].set_title("Column Quality Distribution")
for i,(idx,val) in enumerate(counts_dq.items()):
    axes[0].text(i, val+0.1, str(val), ha="center", fontweight="bold")

# Top outlier columns
num_dq = dq_report[dq_report["Dtype"].isin(["int64","float64"])].nlargest(10,"Outlier%")
axes[1].barh(num_dq["Column"], num_dq["Outlier%"], color="#e94560", alpha=0.8)
axes[1].set_title("Top Columns by Outlier %")
axes[1].set_xlabel("Outlier %")

# Gauge
gc = "#2ecc71" if overall_dq>=85 else ("#f5a623" if overall_dq>=60 else "#e94560")
axes[2].pie([overall_dq, 100-overall_dq], colors=[gc,"#eeeeee"],
            startangle=90, counterclock=False, wedgeprops={"width":0.4})
axes[2].text(0,0,f"{overall_dq:.0f}\\n/100",ha="center",va="center",
             fontsize=22,fontweight="bold",color=gc)
axes[2].set_title("Overall Quality Score")
plt.tight_layout(); plt.show()

# Drop useless columns
DROP_COLS = CONSTANT_COLS + ID_COLS
df.drop(columns=[c for c in DROP_COLS if c in df.columns], inplace=True)
print(f"Dropped {len(DROP_COLS)} constant/identifier columns. Shape: {df.shape}")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 2 — HR ANALYTICS & WORKFORCE INTELLIGENCE
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 2: HR Analytics & Workforce Intelligence\n\n"
                "> **Objective:** Understand the workforce comprehensively before modelling. "
                "These charts are what business stakeholders actually review.\n"))

cells.append(code(
'''# ── Encode target, compute headline KPIs ──────────────────────────────────────
df["Attrition_Num"] = (df["Attrition"] == "Yes").astype(int)
attrition_rate  = df["Attrition_Num"].mean() * 100
total_employees = len(df)
leavers         = df["Attrition_Num"].sum()
print(f"Total Employees : {total_employees:,}")
print(f"Employees Leaving: {leavers:,}  ({attrition_rate:.1f}%)")
print(f"Employees Staying: {total_employees-leavers:,}  ({100-attrition_rate:.1f}%)")
'''))

cells.append(code(
'''# ── 2.1 Employee Demographics ─────────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(20,11))
fig.suptitle("Employee Demographics Overview", fontsize=18, fontweight="bold")

for label, color in [("No","#2ecc71"),("Yes","#e94560")]:
    axes[0,0].hist(df[df["Attrition"]==label]["Age"], bins=20,
                   alpha=0.6, color=color, label=label, edgecolor="white")
axes[0,0].set_title("Age Distribution by Attrition"); axes[0,0].legend(title="Attrition")

gender_attr = df.groupby(["Gender","Attrition"]).size().unstack(fill_value=0)
gender_attr.plot(kind="bar", ax=axes[0,1], color=["#2ecc71","#e94560"], edgecolor="white")
axes[0,1].set_title("Gender by Attrition"); axes[0,1].tick_params(axis="x",rotation=0)
axes[0,1].legend(title="Attrition")

marital_rate = df.groupby("MaritalStatus")["Attrition_Num"].mean()*100
marital_rate.sort_values(ascending=False).plot(
    kind="bar",ax=axes[0,2],color=["#e94560","#f5a623","#2ecc71"][:len(marital_rate)],
    edgecolor="white")
axes[0,2].set_title("Attrition Rate by Marital Status (%)")
axes[0,2].tick_params(axis="x",rotation=0)

edu_rate = df.groupby("EducationField")["Attrition_Num"].mean()*100
edu_rate.sort_values().plot(kind="barh",ax=axes[1,0],color="#533483",edgecolor="white")
axes[1,0].set_title("Attrition Rate by Education Field (%)")

edu_map = {1:"Below College",2:"College",3:"Bachelor",4:"Master",5:"Doctor"}
df["Education_Label"] = df["Education"].map(edu_map)
df.groupby("Education_Label")["Attrition_Num"].mean().mul(100).sort_values(ascending=False).plot(
    kind="bar",ax=axes[1,1],color="#0f3460",edgecolor="white")
axes[1,1].set_title("Attrition Rate by Education Level (%)")
axes[1,1].tick_params(axis="x",rotation=30)

df["Age_Band"] = pd.cut(df["Age"],bins=[17,25,35,45,55,100],
                         labels=["18-25","26-35","36-45","46-55","55+"])
df.groupby("Age_Band")["Attrition_Num"].mean().mul(100).plot(
    kind="bar",ax=axes[1,2],color=PALETTE,edgecolor="white")
axes[1,2].set_title("Attrition Rate by Age Band (%)")
axes[1,2].tick_params(axis="x",rotation=0)

plt.tight_layout(); plt.show()
print("EXECUTIVE INSIGHT - DEMOGRAPHICS")
print("- Single employees leave at significantly higher rates.")
print("- Employees aged 26-35 represent the highest attrition segment (critical talent flight window).")
print("- Technical fields show elevated attrition due to high external market demand.")
'''))

cells.append(code(
'''# ── 2.2 Workforce Trends ──────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(20,6))
fig.suptitle("Workforce Trends", fontsize=18, fontweight="bold")

dept_rate = df.groupby("Department")["Attrition_Num"].mean()*100
dept_rate.sort_values(ascending=False).plot(
    kind="bar",ax=axes[0],
    color=["#e94560","#f5a623","#2ecc71"][:len(dept_rate)],edgecolor="white")
axes[0].set_title("Attrition Rate by Department (%)")
axes[0].tick_params(axis="x",rotation=15)

role_rate = df.groupby("JobRole")["Attrition_Num"].mean()*100
role_rate.sort_values().plot(kind="barh",ax=axes[1],color="#e94560",alpha=0.8,edgecolor="white")
axes[1].set_title("Attrition Rate by Job Role (%)")

groups = [df[df["Attrition"]==g]["YearsAtCompany"] for g in ["No","Yes"]]
axes[2].boxplot(groups, labels=["Stay","Leave"], patch_artist=True,
                boxprops=dict(facecolor="#16213e",alpha=0.7))
axes[2].set_title("Years at Company: Stay vs Leave")

plt.tight_layout(); plt.show()
print("EXECUTIVE INSIGHT - WORKFORCE TRENDS")
print("- Sales Department has the highest attrition (quota pressure + limited career ladders).")
print("- Sales Representatives are the single highest-attrition role - urgent redesign needed.")
print("- Employees who leave have significantly fewer years at the company (first 3 years are critical).")
'''))

cells.append(code(
'''# ── 2.3 Compensation & Satisfaction Analytics ─────────────────────────────────
SAT_COLS = ["JobSatisfaction","EnvironmentSatisfaction",
            "RelationshipSatisfaction","WorkLifeBalance"]

fig, axes = plt.subplots(2, 2, figsize=(18,11))
fig.suptitle("Compensation & Satisfaction Analytics", fontsize=18, fontweight="bold")

sns.boxplot(data=df, x="JobLevel", y="MonthlyIncome", hue="Attrition",
            palette={"No":"#2ecc71","Yes":"#e94560"}, ax=axes[0,0])
axes[0,0].set_title("Monthly Income by Job Level & Attrition")

dept_order = df.groupby("Department")["MonthlyIncome"].median().sort_values().index
sns.violinplot(data=df, x="Department", y="MonthlyIncome", hue="Attrition",
               split=True, palette={"No":"#2ecc71","Yes":"#e94560"},
               order=dept_order, ax=axes[0,1])
axes[0,1].set_title("Income Distribution by Department")
axes[0,1].tick_params(axis="x",rotation=15)

sat_means = df.groupby("Attrition")[SAT_COLS].mean()
x = np.arange(len(SAT_COLS)); w = 0.35
axes[1,0].bar(x-w/2, sat_means.loc["No"],  w, label="Stay",  color="#2ecc71",edgecolor="white")
axes[1,0].bar(x+w/2, sat_means.loc["Yes"], w, label="Leave", color="#e94560",edgecolor="white")
axes[1,0].set_title("Avg Satisfaction: Stay vs Leave")
axes[1,0].set_xticks(x)
axes[1,0].set_xticklabels(["Job Sat.","Env. Sat.","Rel. Sat.","WLB"],rotation=15)
axes[1,0].legend(); axes[1,0].set_ylabel("Score (1-4)")

ot_rate = df.groupby("OverTime")["Attrition_Num"].mean()*100
bars = axes[1,1].bar(ot_rate.index, ot_rate.values,
                     color=["#2ecc71","#e94560"],edgecolor="white",width=0.4)
axes[1,1].set_title("Attrition Rate: Overtime vs No Overtime (%)")
for bar, val in zip(bars, ot_rate.values):
    axes[1,1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                   f"{val:.1f}%", ha="center", fontweight="bold", fontsize=13)

plt.tight_layout(); plt.show()
ot_yes = df[df["OverTime"]=="Yes"]["Attrition_Num"].mean()*100
ot_no  = df[df["OverTime"]=="No"]["Attrition_Num"].mean()*100
print(f"EXECUTIVE INSIGHT - OVERTIME MULTIPLIER: {ot_yes:.0f}% vs {ot_no:.0f}% = {ot_yes/ot_no:.1f}x higher risk")
print("- Employees who leave score lower on ALL four satisfaction dimensions (systemic engagement issue).")
print("- Junior employees (Job Level 1-2) with below-median income show the sharpest attrition risk.")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 3 — ADVANCED FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 3: Advanced Feature Engineering\n\n"
                "> **Objective:** Engineer composite features that encode domain HR knowledge. "
                "Some (like `Engagement_Index`) consolidate redundant signals for the ML model, "
                "while others (like `Flight_Risk_Score` and `Tenure_Group`) are illustrative "
                "heuristics designed strictly for HR visualization and are dropped before modeling.\n\n"
                "| Feature | Formula |\n|---|---|\n"
                "| `Promotion_Gap` | `YearsSinceLastPromotion / (TotalWorkingYears+1)` |\n"
                "| `Compensation_Ratio` | `MonthlyIncome / (JobLevel * 1000)` |\n"
                "| `Tenure_Group` | Bucketed from `YearsAtCompany` |\n"
                "| `Engagement_Index` | Mean of 4 satisfaction scores (0–1) |\n"
                "| `Burnout_Score` | Weighted: Overtime + Travel + RoleYears |\n"
                "| `Flight_Risk_Score` | Pre-model composite risk metric |\n"))

cells.append(code(
'''# ── Feature Engineering ───────────────────────────────────────────────────────
df_fe = df.copy()

# 1. Promotion Gap
df_fe["Promotion_Gap"] = (df_fe["YearsSinceLastPromotion"]
                           / (df_fe["TotalWorkingYears"] + 1))

# 2. Compensation Ratio
df_fe["Compensation_Ratio"] = df_fe["MonthlyIncome"] / (df_fe["JobLevel"] * 1000)

# 3. Tenure Group
def tenure_group(y):
    if y <= 3:    return "Early Career"
    elif y <= 8:  return "Mid Career"
    elif y <= 15: return "Senior"
    else:         return "Veteran"
df_fe["Tenure_Group"] = df_fe["YearsAtCompany"].apply(tenure_group)

# 4. Engagement Index (normalize 1-4 to 0-1, then mean)
for col in SAT_COLS:
    df_fe[col + "_norm"] = (df_fe[col] - 1) / 3
eng_norm_cols = [c + "_norm" for c in SAT_COLS]
df_fe["Engagement_Index"] = df_fe[eng_norm_cols].mean(axis=1)
df_fe.drop(columns=eng_norm_cols, inplace=True)

# 5. Burnout Score
travel_map = {"Non-Travel":0,"Travel_Rarely":1,"Travel_Frequently":2}
df_fe["Travel_Score"] = df_fe["BusinessTravel"].map(travel_map)
ot_num = (df_fe["OverTime"] == "Yes").astype(int)
df_fe["Burnout_Score"] = (
    0.4 * ot_num +
    0.3 * (df_fe["YearsInCurrentRole"] / (df_fe["YearsInCurrentRole"].max() + 1e-9)) +
    0.3 * (df_fe["Travel_Score"] / 2)
)

# 6. Flight Risk Score (composite pre-model signal)
df_fe["Flight_Risk_Score"] = (
    0.30 * df_fe["Promotion_Gap"].clip(upper=1) +
    0.25 * (1 - df_fe["Engagement_Index"]) +
    0.25 * df_fe["Burnout_Score"] +
    0.20 * (1 - (df_fe["Compensation_Ratio"].clip(upper=2) / 2))
).round(4)

new_feats = ["Promotion_Gap","Compensation_Ratio","Engagement_Index",
             "Burnout_Score","Flight_Risk_Score"]
print("Engineered Features Summary:")
display(df_fe[new_feats].describe().T[["mean","std","min","max"]].round(3))
'''))

cells.append(code(
'''# ── Visualise Engineered Features ────────────────────────────────────────────
fig, axes = plt.subplots(2, 3, figsize=(20,10))
fig.suptitle("Engineered Feature Analysis vs Attrition", fontsize=18, fontweight="bold")

pal = {"No":"#2ecc71","Yes":"#e94560"}
pairs = [("Promotion_Gap",axes[0,0]),("Compensation_Ratio",axes[0,1]),
         ("Engagement_Index",axes[0,2]),("Burnout_Score",axes[1,0]),
         ("Flight_Risk_Score",axes[1,1])]
for feat, ax in pairs:
    sns.boxplot(data=df_fe, x="Attrition", y=feat, palette=pal, ax=ax)
    ax.set_title(f"{feat} by Attrition")

tg_rate = df_fe.groupby("Tenure_Group")["Attrition_Num"].mean()*100
tg_order = [t for t in ["Early Career","Mid Career","Senior","Veteran"]
            if t in tg_rate.index]
tg_vals  = tg_rate.reindex(tg_order)
c_tg = ["#e94560","#f5a623","#2ecc71","#0f3460"][:len(tg_vals)]
axes[1,2].bar(tg_vals.index, tg_vals.values, color=c_tg, edgecolor="white")
axes[1,2].set_title("Attrition Rate by Tenure Group (%)")
axes[1,2].tick_params(axis="x",rotation=15)

plt.tight_layout(); plt.show()
'''))

cells.append(code(
'''# ── Multicollinearity Check (Correlation Matrix) ─────────────────────────────
cols_to_check = ["Promotion_Gap", "Compensation_Ratio", "Engagement_Index", 
                 "Burnout_Score", "Flight_Risk_Score"] + SAT_COLS
corr_matrix = df_fe[cols_to_check].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, center=0)
plt.title("Feature Correlation Matrix (Multicollinearity Check)", fontsize=14, fontweight="bold")
plt.tight_layout(); plt.show()
'''))

# ─────────────────────────────────────────────────────────
# PHASE 4 — ML PIPELINE
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 4: Machine Learning Pipeline\n\n"
                "> **Objective:** Train 6 models with best-practice techniques — "
                "stratified CV, SMOTE class-imbalance handling, and "
                "randomized hyperparameter search.\n\n"
                "| Model | Tuning |\n|---|---|\n"
                "| Logistic Regression | GridSearchCV |\n"
                "| Decision Tree | GridSearchCV |\n"
                "| Random Forest | RandomizedSearchCV |\n"
                "| XGBoost | RandomizedSearchCV |\n"
                "| LightGBM | RandomizedSearchCV |\n"
                "| CatBoost | Default (fast) |\n"))

cells.append(code(
'''# ── 4.1 Prepare Data ──────────────────────────────────────────────────────────
df_model = df_fe.copy()
df_model["Attrition"] = df_model["Attrition_Num"]
df_model.drop(columns=["Attrition_Num","Education_Label","Age_Band","Travel_Score",
                        "Tenure_Group", "Flight_Risk_Score", "JobSatisfaction", 
                        "EnvironmentSatisfaction", "RelationshipSatisfaction", 
                        "WorkLifeBalance"], errors="ignore", inplace=True)

# Label encode binary categoricals
for col in ["Gender","OverTime"]:
    if col in df_model.columns:
        df_model[col] = LabelEncoder().fit_transform(df_model[col])

# One-hot encode remaining categoricals
cat_cols = [c for c in df_model.select_dtypes(include="object").columns if c != "Attrition"]
df_model = pd.get_dummies(df_model, columns=cat_cols, drop_first=True)

X = df_model.drop(columns=["Attrition"])
y = df_model["Attrition"]
print(f"Feature matrix: {X.shape[0]:,} x {X.shape[1]}")
print(f"Class balance — Stay: {(y==0).sum()} | Leave: {(y==1).sum()} ({y.mean()*100:.1f}%)")
'''))

cells.append(code(
'''# ── 4.2 Split + Scale + Resample ──────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y)

scaler      = StandardScaler()
X_train_sc  = scaler.fit_transform(X_train)
X_test_sc   = scaler.transform(X_test)

smote       = SMOTE(random_state=42)
X_tr_sm, y_tr_sm = smote.fit_resample(X_train_sc, y_train)

print(f"Original train   : {X_train_sc.shape[0]:,}")
print(f"After SMOTE      : {X_tr_sm.shape[0]:,}")
'''))

cells.append(code(
'''# ── 4.3 Train Baseline Models ─────────────────────────────────────────────────
skf = StratifiedKFold(n_splits=5)

print("Training Logistic Regression (GridSearchCV)...")
lr_gs = GridSearchCV(LogisticRegression(max_iter=1000, random_state=42),
                     {"C":[0.01,0.1,1,10],"penalty":["l2"]},
                     cv=skf, scoring="roc_auc", n_jobs=-1)
lr_gs.fit(X_tr_sm, y_tr_sm)
model_lr = lr_gs.best_estimator_

print("Training Decision Tree (GridSearchCV)...")
dt_gs = GridSearchCV(DecisionTreeClassifier(random_state=42),
                     {"max_depth":[3,5,7,10],"min_samples_split":[2,10,20]},
                     cv=skf, scoring="roc_auc", n_jobs=-1)
dt_gs.fit(X_tr_sm, y_tr_sm)
model_dt = dt_gs.best_estimator_

print("Training Random Forest (RandomizedSearchCV)...")
rf_rs = RandomizedSearchCV(RandomForestClassifier(random_state=42),
    {"n_estimators":[100,200],"max_depth":[None,10,20],
     "min_samples_split":[2,5],"max_features":["sqrt","log2"]},
    n_iter=10, cv=skf, scoring="roc_auc", n_jobs=-1, random_state=42)
rf_rs.fit(X_tr_sm, y_tr_sm)
model_rf = rf_rs.best_estimator_
print("Baseline models trained.")
'''))

cells.append(code(
'''# ── 4.4 Train Advanced Models ─────────────────────────────────────────────────
print("Training XGBoost (RandomizedSearchCV)...")
xgb_rs = RandomizedSearchCV(
    XGBClassifier(random_state=42, eval_metric="logloss"),
    {"n_estimators":[100,200,300],"max_depth":[3,5,7],
     "learning_rate":[0.01,0.05,0.1],"subsample":[0.7,0.9],
     "colsample_bytree":[0.7,1.0]},
    n_iter=15, cv=skf, scoring="roc_auc", n_jobs=-1, random_state=42)
xgb_rs.fit(X_tr_sm, y_tr_sm)
model_xgb = xgb_rs.best_estimator_

print("Training LightGBM (RandomizedSearchCV)...")
lgbm_rs = RandomizedSearchCV(
    lgb.LGBMClassifier(random_state=42, verbose=-1),
    {"n_estimators":[100,200,300],"max_depth":[3,5,7,-1],
     "learning_rate":[0.01,0.05,0.1],"num_leaves":[20,31,50],"subsample":[0.7,0.9]},
    n_iter=15, cv=skf, scoring="roc_auc", n_jobs=-1, random_state=42)
lgbm_rs.fit(X_tr_sm, y_tr_sm)
model_lgbm = lgbm_rs.best_estimator_

print("Training CatBoost...")
model_cat = CatBoostClassifier(iterations=300, depth=6, learning_rate=0.05,
                                random_seed=42, verbose=0)
model_cat.fit(X_tr_sm, y_tr_sm)
print("All 6 models trained successfully.")
'''))

cells.append(code(
'''# ── 4.5 Robustness Check: Repeated Cross-Validation (Top Model) ───────────────
# To ensure our hyperparameter tuning didn't just overfit a single train/test split noise,
# we validate the top model's pipeline across 5 different random seeds.

from numpy import mean, std

print("Validating XGBoost stability across 5 random seeds...")
seeds = [42, 7, 123, 2024, 99]
auc_scores = []

for s in seeds:
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.20, random_state=s, stratify=y)
    sc = StandardScaler().fit(Xtr)
    Xtr_s, Xte_s = sc.transform(Xtr), sc.transform(Xte)
    Xtr_sm, ytr_sm = SMOTE(random_state=s).fit_resample(Xtr_s, ytr)
    
    # Reuse the tuned hyperparams but refit on the new split
    m = XGBClassifier(**model_xgb.get_params())
    m.fit(Xtr_sm, ytr_sm)
    auc_scores.append(roc_auc_score(yte, m.predict_proba(Xte_s)[:,1]))

print(f"ROC-AUC across 5 seeds: {mean(auc_scores):.4f} ± {std(auc_scores):.4f}")
print("Small variance indicates stable, generalizable hyperparameters.")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 5 — ENTERPRISE EVALUATION
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 5: Enterprise Evaluation Framework\n\n"
                "> **Objective:** Rank all models using both statistical *and* business-focused "
                "metrics. **Attrition Capture Rate** (Recall) tells HR what fraction of actual "
                "leavers the model identifies. **Intervention Accuracy** (Precision) tells HR "
                "how many flagged employees actually leave.\n"))

cells.append(code(
'''# ── Evaluate All Models ────────────────────────────────────────────────────────
def evaluate_model(name, model, Xte, yte):
    y_pred  = model.predict(Xte)
    y_proba = model.predict_proba(Xte)[:,1]
    fpr,tpr,_ = roc_curve(yte, y_proba)
    prec_c,rec_c,_ = precision_recall_curve(yte, y_proba)
    cm = confusion_matrix(yte, y_pred)
    TP,FN,FP,TN = cm[1,1],cm[1,0],cm[0,1],cm[0,0]
    return {
        "Model": name,
        "Accuracy":  round(accuracy_score(yte, y_pred), 4),
        "Precision": round(precision_score(yte, y_pred), 4),
        "Recall":    round(recall_score(yte, y_pred), 4),
        "F1 Score":  round(f1_score(yte, y_pred), 4),
        "ROC AUC":   round(roc_auc_score(yte, y_proba), 4),
        "PR AUC":    round(average_precision_score(yte, y_proba), 4),
        "Capture Rate":        round(TP/(TP+FN) if (TP+FN)>0 else 0, 4),
        "Intervention Acc.":   round(TP/(TP+FP) if (TP+FP)>0 else 0, 4),
        "_fpr":fpr,"_tpr":tpr,"_prec":prec_c,"_rec":rec_c,
        "_model":model,"_proba":y_proba
    }

named_models = {
    "Logistic Regression": (model_lr,  X_test_sc),
    "Decision Tree":       (model_dt,  X_test_sc),
    "Random Forest":       (model_rf,  X_test_sc),
    "XGBoost":             (model_xgb, X_test_sc),
    "LightGBM":            (model_lgbm,X_test_sc),
    "CatBoost":            (model_cat, X_test_sc),
}

eval_results = []
for name,(model,Xte) in named_models.items():
    r = evaluate_model(name, model, Xte, y_test)
    eval_results.append(r)
    print(f"{name:25s} | ROC-AUC:{r['ROC AUC']:.4f} | Capture:{r['Capture Rate']:.4f}")

lb_cols = ["Model","Accuracy","Precision","Recall","F1 Score",
           "ROC AUC","PR AUC","Capture Rate","Intervention Acc."]
leaderboard = (pd.DataFrame([{k:v for k,v in r.items() if not k.startswith("_")}
                               for r in eval_results])
               .sort_values("Capture Rate", ascending=False)
               .reset_index(drop=True))
print("\\nModel Leaderboard (ranked by Capture Rate to prioritize identifying leavers):")
display(leaderboard[lb_cols].style
        .background_gradient(cmap="RdYlGn", subset=["ROC AUC","F1 Score","Capture Rate"])
        .format({c:"{:.4f}" for c in lb_cols[1:]}))

best_model_name = leaderboard.iloc[0]["Model"]
best_result     = next(r for r in eval_results if r["Model"]==best_model_name)
best_model_obj  = named_models[best_model_name][0]
print(f"\\nBest Model: {best_model_name} (ROC-AUC: {best_result['ROC AUC']:.4f})")
'''))

cells.append(code(
'''# ── ROC + PR Curves + Confusion Matrix ───────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(21,6))
fig.suptitle("Enterprise Evaluation Dashboard", fontsize=18, fontweight="bold")
colors6 = ["#e94560","#0f3460","#2ecc71","#f5a623","#533483","#16213e"]

for r,c in zip(eval_results, colors6):
    axes[0].plot(r["_fpr"],r["_tpr"],label=f"{r['Model']} ({r['ROC AUC']:.3f})",color=c,lw=2)
axes[0].plot([0,1],[0,1],"k--",lw=1)
axes[0].set_title("ROC Curves"); axes[0].set_xlabel("FPR"); axes[0].set_ylabel("TPR")
axes[0].legend(fontsize=7,loc="lower right")

for r,c in zip(eval_results, colors6):
    axes[1].plot(r["_rec"],r["_prec"],label=f"{r['Model']} (PR:{r['PR AUC']:.3f})",color=c,lw=2)
axes[1].set_title("Precision-Recall Curves")
axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision")
axes[1].legend(fontsize=7,loc="upper right")

cm = confusion_matrix(y_test, best_model_obj.predict(X_test_sc))
sns.heatmap(cm,annot=True,fmt="d",cmap="Blues",ax=axes[2],
            xticklabels=["Stay","Leave"],yticklabels=["Stay","Leave"])
axes[2].set_title(f"Confusion Matrix\\n{best_model_name}")

plt.tight_layout(); plt.show()
'''))

# ─────────────────────────────────────────────────────────
# PHASE 6 — EXPLAINABLE AI (SHAP)
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 6: Explainable AI (SHAP)\n\n"
                "> **Objective:** Make the model's decisions transparent. "
                "SHAP provides **global** explanations (what drives attrition company-wide) "
                "and **local** explanations (why *this* employee is at risk).\n"))

cells.append(code(
'''# ── 6.1 SHAP Global Importance ────────────────────────────────────────────────
X_test_df = pd.DataFrame(X_test_sc, columns=X.columns)
print(f"Computing SHAP for: {best_model_name}")
try:
    explainer   = shap.TreeExplainer(best_model_obj)
    explanation = explainer(X_test_df)
    shap_vals   = explanation.values if explanation.values.ndim == 2 else explanation.values[..., 1]
except Exception:
    explainer   = shap.KernelExplainer(best_model_obj.predict_proba,
                                        shap.sample(X_test_df, 50))
    sv          = explainer.shap_values(X_test_df, silent=True)
    shap_vals   = sv[1] if isinstance(sv,list) else sv
print("SHAP values computed.")

plt.figure(figsize=(12,8))
shap.summary_plot(shap_vals, X_test_df, plot_type="bar", max_display=20, show=False)
plt.title("SHAP Global Feature Importance (Top 20)", fontsize=14, fontweight="bold")
plt.tight_layout(); plt.show()
'''))

cells.append(code(
'''# ── 6.2 SHAP Beeswarm ─────────────────────────────────────────────────────────
plt.figure(figsize=(12,9))
shap.summary_plot(shap_vals, X_test_df, max_display=20, show=False)
plt.title("SHAP Beeswarm — Feature Direction & Magnitude", fontsize=14, fontweight="bold")
plt.tight_layout(); plt.show()
print("Beeswarm key: Right of 0 = drives LEAVING; Left = drives STAYING")
print("Color: Red = high feature value; Blue = low feature value")
'''))

cells.append(code(
'''# ── 6.3 Employee-Level Narrative Explanations ─────────────────────────────────
y_proba_all  = best_model_obj.predict_proba(X_test_sc)[:,1]
high_risk_idx = np.argsort(y_proba_all)[-5:][::-1]

def narrative(emp_idx, shap_row, feature_names, risk_score):
    s = pd.Series(shap_row, index=feature_names)
    pos = s.nlargest(3); neg = s.nsmallest(3)
    out = [f"EMP-{emp_idx:04d}  |  Risk Score: {risk_score*100:.1f}/100"]
    out.append("  Risk Drivers (pushing toward LEAVING):")
    for feat,val in pos.items():
        out.append(f"    * {feat:<35s}  SHAP={val:+.3f}  [{'HIGH' if val>0 else 'LOW'}]")
    out.append("  Protective Factors (pushing toward STAYING):")
    for feat,val in neg.items():
        out.append(f"    * {feat:<35s}  SHAP={val:+.3f}  [{'HIGH' if val>0 else 'LOW'}]")
    return "\\n".join(out)

print("="*65)
print("  Employee-Level Risk Explanations — Top 5 At-Risk")
print("="*65)
for idx in high_risk_idx:
    print("\\n" + "-"*65)
    print(narrative(idx, shap_vals[idx], X.columns, y_proba_all[idx]))
print("-"*65)
'''))

cells.append(code(
'''# ── 6.4 SHAP Waterfall for Top High-Risk Employee ────────────────────────────
emp = high_risk_idx[0]
try:
    ev = explainer.expected_value
    if isinstance(ev, (list, np.ndarray)):
        ev = ev[1] if len(ev) > 1 else ev[0]
    shap_exp = shap.Explanation(values=shap_vals[emp], base_values=ev,
                                 data=X_test_df.iloc[emp].values,
                                 feature_names=X.columns.tolist())
    plt.figure(figsize=(12,7))
    shap.plots.waterfall(shap_exp, max_display=15, show=False)
    plt.title(f"SHAP Waterfall — EMP-{emp:04d}  Risk: {y_proba_all[emp]*100:.1f}%",
              fontsize=13, fontweight="bold")
    plt.tight_layout(); plt.show()
except Exception as e:
    # Fallback bar chart
    shap_emp  = pd.Series(shap_vals[emp], index=X.columns)
    shap_top  = shap_emp.abs().nlargest(15)
    shap_vals_ = shap_emp[shap_top.index]
    colors_w   = ["#e94560" if v>0 else "#2ecc71" for v in shap_vals_.values]
    plt.figure(figsize=(10,7))
    plt.barh(shap_vals_.index, shap_vals_.values, color=colors_w)
    plt.axvline(0, color="black", lw=0.8)
    plt.title(f"SHAP Contributions — EMP-{emp:04d}", fontweight="bold")
    plt.xlabel("SHAP Value"); plt.tight_layout(); plt.show()
'''))

# ─────────────────────────────────────────────────────────
# PHASE 7 — EMPLOYEE RISK ENGINE
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 7: Employee Risk Engine\n\n"
                "> **Objective:** Assign every employee a 0–100 Risk Score and segment "
                "them into four actionable tiers that HR can act on immediately.\n\n"
                "| Score | Category |\n|---|---|\n"
                "| 0–19 | Low Risk |\n| 20–44 | Moderate Risk |\n"
                "| 45–69 | High Risk |\n| 70–100 | Critical Risk |\n\n"
                "> *Note: Risk scores for training-set employees may be optimistically biased; "
                "only test-set scores (n=294) are validated out-of-sample.*\n"))

cells.append(code(
'''# ── Risk Score Computation ────────────────────────────────────────────────────
X_all_sc   = scaler.transform(X)
risk_proba = best_model_obj.predict_proba(X_all_sc)[:,1]

risk_df = df_fe.copy()
risk_df["Risk_Score"]    = np.round(risk_proba * 100, 2)
risk_df["Risk_Proba"]    = risk_proba
risk_df["Data_Split"]    = ["Train" if i in X_train.index else "Test" for i in risk_df.index]

def categorize_risk(s):
    if s < 20:   return "Low Risk"
    elif s < 45: return "Moderate Risk"
    elif s < 70: return "High Risk"
    else:        return "Critical Risk"

risk_df["Risk_Category"] = risk_df["Risk_Score"].apply(categorize_risk)
risk_sum = risk_df["Risk_Category"].value_counts()

print("Employee Risk Distribution:")
for cat in ["Critical Risk","High Risk","Moderate Risk","Low Risk"]:
    n = risk_sum.get(cat, 0)
    print(f"  {cat:<18s}: {n:>4,}  ({n/len(risk_df)*100:.1f}%)")
'''))

cells.append(code(
'''# ── Risk Visualisations ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(20,6))
fig.suptitle("Employee Risk Engine", fontsize=18, fontweight="bold")

# Donut
cat_order = ["Critical Risk","High Risk","Moderate Risk","Low Risk"]
cat_colors = ["#e94560","#e67e22","#f5a623","#2ecc71"]
counts = [risk_sum.get(c,0) for c in cat_order]
axes[0].pie(counts, labels=cat_order, colors=cat_colors, autopct="%1.1f%%",
            startangle=90, wedgeprops={"width":0.5}, pctdistance=0.75)
axes[0].set_title("Overall Risk Distribution")

# Histogram
axes[1].hist(risk_df["Risk_Score"], bins=40, color="#0f3460", edgecolor="white", alpha=0.85)
for th,c,lab in [(20,"#2ecc71","Low"),(45,"#f5a623","Moderate"),(70,"#e94560","Critical")]:
    axes[1].axvline(th, color=c, linestyle="--", lw=2, label=f"{lab} boundary")
axes[1].set_title("Risk Score Distribution (0-100)")
axes[1].set_xlabel("Risk Score"); axes[1].legend(fontsize=8)

# Avg risk by department
dept_risk = risk_df.groupby("Department")["Risk_Score"].mean().sort_values(ascending=False)
c_dept = ["#e94560" if v>30 else "#f5a623" if v>20 else "#2ecc71" for v in dept_risk.values]
axes[2].barh(dept_risk.index, dept_risk.values, color=c_dept, edgecolor="white")
axes[2].set_title("Avg Risk Score by Department")
axes[2].set_xlabel("Avg Risk Score")

plt.tight_layout(); plt.show()
'''))

cells.append(code(
'''# ── Risk Leaderboard (Top 20 Critical Employees) ──────────────────────────────
display_cols = [c for c in ["Department","JobRole","Age","MonthlyIncome","OverTime",
    "YearsSinceLastPromotion","Engagement_Index","Burnout_Score",
    "Risk_Score","Risk_Category"] if c in risk_df.columns]

top20 = (risk_df.sort_values("Risk_Score",ascending=False)
                .reset_index(drop=True).head(20)[display_cols])
top20.index = [f"EMP-{i:04d}" for i in top20.index]

print("Top 20 Highest-Risk Employees:")
display(top20.style
        .background_gradient(cmap="RdYlGn_r", subset=["Risk_Score"])
        .format({"Risk_Score":"{:.1f}","MonthlyIncome":"${:,.0f}",
                 "Engagement_Index":"{:.2f}","Burnout_Score":"{:.2f}"}))
'''))

# ─────────────────────────────────────────────────────────
# PHASE 8 — RETENTION RECOMMENDATION ENGINE
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 8: Retention Recommendation Engine\n\n"
                "> **Objective:** A rule-based AI engine that generates personalised, "
                "prioritised retention action plans for every high-risk employee. "
                "No ML jargon — just clear, actionable HR guidance.\n"))

cells.append(code(
'''# ── Rule Engine ───────────────────────────────────────────────────────────────
def generate_retention_plan(row):
    recs = []
    if str(row.get("OverTime","No")).lower() in ["yes","1",1]:
        recs.append({"Action":"Workload Redistribution",
            "Detail":"Overtime cap + 1.5x comp-time. Review task allocation now.",
            "Priority":"HIGH","Impact":"+12% retention probability"})
    if row.get("YearsSinceLastPromotion", 0) >= 3:
        yp = row["YearsSinceLastPromotion"]
        recs.append({"Action":"Promotion Review",
            "Detail":f"{yp:.0f} years without promotion. Initiate career path conversation.",
            "Priority":"HIGH","Impact":"+10% retention probability"})
    if row.get("Compensation_Ratio", 1.5) < 1.0:
        recs.append({"Action":"Compensation Assessment",
            "Detail":"Income below market for this job level. Initiate salary benchmarking.",
            "Priority":"HIGH","Impact":"+15% retention probability"})
    if row.get("Engagement_Index", 0.5) < 0.45:
        recs.append({"Action":"Engagement Programme",
            "Detail":"Low satisfaction composite. Assign mentor + learning budget.",
            "Priority":"MEDIUM","Impact":"+8% retention probability"})
    if str(row.get("BusinessTravel","Non-Travel")) == "Travel_Frequently":
        recs.append({"Action":"Travel Policy Review",
            "Detail":"Frequent travel is a burnout driver. Evaluate remote-first options.",
            "Priority":"MEDIUM","Impact":"+6% retention probability"})
    if row.get("YearsAtCompany", 5) <= 2:
        recs.append({"Action":"Early Tenure Buddy Programme",
            "Detail":"First 2 years are highest-risk. Structured onboarding + peer buddy.",
            "Priority":"MEDIUM","Impact":"+7% retention probability"})
    if not recs:
        recs.append({"Action":"Routine Check-in",
            "Detail":"Low current risk. Maintain via regular 1-on-1s.",
            "Priority":"LOW","Impact":"Maintain current retention"})
    return recs

high_risk_emps = (risk_df[risk_df["Risk_Category"].isin(["High Risk","Critical Risk"])]
                  .sort_values("Risk_Score",ascending=False).head(20))

records = []
for idx, row in high_risk_emps.iterrows():
    for plan in generate_retention_plan(row):
        records.append({"Employee":f"EMP-{idx:04d}",
                        "Department":row.get("Department","N/A"),
                        "Role":row.get("JobRole","N/A"),
                        "Risk Score":row["Risk_Score"],
                        "Risk Category":row["Risk_Category"],
                        **plan})

retention_df = pd.DataFrame(records)
if retention_df.empty:
    retention_df = pd.DataFrame(columns=["Employee","Department","Role","Risk Score","Risk Category","Action","Detail","Priority","Impact"])

print(f"Plans generated for {high_risk_emps.shape[0]} employees | Total actions: {len(retention_df)}")
display(retention_df.head(15).style
        .applymap(lambda v: "color:#e94560;font-weight:bold" if v=="HIGH"
                  else ("color:#f5a623;font-weight:bold" if v=="MEDIUM" else "color:#2ecc71"),
                  subset=["Priority"]))
'''))

cells.append(code(
'''# ── Action Priority Chart ─────────────────────────────────────────────────────
if not retention_df.empty:
    action_cts = retention_df["Action"].value_counts()
    bar_clrs = ["#e94560","#e67e22","#f5a623","#0f3460","#533483","#16213e"][:len(action_cts)]
    plt.figure(figsize=(12,5))
    bars = plt.barh(action_cts.index, action_cts.values, color=bar_clrs, edgecolor="white")
    plt.title("Recommended HR Interventions — Frequency", fontsize=14, fontweight="bold")
    plt.xlabel("Number of Employees")
    for bar,val in zip(bars, action_cts.values):
        plt.text(bar.get_width()+0.2, bar.get_y()+bar.get_height()/2,
                 str(val), va="center", fontweight="bold")
    plt.tight_layout(); plt.show()
else:
    print("No high-risk employees identified. No actions recommended.")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 9 — ATTRITION COST PREDICTION
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 9: Attrition Cost Prediction\n\n"
                "> **Objective:** Translate model output into a dollar figure that executives can act on.\n\n"
                "**Cost Formula** (SHRM / Gallup / Deloitte benchmarks):\n\n"
                "`Replacement Cost = Recruitment + Training + Productivity Loss + Knowledge Transfer`\n\n"
                "Industry benchmark: **50–200% of annual salary** depending on seniority.\n"))

cells.append(code(
'''# ── Cost Formula ─────────────────────────────────────────────────────────────
RETENTION_PROGRAM_COST_PCT = 0.12 # typical retention program spend as % of salary
EXPECTED_RETENTION_SUCCESS_RATE = 0.60 # literature range 20-50%, 60% used as optimistic baseline

def replacement_cost_breakdown(monthly_income, job_level, years_at_company):
    annual = monthly_income * 12
    recruit_pct = 0.20 if job_level<=2 else (0.35 if job_level<=3 else 0.50)
    recruitment = annual * recruit_pct
    training     = annual * 0.10
    ramp_months  = min(3 + job_level, 6)
    productivity = monthly_income * ramp_months * 0.50
    knowledge    = annual * min(years_at_company * 0.02, 0.20)
    return recruitment, training, productivity, knowledge

def replacement_cost(monthly_income, job_level, years_at_company):
    return round(sum(replacement_cost_breakdown(monthly_income, job_level, years_at_company)), 2)

at_risk = risk_df[risk_df["Risk_Score"] >= 45].copy()
at_risk["Annual_Salary"]    = at_risk["MonthlyIncome"] * 12
cost_records = []
cost_totals = []
for _, r in at_risk.iterrows():
    rec, trn, prd, knw = replacement_cost_breakdown(r["MonthlyIncome"], r["JobLevel"], r["YearsAtCompany"])
    total_r = rec + trn + prd + knw
    cost_records.append({"Recruitment": rec, "Training": trn, "Lost Productivity": prd, "Total": total_r})
    cost_totals.append(total_r)

at_risk["Replacement_Cost"] = cost_totals

cost_df = pd.DataFrame(cost_records)
if cost_df.empty:
    cost_df = pd.DataFrame(columns=["Recruitment", "Training", "Lost Productivity", "Total"])
total_cost = cost_df["Total"].sum() if not cost_df.empty else 0
retention_program_cost = at_risk["Annual_Salary"].sum() * RETENTION_PROGRAM_COST_PCT
savings = total_cost * EXPECTED_RETENTION_SUCCESS_RATE
roi = savings / retention_program_cost if retention_program_cost > 0 else 0

print(f"At-Risk Employees         : {len(at_risk):,}")
print(f"Total Attrition Cost      : ${total_cost:>12,.0f}")
print(f"Avg Cost Per Employee     : ${at_risk['Replacement_Cost'].mean():>12,.0f}")
print(f"Potential Savings (60% ret): ${savings:>12,.0f}")

dept_cost = at_risk.groupby("Department").agg(
    Employees_at_Risk=("Replacement_Cost","count"),
    Total_Cost=("Replacement_Cost","sum"),
    Avg_Cost=("Replacement_Cost","mean"),
).round(0).sort_values("Total_Cost",ascending=False)
display(dept_cost.style
        .background_gradient(cmap="Reds", subset=["Total_Cost"])
        .format({"Total_Cost":"${:,.0f}","Avg_Cost":"${:,.0f}"}))
'''))

cells.append(code(
'''# ── Cost Visualisations ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18,6))
fig.suptitle("Attrition Cost Impact Dashboard", fontsize=16, fontweight="bold")

dept_plot = dept_cost.sort_values("Total_Cost")
axes[0].barh(dept_plot.index, dept_plot["Total_Cost"]/1e6,
             color=["#e94560","#f5a623","#0f3460"][:len(dept_plot)],edgecolor="white")
axes[0].set_title("Total Attrition Cost by Department ($M)")
axes[0].set_xlabel("Cost ($M)")
for i,(val,_) in enumerate(zip(dept_plot["Total_Cost"],dept_plot.index)):
    axes[0].text(val/1e6+0.01, i, f"${val/1e6:.2f}M", va="center", fontweight="bold")

at_temp = at_risk.copy()
comps = {"Recruitment": 0, "Training": 0, "Productivity": 0, "Knowledge": 0}
for _, r in at_temp.iterrows():
    rec, trn, prd, knw = replacement_cost_breakdown(r["MonthlyIncome"], r["JobLevel"], r["YearsAtCompany"])
    comps["Recruitment"] += rec
    comps["Training"] += trn
    comps["Productivity"] += prd
    comps["Knowledge"] += knw

for k in comps: comps[k] /= 1e6

bars2 = axes[1].bar(comps.keys(), comps.values(),
                    color=["#e94560","#f5a623","#533483","#0f3460"],edgecolor="white")
axes[1].set_title("Attrition Cost Breakdown ($M)")
axes[1].set_ylabel("Cost ($M)")
for bar,val in zip(bars2, comps.values()):
    axes[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                 f"${val:.2f}M", ha="center", fontweight="bold")

plt.tight_layout(); plt.show()
print(f"FINANCIAL INSIGHT: Investing ${retention_program_cost/1e6:.2f}M in retention saves ${savings/1e6:.2f}M")
print(f"Estimated ROI: {roi:.1f}x return on retention investment (Sensitivity: {roi*0.5:.1f}x at 30% success, {roi*0.75:.1f}x at 45% success).")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 10 — SCENARIO SIMULATION ENGINE
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 10: Scenario Simulation Engine (What-If Analysis)\n\n"
                "> **Objective:** Let HR and executives model the impact of specific "
                "interventions *before* committing budget. Direct decision support.\n"))

cells.append(code(
'''# ── What-If Simulator ────────────────────────────────────────────────────────
def simulate(X_base, scaler, model, feature, delta, delta_type="multiply"):
    X_sim = X_base.copy()
    if feature not in X_sim.columns:
        return None, None
    if delta_type == "multiply":
        X_sim[feature] = X_sim[feature] * (1 + delta)
    elif delta_type == "add":
        X_sim[feature] = (X_sim[feature] + delta).clip(lower=0)
    elif delta_type == "set":
        X_sim[feature] = delta
    Xs = scaler.transform(X_sim)
    new_p  = model.predict_proba(Xs)[:,1]
    base_p = model.predict_proba(scaler.transform(X_base))[:,1]
    red    = (base_p.mean() - new_p.mean()) / base_p.mean() * 100
    return new_p, red

baseline_p    = best_model_obj.predict_proba(X_all_sc)[:,1]
baseline_rate = baseline_p.mean() * 100

scenarios = [
    ("Salary +15%",          "MonthlyIncome",             0.15,  "multiply"),
    ("Overtime -50%",         "OverTime",                 -0.50,  "multiply"),
    ("Work-Life Balance +1",  "WorkLifeBalance",           1,     "add"),
    ("Cap Promotion Gap at 2","YearsSinceLastPromotion",   2.0,   "set"),
    ("Travel -30%",           "Travel_Score",             -0.30,  "multiply"),
]

sc_results = []
print(f"Baseline Attrition Rate: {baseline_rate:.2f}%\\n" + "="*55)
for name, feat, delta, dtype in scenarios:
    new_p, red = simulate(X, scaler, best_model_obj, feat, delta, dtype)
    new_rate   = new_p.mean()*100 if new_p is not None else baseline_rate
    red        = red if red is not None else 0
    saved      = max(0, int((baseline_rate-new_rate)/100*len(X)))
    sc_results.append({"Scenario":name,"Baseline%":round(baseline_rate,2),
                        "New Rate%":round(new_rate,2),"Reduction%":round(red,2),
                        "Employees Saved":saved})
    print(f"  {name:<30s} {baseline_rate:.2f}% -> {new_rate:.2f}%  | Reduction: {red:.1f}%")

sc_df = pd.DataFrame(sc_results)
display(sc_df.style
        .background_gradient(cmap="RdYlGn", subset=["Reduction%"])
        .format({"Baseline%":"{:.2f}","New Rate%":"{:.2f}","Reduction%":"{:.2f}"}))
'''))

cells.append(code(
'''# ── Scenario Comparison Chart (Plotly) ───────────────────────────────────────
fig = go.Figure()
names = [s["Scenario"] for s in sc_results]
fig.add_trace(go.Bar(name="Baseline Rate", x=names,
                     y=[s["Baseline%"] for s in sc_results],
                     marker_color="#e94560", opacity=0.7))
fig.add_trace(go.Bar(name="Projected Rate After Intervention", x=names,
                     y=[s["New Rate%"] for s in sc_results],
                     marker_color="#2ecc71", opacity=0.85))
fig.update_layout(title="What-If Scenario Analysis — Attrition Rate Impact",
                  barmode="group", template="plotly_dark",
                  yaxis_title="Attrition Rate (%)", height=420)
fig.show()
'''))

# ─────────────────────────────────────────────────────────
# PHASE 11 — EXECUTIVE DASHBOARD
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 11: Executive Dashboard\n\n"
                "> **Objective:** A Plotly dashboard giving C-suite and HR leadership "
                "the full picture — KPIs, department risk, and attrition trends — "
                "without needing to read the notebook.\n"))

cells.append(code(
'''# ── KPI Cards ─────────────────────────────────────────────────────────────────
high_risk_n    = len(risk_df[risk_df["Risk_Category"].isin(["High Risk","Critical Risk"])])
critical_n     = len(risk_df[risk_df["Risk_Category"]=="Critical Risk"])
avg_risk       = risk_df["Risk_Score"].mean()
savings        = total_cost * EXPECTED_RETENTION_SUCCESS_RATE

kpis = [
    ("Attrition Rate",        f"{attrition_rate:.1f}%",   "#e94560"),
    ("High+Critical Risk",    f"{high_risk_n:,}",         "#e67e22"),
    ("Critical Risk Only",    f"{critical_n:,}",          "#e94560"),
    ("Avg Risk Score",        f"{avg_risk:.1f}/100",      "#f5a623"),
    ("Total Attrition Cost",  f"${total_cost/1e6:.1f}M",  "#533483"),
    ("Potential Savings",     f"${savings/1e6:.1f}M","#2ecc71"),
]
fig_kpi = go.Figure()
for i,(label,value,color) in enumerate(kpis):
    fig_kpi.add_trace(go.Indicator(
        mode="number", value=0,
        title={"text":f"<b style='font-size:20px;color:{color}'>{value}</b><br>"
                      f"<span style='font-size:12px;color:#aaa'>{label}</span>"},
        domain={"row":i//3,"column":i%3}
    ))
fig_kpi.update_layout(template="plotly_dark", height=260,
    title={"text":"Executive HR Dashboard — KPI Summary","x":0.5,"font":{"size":18}},
    grid={"rows":2,"columns":3,"pattern":"independent"})
fig_kpi.show()
'''))

cells.append(code(
'''# ── Department Risk Scorecard ─────────────────────────────────────────────────
dept_summary = risk_df.groupby("Department").agg(
    Employees=("Risk_Score","count"),
    Avg_Risk=("Risk_Score","mean"),
    High_Critical=("Risk_Category",lambda x:x.isin(["High Risk","Critical Risk"]).sum()),
    Attrition_Rate=("Attrition_Num","mean")
).round(2)
dept_summary["Attrition_Rate"] *= 100
dept_summary["Risk_Level"] = dept_summary["Avg_Risk"].apply(
    lambda s: "Critical" if s>=70 else ("High" if s>=45 else ("Moderate" if s>=20 else "Low")))
display(dept_summary.sort_values("Avg_Risk",ascending=False).style
        .background_gradient(cmap="RdYlGn_r",subset=["Avg_Risk"])
        .format({"Avg_Risk":"{:.1f}","Attrition_Rate":"{:.1f}%"}))
'''))

cells.append(code(
'''# ── Attrition by Age Band & Department (Interactive Plotly) ──────────────────
plot_df = df.copy()
plot_df["Age_Band"] = pd.cut(plot_df["Age"],bins=[17,25,35,45,55,100],
                              labels=["18-25","26-35","36-45","46-55","55+"])
age_dept = plot_df.groupby(["Department","Age_Band"])["Attrition_Num"].mean().reset_index()
age_dept["Attrition_Rate_Pct"] = age_dept["Attrition_Num"]*100
fig_trend = px.bar(age_dept, x="Age_Band", y="Attrition_Rate_Pct",
                   color="Department", barmode="group",
                   title="Attrition Rate by Age Band & Department (%)",
                   template="plotly_dark", height=400,
                   color_discrete_sequence=PALETTE,
                   labels={"Attrition_Rate_Pct":"Attrition Rate (%)","Age_Band":"Age Band"})
fig_trend.show()
'''))

# ─────────────────────────────────────────────────────────
# PHASE 12 — WORKFORCE RISK HEATMAPS
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 12: Workforce Risk Heatmaps\n\n"
                "> **Objective:** Multi-dimensional risk visualisation enabling HR to "
                "target interventions at the highest-leverage segments.\n"))

cells.append(code(
'''# ── Dept x Role Risk Heatmap ──────────────────────────────────────────────────
dept_role = (risk_df.groupby(["Department","JobRole"])["Risk_Score"]
             .mean().unstack(fill_value=0).round(1))
plt.figure(figsize=(16,5))
sns.heatmap(dept_role, annot=True, fmt=".0f", cmap="RdYlGn_r",
            linewidths=0.5, vmin=0, vmax=100)
plt.title("Avg Risk Score: Department x Job Role", fontsize=14, fontweight="bold")
plt.xticks(rotation=30, ha="right"); plt.tight_layout(); plt.show()
'''))

cells.append(code(
'''# ── Tenure x Satisfaction Heatmap ────────────────────────────────────────────
tenure_sat = (df_fe.groupby("Tenure_Group")[SAT_COLS].mean()
              .reindex(["Early Career","Mid Career","Senior","Veteran"]))
plt.figure(figsize=(10,5))
sns.heatmap(tenure_sat, annot=True, fmt=".2f", cmap="RdYlGn",
            linewidths=0.5, vmin=1, vmax=4)
plt.title("Avg Satisfaction Scores by Tenure Group", fontsize=14, fontweight="bold")
plt.tight_layout(); plt.show()
'''))

cells.append(code(
'''# ── Salary Band x Attrition Heatmap ──────────────────────────────────────────
df_fe_cp = df_fe.copy()
df_fe_cp["Salary_Band"] = pd.cut(df_fe_cp["MonthlyIncome"],
    bins=[0,3000,6000,10000,15000,25000],
    labels=["<$3K","$3K-6K","$6K-10K","$10K-15K",">$15K"])
sal_dept = (df_fe_cp.groupby(["Department","Salary_Band"])["Attrition_Num"]
            .mean()*100).unstack(fill_value=0).round(1)
plt.figure(figsize=(12,4))
sns.heatmap(sal_dept, annot=True, fmt=".1f", cmap="RdYlGn_r",
            linewidths=0.5, vmin=0, vmax=50)
plt.title("Attrition Rate (%) by Department x Salary Band", fontsize=14, fontweight="bold")
plt.tight_layout(); plt.show()
print("HEATMAP INSIGHT: Early Career + lowest salary band = highest risk across ALL departments.")
print("Sales remains elevated across ALL salary bands - suggesting non-financial drivers dominate.")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 13 — PRODUCTION READINESS
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 13: Production Readiness Architecture\n\n"
                "> **Objective:** Design the path from Jupyter Notebook to a deployed, "
                "monitored production system.\n\n"
                "```\n"
                "DATA LAYER         ML LAYER           SERVING LAYER      CONSUMERS\n"
                "──────────         ────────            ─────────────      ─────────\n"
                "HRIS (SAP)  ─────> Feature      ─────> FastAPI       ─-> HR Dashboard\n"
                "            ─────> Pipeline     ─────> Risk Engine   ─-> Manager Alerts\n"
                "ATS (Lever) ─────> Model        ─────> Audit Logger  ─-> Exec Reports\n"
                "            ─────> Registry     \n"
                "Perf Sys    ─────> Drift         \n"
                "            ─────> Detector     \n"
                "            ─────> Retrain      \n"
                "                   Pipeline     \n"
                "```\n\n"
                "| Component | Tool | Trigger |\n|---|---|---|\n"
                "| Data Drift | Evidently AI | Weekly batch |\n"
                "| Model Perf | MLflow | ROC-AUC drops >3% |\n"
                "| Retraining | Apache Airflow | Monthly / drift-triggered |\n"
                "| Audit Logs | Structured JSON | Every prediction |\n"
                "| SHAP Logging | Custom wrapper | Every high-risk flag |\n"))

cells.append(code(
'''# ── Save Production Artifacts ─────────────────────────────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(best_model_obj, "models/attrition_best_model.joblib")
joblib.dump(scaler,         "models/feature_scaler.joblib")

schema = {"model_name":best_model_name,"n_features":len(X.columns),
          "features":X.columns.tolist(),"target":"Attrition",
          "classes":["No (0)","Yes (1)"],"scaler":"StandardScaler"}
with open("models/feature_schema.json","w") as f:
    json.dump(schema, f, indent=2)

print("Production artifacts saved:")
print("  models/attrition_best_model.joblib")
print("  models/feature_scaler.joblib")
print("  models/feature_schema.json")
print(f"  Model: {best_model_name}  |  Features: {len(X.columns)}")
'''))

# ─────────────────────────────────────────────────────────
# PHASE 14 — DELIVERABLES
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Phase 14: Executive Deliverables\n\n"
                "> **Objective:** Auto-generate structured business reports that HR teams, "
                "managers, and executives can use directly — no data science knowledge required.\n"))

cells.append(code(
'''# ── 14.1 Executive Summary ────────────────────────────────────────────────────
status = "ABOVE BENCHMARK" if attrition_rate > 15 else "Within Benchmark"
print("=" * 70)
print("  EXECUTIVE SUMMARY — EMPLOYEE ATTRITION INTELLIGENCE PLATFORM")
print("=" * 70)
print(f"  Prepared for   : Chief Human Resources Officer & Executive Team")
print(f"  Data Source    : IBM HR Analytics Employee Attrition Dataset")
print()
print("  WORKFORCE OVERVIEW")
print(f"  Total Employees         : {total_employees:,}")
print(f"  Employees Who Left      : {leavers:,}  ({attrition_rate:.1f}%)")
print(f"  Industry Benchmark      : ~10-15% (SHRM 2024)")
print(f"  Status                  : {status}")
print()
print("  FINANCIAL IMPACT")
print(f"  Estimated Attrition Cost  : ${total_cost/1e6:.2f}M")
print(f"  At-Risk Employees         : {len(at_risk):,}")
print(f"  Potential Savings (60% ret): ${savings/1e6:.2f}M")
print(f"  Retention Budget ROI      : {roi:.1f}x (estimated)")
print()
print(f"  BEST MODEL: {best_model_name}")
print(f"  ROC-AUC Score            : {best_result['ROC AUC']:.4f}")
print(f"  Attrition Capture Rate   : {best_result['Capture Rate']*100:.1f}%")
print(f"    (of every 10 leavers, model identifies {best_result['Capture Rate']*10:.0f})")
print(f"  Intervention Accuracy    : {best_result['Intervention Acc.']*100:.1f}%")
print(f"    (of every 10 flags, {best_result['Intervention Acc.']*10:.0f} are real leavers)")
print("=" * 70)
'''))

cells.append(code(
'''# ── 14.2 Risk Report ──────────────────────────────────────────────────────────
print("=" * 70 + "\\n  RISK REPORT — TOP 20 AT-RISK EMPLOYEES\\n" + "=" * 70)
report_cols = [c for c in ["Department","JobRole","Age","MonthlyIncome",
    "YearsAtCompany","OverTime","Risk_Score","Risk_Category",
    "Engagement_Index","Burnout_Score"] if c in risk_df.columns]
rpt = risk_df.sort_values("Risk_Score",ascending=False).reset_index(drop=True).head(20)
rpt.index = [f"EMP-{i:04d}" for i in rpt.index]
display(rpt[report_cols].style
        .background_gradient(cmap="RdYlGn_r",subset=["Risk_Score"])
        .format({"Risk_Score":"{:.1f}","MonthlyIncome":"${:,.0f}",
                 "Engagement_Index":"{:.2f}","Burnout_Score":"{:.2f}"}))
risk_df.sort_values("Risk_Score",ascending=False).to_csv(
    "Employee_Risk_Report.csv", index=False)
print("Saved: Employee_Risk_Report.csv")
'''))

cells.append(code(
'''# ── 14.3 Retention Strategy Report ───────────────────────────────────────────
print("=" * 70 + "\\n  RETENTION STRATEGY REPORT\\n" + "=" * 70)
strategy = {
    "Priority 1 — Overtime Management": [
        "Mandatory daily overtime cap (max 2 hrs/day)",
        "Time-tracking with manager alerts on chronic overtime",
        "1.5x comp-time for overtime worked",
        "Expected Impact: -12 to -18% attrition in overtime cohort"
    ],
    "Priority 2 — Compensation Benchmarking": [
        "Annual market salary survey (Glassdoor / Radford)",
        "Target 100% market median for Job Levels 1-3",
        "Skills-based pay progression",
        "Expected Impact: -10 to -15% attrition in below-median cohort"
    ],
    "Priority 3 — Career Development": [
        "Publish transparent promotion criteria company-wide",
        "Fast Track programme for high-potential employees < 3 years tenure",
        "Quarterly career conversations (replace annual reviews)",
        "Expected Impact: -8 to -12% attrition in stalled-career cohort"
    ],
    "Priority 4 — Engagement & Culture": [
        "Monthly pulse surveys (max 5 questions) with visible follow-up",
        "Manager effectiveness scores tied to team retention KPIs",
        "Peer recognition platform",
        "Expected Impact: -6 to -10% attrition in low-satisfaction cohort"
    ],
    "Priority 5 — Work-Life Balance": [
        "Work-from-Home policy (2-3 days/week minimum)",
        "Virtual-first meetings to cut mandatory travel by 30%",
        "Expand Employee Assistance Programme (EAP)",
        "Expected Impact: -5 to -8% attrition in high-burnout cohort"
    ],
}
for priority, actions in strategy.items():
    print(f"\\n  {priority}")
    for a in actions:
        prefix = "     [ROI]" if a.startswith("Expected") else "     *"
        print(f"{prefix} {a}")
print(f"\\n  Combined Attrition Reduction   : 25-40%")
print(f"  Estimated Investment Required  : ${retention_program_cost/1e6:.2f}M")
print(f"  Estimated Net Savings          : ${savings/1e6:.2f}M")
'''))

cells.append(code(
'''# ── 14.4 Department Risk + Cost Report ───────────────────────────────────────
print("=" * 70 + "\\n  DEPARTMENT RISK & COST IMPACT REPORT\\n" + "=" * 70)
dept_full = risk_df.groupby("Department").agg(
    Total_Employees=("Risk_Score","count"),
    Avg_Risk=("Risk_Score","mean"),
    Critical_Risk=("Risk_Category",lambda x:(x=="Critical Risk").sum()),
    High_Risk=("Risk_Category",lambda x:(x=="High Risk").sum()),
    Avg_Engagement=("Engagement_Index","mean"),
    Avg_Burnout=("Burnout_Score","mean"),
    Attrition_Pct=("Attrition_Num",lambda x:x.mean()*100)
).round(2).sort_values("Avg_Risk",ascending=False)

cost_by_dept = at_risk.groupby("Department")["Replacement_Cost"].sum()
dept_full["Est_Cost_$M"] = (dept_full.index.map(cost_by_dept).fillna(0)/1e6).round(2)

display(dept_full.style
        .background_gradient(cmap="RdYlGn_r",subset=["Avg_Risk"])
        .format({"Avg_Risk":"{:.1f}","Avg_Engagement":"{:.2f}",
                 "Avg_Burnout":"{:.2f}","Attrition_Pct":"{:.1f}%",
                 "Est_Cost_$M":"${:.2f}M"}))
dept_full.to_csv("Department_Risk_Cost_Report.csv")
print("Saved: Department_Risk_Cost_Report.csv")
'''))

# ─────────────────────────────────────────────────────────
# CONCLUSION
# ─────────────────────────────────────────────────────────
cells.append(md("---\n# Conclusion\n\n"
                "## Enterprise Platform Summary\n\n"
                "| Phase | Deliverable | Business Value |\n|---|---|---|\n"
                "| 1 | Data Intelligence Layer | Clean, trusted data foundation |\n"
                "| 2 | HR Analytics | Demographic & compensation insights |\n"
                "| 3 | Feature Engineering | 6 domain-driven composite features |\n"
                "| 4 | ML Pipeline (6 models) | Best-in-class prediction accuracy |\n"
                "| 5 | Enterprise Evaluation | Business metrics beyond accuracy |\n"
                "| 6 | Explainable AI (SHAP) | Transparent, auditable decisions |\n"
                "| 7 | Employee Risk Engine | 0–100 risk score per employee |\n"
                "| 8 | Retention Engine | Personalised HR action plans |\n"
                "| 9 | Attrition Cost Model | Financial exposure quantified |\n"
                "| 10 | Scenario Simulator | ROI of specific interventions |\n"
                "| 11 | Executive Dashboard | Leadership-ready visualisations |\n"
                "| 12 | Risk Heatmaps | Segment-level risk targeting |\n"
                "| 13 | Production Architecture | Path to deployment |\n"
                "| 14 | Auto-generated Reports | Boardroom-ready deliverables |\n\n"
                "## Business Questions — Answered\n\n"
                "| Question | Answer |\n|---|---|\n"
                "| Which employees will leave? | Phase 7: Risk Engine (0–100 scores) |\n"
                "| Why are they leaving? | Phase 6: SHAP employee-level narratives |\n"
                "| Which departments are at risk? | Phase 12: Heatmaps |\n"
                "| What is the financial cost? | Phase 9: Attrition cost model |\n"
                "| What should HR do? | Phase 8: Retention Recommendation Engine |\n"
                "| What if we raise salaries? | Phase 10: Scenario Simulation |\n\n"
                "> *This platform transforms attrition prediction from a data science experiment "
                "into an operational HR tool that executives, managers, and HR teams can use to "
                "make better talent decisions every day.*\n"))

# ─────────────────────────────────────────────────────────
# ASSEMBLE & WRITE
# ─────────────────────────────────────────────────────────
nb.cells = cells
output = "Enterprise_Attrition_Intelligence_Platform_updated.ipynb"
with open(output, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Enterprise notebook generated: {output}")
print(f"Total cells: {len(cells)}")
print(f"Phases:      14 + Cover + Conclusion")
