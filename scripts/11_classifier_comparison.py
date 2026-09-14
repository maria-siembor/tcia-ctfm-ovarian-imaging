import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
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
print(f"N={len(y)}, majority-class baseline: {majority_baseline:.3f}\n")

models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, C=0.1),
    'Linear SVM': SVC(kernel='linear', C=0.1),
    'RBF SVM': SVC(kernel='rbf', C=1.0, gamma='scale'),
    'Random Forest (shallow)': RandomForestClassifier(n_estimators=100, max_depth=3, random_state=42),
    'Small MLP': MLPClassifier(hidden_layer_sizes=(16,), alpha=1.0, max_iter=2000, random_state=42),
}

for name, clf in models.items():
    pipe = Pipeline([
        ('scale', StandardScaler()),
        ('pca', PCA(n_components=5)),
        ('clf', clf)
    ])
    scores = cross_val_score(pipe, X, y, cv=cv, scoring='accuracy')
    print(f"{name}: {scores.mean():.3f} +/- {scores.std():.3f}")