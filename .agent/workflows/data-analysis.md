---
description: Data analysis and EDA workflow with pandas, visualization, and statistical analysis
---

# Data Analysis Workflow

## Setup
// turbo
```powershell
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter
```

---

## Initial Exploration

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('data.csv')

# Quick overview
print(f"Shape: {df.shape}")
print(f"\nColumns:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nStatistics:\n{df.describe()}")

# First look
df.head(10)
```

---

## Data Quality Check

```python
# Missing values visualization
plt.figure(figsize=(12, 6))
sns.heatmap(df.isnull(), cbar=True, yticklabels=False)
plt.title('Missing Values Heatmap')

# Duplicates
print(f"Duplicates: {df.duplicated().sum()}")

# Unique values per column
for col in df.columns:
    print(f"{col}: {df[col].nunique()} unique values")
```

---

## Univariate Analysis

```python
# Numerical distributions
numerical_cols = df.select_dtypes(include=[np.number]).columns

fig, axes = plt.subplots(len(numerical_cols), 2, figsize=(12, 4*len(numerical_cols)))
for i, col in enumerate(numerical_cols):
    # Histogram
    axes[i, 0].hist(df[col].dropna(), bins=30, edgecolor='black')
    axes[i, 0].set_title(f'{col} Distribution')
    
    # Box plot
    axes[i, 1].boxplot(df[col].dropna())
    axes[i, 1].set_title(f'{col} Box Plot')

plt.tight_layout()

# Categorical counts
categorical_cols = df.select_dtypes(include=['object', 'category']).columns
for col in categorical_cols:
    print(f"\n{col}:\n{df[col].value_counts()}")
```

---

## Bivariate Analysis

```python
# Correlation matrix
plt.figure(figsize=(10, 8))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0, fmt='.2f')
plt.title('Correlation Matrix')

# Scatter plots for top correlations
# Pairplot for key variables
sns.pairplot(df[['var1', 'var2', 'var3', 'target']], hue='target')

# Categorical vs numerical
for cat_col in categorical_cols[:3]:
    for num_col in numerical_cols[:3]:
        plt.figure(figsize=(10, 4))
        sns.boxplot(x=cat_col, y=num_col, data=df)
        plt.xticks(rotation=45)
        plt.title(f'{num_col} by {cat_col}')
```

---

## Statistical Tests

```python
from scipy import stats

# T-test (compare two groups)
group1 = df[df['category'] == 'A']['value']
group2 = df[df['category'] == 'B']['value']
t_stat, p_value = stats.ttest_ind(group1, group2)
print(f"T-test p-value: {p_value:.4f}")

# Chi-square (categorical association)
contingency = pd.crosstab(df['cat1'], df['cat2'])
chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
print(f"Chi-square p-value: {p_value:.4f}")

# Correlation significance
r, p = stats.pearsonr(df['var1'], df['var2'])
print(f"Pearson r={r:.3f}, p={p:.4f}")
```

---

## Feature Engineering Ideas

```python
# Date features
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.dayofweek
df['is_weekend'] = df['day_of_week'].isin([5, 6])

# Bins
df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100], 
                         labels=['child', 'young', 'middle', 'senior', 'elderly'])

# Aggregations
df['user_avg_spend'] = df.groupby('user_id')['amount'].transform('mean')

# Interactions
df['price_per_unit'] = df['total_price'] / df['quantity']
```

---

## Export Findings

```python
# Save cleaned data
df.to_csv('cleaned_data.csv', index=False)

# Save figures
plt.savefig('analysis_figures.png', dpi=150, bbox_inches='tight')

# Generate report
summary = {
    'total_records': len(df),
    'features': len(df.columns),
    'missing_pct': df.isnull().mean().to_dict(),
    'correlations': df.corr()['target'].sort_values().to_dict()
}
```
