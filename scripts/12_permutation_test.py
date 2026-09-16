import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

df = pd.read_csv('data/series_lists/tcga_ov_with_clovar_labels.csv')
df = df.dropna(subset=['subtype'])

X = np.array([np.load(f"outputs/embeddings/tcga_ov/{pid}.npy") for pid in df['PatientID']])
y = np.array(df['subtype'])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
pipe = Pipeline([
    ('scale', StandardScaler()),
    ('pca', PCA(n_components=5)),
    ('clf', SVC(kernel='linear', C=0.1))
])

real_score = cross_val_score(pipe, X, y, cv=cv, scoring='accuracy').mean()
print(f"Real accuracy: {real_score:.3f}")

# Permutation test: shuffle labels 200 times, rerun CV each time
n_permutations = 200
perm_scores = []
rng = np.random.RandomState(42)

for i in range(n_permutations):
    y_shuffled = rng.permutation(y)
    score = cross_val_score(pipe, X, y_shuffled, cv=cv, scoring='accuracy').mean()
    perm_scores.append(score)
    if (i + 1) % 50 == 0:
        print(f"  ...{i+1}/{n_permutations} permutations done")

perm_scores = np.array(perm_scores)
p_value = (perm_scores >= real_score).sum() / n_permutations

print(f"\nPermutation scores: mean={perm_scores.mean():.3f}, std={perm_scores.std():.3f}")
print(f"Fraction of random shuffles reaching >= {real_score:.3f}: {p_value:.3f}")
print(f"(This is an empirical p-value: lower = more evidence the real result isn't just luck)")
