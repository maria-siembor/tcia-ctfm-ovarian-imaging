import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from collections import Counter

df = pd.read_csv('data/series_lists/tcga_ov_with_clovar_labels.csv')
df = df.dropna(subset=['subtype'])

X = np.array([np.load(f"outputs/embeddings/tcga_ov/{pid}.npy") for pid in df['PatientID']])
y = np.array(df['subtype'])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
majority_baseline = max(Counter(y).values()) / len(y)
print(f"Majority-class baseline: {majority_baseline:.3f}\n")

# Try a range of regularization strengths (lower C = stronger regularization)
for C in [0.001, 0.01, 0.1, 1.0]:
    pipe = Pipeline([
        ('scale', StandardScaler()),
        ('clf', LogisticRegression(max_iter=1000, C=C))
    ])
    scores = cross_val_score(pipe, X, y, cv=cv, scoring='accuracy')
    print(f"C={C}: accuracy {scores.mean():.3f} +/- {scores.std():.3f}")

print()

# Try PCA dimensionality reduction before classifying
for n_components in [5, 10, 20, 30]:
    pipe = Pipeline([
        ('scale', StandardScaler()),
        ('pca', PCA(n_components=n_components)),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    scores = cross_val_score(pipe, X, y, cv=cv, scoring='accuracy')
    print(f"PCA n={n_components}: accuracy {scores.mean():.3f} +/- {scores.std():.3f}")