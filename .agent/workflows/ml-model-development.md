---
description: End-to-end machine learning model development workflow from data to deployment
---

# ML Model Development Workflow

## Phase 1: Problem Definition & Data Understanding

### 1.1 Define the Problem
- [ ] Clearly state the business/research objective
- [ ] Identify the type of problem (classification, regression, clustering, etc.)
- [ ] Define success metrics (ROC-AUC, RMSE, F1, etc.)
- [ ] Set baseline performance targets

### 1.2 Data Inventory
// turbo
```python
import pandas as pd
import numpy as np

# Load and inspect data
df = pd.read_csv('data/train.csv')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"Dtypes:\n{df.dtypes}")
print(f"Missing values:\n{df.isnull().sum()}")
print(f"Target distribution:\n{df['target'].value_counts(normalize=True)}")
```

---

## Phase 2: Exploratory Data Analysis (EDA)

### 2.1 Statistical Summary
```python
# Numerical features
df.describe()

# Categorical features
df.describe(include='object')

# Correlation matrix
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 8))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0)
plt.title('Feature Correlation Matrix')
plt.tight_layout()
plt.savefig('outputs/correlation_matrix.png', dpi=150)
```

### 2.2 Distribution Analysis
```python
# Target vs features
for col in numerical_cols:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Distribution
    sns.histplot(df[col], kde=True, ax=axes[0])
    axes[0].set_title(f'{col} Distribution')
    
    # Box plot by target
    sns.boxplot(x='target', y=col, data=df, ax=axes[1])
    axes[1].set_title(f'{col} by Target')
    
    plt.tight_layout()
    plt.savefig(f'outputs/dist_{col}.png', dpi=150)
```

### 2.3 Missing Value Analysis
```python
import missingno as msno

msno.matrix(df)
plt.savefig('outputs/missing_matrix.png', dpi=150)

# Missing value patterns
msno.heatmap(df)
plt.savefig('outputs/missing_heatmap.png', dpi=150)
```

---

## Phase 3: Feature Engineering

### 3.1 Standard Transformations
```python
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer

# Numerical imputation
num_imputer = SimpleImputer(strategy='median')
df[numerical_cols] = num_imputer.fit_transform(df[numerical_cols])

# Categorical imputation
cat_imputer = SimpleImputer(strategy='most_frequent')
df[categorical_cols] = cat_imputer.fit_transform(df[categorical_cols])

# Scaling
scaler = StandardScaler()
df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
```

### 3.2 Advanced Feature Engineering
```python
# Interaction features
for i, col1 in enumerate(numerical_cols):
    for col2 in numerical_cols[i+1:]:
        df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
        df[f'{col1}_div_{col2}'] = df[col1] / (df[col2] + 1e-8)

# Aggregation features
for col in categorical_cols:
    for num_col in numerical_cols:
        df[f'{col}_{num_col}_mean'] = df.groupby(col)[num_col].transform('mean')
        df[f'{col}_{num_col}_std'] = df.groupby(col)[num_col].transform('std')

# Polynomial features (careful with dimensionality!)
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, include_bias=False)
poly_features = poly.fit_transform(df[top_features])

# Binning
df['age_bin'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100], labels=['child', 'young', 'middle', 'senior', 'elderly'])
```

### 3.3 Target Encoding (for high-cardinality categoricals)
```python
from sklearn.model_selection import KFold

def target_encode(df, col, target, n_splits=5):
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    df[f'{col}_target_enc'] = np.nan
    
    for train_idx, val_idx in kf.split(df):
        means = df.iloc[train_idx].groupby(col)[target].mean()
        df.loc[df.index[val_idx], f'{col}_target_enc'] = df.iloc[val_idx][col].map(means)
    
    # Fill NaN with global mean
    df[f'{col}_target_enc'].fillna(df[target].mean(), inplace=True)
    return df
```

---

## Phase 4: Model Training

### 4.1 Train/Validation Split
```python
from sklearn.model_selection import train_test_split, StratifiedKFold

X = df.drop('target', axis=1)
y = df['target']

X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

### 4.2 Baseline Models
```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, classification_report

models = {
    'LogisticRegression': LogisticRegression(max_iter=1000),
    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
    'GradientBoosting': GradientBoostingClassifier(random_state=42)
}

for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    score = roc_auc_score(y_val, y_pred_proba)
    print(f"{name}: ROC-AUC = {score:.4f}")
```

### 4.3 Advanced Models (XGBoost, LightGBM, CatBoost)
```python
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

# XGBoost
xgb_model = xgb.XGBClassifier(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    early_stopping_rounds=50,
    eval_metric='auc'
)
xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=100)

# LightGBM
lgb_model = lgb.LGBMClassifier(
    n_estimators=1000,
    learning_rate=0.05,
    num_leaves=31,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42
)
lgb_model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
)

# CatBoost
cat_model = CatBoostClassifier(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    random_state=42,
    early_stopping_rounds=50,
    verbose=100
)
cat_model.fit(X_train, y_train, eval_set=(X_val, y_val))
```

---

## Phase 5: Hyperparameter Optimization

### 5.1 Optuna Optimization
```python
import optuna
from optuna.integration import LightGBMPruningCallback

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 2000),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'max_depth': trial.suggest_int('max_depth', 3, 12),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        'random_state': 42
    }
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = []
    
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_vl = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_vl = y.iloc[train_idx], y.iloc[val_idx]
        
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_vl, y_vl)],
            callbacks=[
                lgb.early_stopping(50),
                LightGBMPruningCallback(trial, 'auc')
            ]
        )
        
        y_pred = model.predict_proba(X_vl)[:, 1]
        scores.append(roc_auc_score(y_vl, y_pred))
    
    return np.mean(scores)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100, show_progress_bar=True)

print(f"Best score: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")
```

---

## Phase 6: Model Ensembling

### 6.1 Weighted Averaging
```python
# Get predictions from multiple models
preds_xgb = xgb_model.predict_proba(X_val)[:, 1]
preds_lgb = lgb_model.predict_proba(X_val)[:, 1]
preds_cat = cat_model.predict_proba(X_val)[:, 1]

# Simple average
ensemble_avg = (preds_xgb + preds_lgb + preds_cat) / 3

# Weighted average (optimize weights)
from scipy.optimize import minimize

def objective(weights):
    final_pred = weights[0] * preds_xgb + weights[1] * preds_lgb + weights[2] * preds_cat
    return -roc_auc_score(y_val, final_pred)

result = minimize(objective, [1/3, 1/3, 1/3], method='Nelder-Mead')
optimal_weights = result.x / result.x.sum()
print(f"Optimal weights: {optimal_weights}")
```

### 6.2 Stacking
```python
from sklearn.ensemble import StackingClassifier

estimators = [
    ('xgb', xgb_model),
    ('lgb', lgb_model),
    ('cat', cat_model)
]

stacking = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(),
    cv=5,
    passthrough=False
)
stacking.fit(X_train, y_train)
```

---

## Phase 7: Model Evaluation & Interpretation

### 7.1 Comprehensive Evaluation
```python
from sklearn.metrics import (
    classification_report, confusion_matrix, 
    roc_curve, precision_recall_curve, average_precision_score
)

y_pred = model.predict(X_val)
y_pred_proba = model.predict_proba(X_val)[:, 1]

print(classification_report(y_val, y_pred))

# ROC Curve
fpr, tpr, _ = roc_curve(y_val, y_pred_proba)
plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, label=f'ROC-AUC: {roc_auc_score(y_val, y_pred_proba):.4f}')
plt.plot([0, 1], [0, 1], 'k--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.savefig('outputs/roc_curve.png', dpi=150)
```

### 7.2 Feature Importance
```python
# Built-in importance
importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

plt.figure(figsize=(10, 8))
sns.barplot(x='importance', y='feature', data=importance.head(20))
plt.title('Top 20 Feature Importances')
plt.tight_layout()
plt.savefig('outputs/feature_importance.png', dpi=150)

# SHAP values (more interpretable)
import shap

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_val)

shap.summary_plot(shap_values, X_val, show=False)
plt.savefig('outputs/shap_summary.png', dpi=150, bbox_inches='tight')
```

---

## Phase 8: Final Submission / Deployment

### 8.1 Generate Predictions
```python
# Load test data
test = pd.read_csv('data/test.csv')

# Apply same preprocessing (use saved transformers!)
test_processed = preprocess(test)

# Make predictions
predictions = model.predict_proba(test_processed)[:, 1]

# Create submission
submission = pd.DataFrame({
    'id': test['id'],
    'target': predictions
})
submission.to_csv('submission.csv', index=False)
print(f"Submission shape: {submission.shape}")
```

### 8.2 Save Model Artifacts
```python
import joblib
import json

# Save model
joblib.dump(model, 'models/final_model.joblib')

# Save preprocessing artifacts
artifacts = {
    'scaler': scaler,
    'imputer': imputer,
    'label_encoders': label_encoders,
    'feature_names': list(X.columns)
}
joblib.dump(artifacts, 'models/preprocessing_artifacts.joblib')

# Save metadata
metadata = {
    'model_type': type(model).__name__,
    'validation_score': float(val_score),
    'features_count': len(X.columns),
    'training_date': str(pd.Timestamp.now())
}
with open('models/model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)
```

---

## Quick Reference: Essential Imports

```python
# Data
import pandas as pd
import numpy as np

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# ML
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix

# Advanced models
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

# Hyperparameter optimization
import optuna

# Model interpretation
import shap
```
