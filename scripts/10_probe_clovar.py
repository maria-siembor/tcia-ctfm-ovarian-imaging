import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('data/series_lists/tcga_ov_with_clovar_labels.csv')
df = df.dropna(subset=['subtype'])
print(f"Patients with labels: {len(df)}")

X = []
y = []
for _, row in df.iterrows():
    emb_path = f"outputs/embeddings/tcga_ov/{row['PatientID']}.npy"
    X.append(np.load(emb_path))
    y.append(row['subtype'])

X = np.array(X)
y = np.array(y)
print(f"X shape: {X.shape}, classes: {np.unique(y, return_counts=True)}")

X_scaled = StandardScaler().fit_transform(X)

clf = LogisticRegression(max_iter=1000)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

scores = cross_val_score(clf, X_scaled, y, cv=cv, scoring='accuracy')
print(f"5-fold CV accuracy: {scores.mean():.3f} +/- {scores.std():.3f}")
print(f"Per-fold scores: {scores}")

# baseline: what a random/majority-class guesser would get
from collections import Counter
majority_baseline = max(Counter(y).values()) / len(y)
print(f"Majority-class baseline: {majority_baseline:.3f}")