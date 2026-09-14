import numpy as np
import pandas as pd
import shap
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

df = pd.read_csv('data/series_lists/tcga_ov_with_clovar_labels.csv')
df = df.dropna(subset=['subtype'])

X = np.array([np.load(f"outputs/embeddings/tcga_ov/{pid}.npy") for pid in df['PatientID']])
y = np.array(df['subtype'])

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA(n_components=5)
X_pca = pca.fit_transform(X_scaled)

clf = SVC(kernel='linear', C=0.1, probability=True)
clf.fit(X_pca, y)

explainer = shap.KernelExplainer(clf.predict_proba, X_pca)
shap_values = explainer.shap_values(X_pca)

print("SHAP values shape:", np.array(shap_values).shape)
print("\nMean |SHAP value| per PCA component, per class:")
classes = clf.classes_
for i, cls in enumerate(classes):
    importances = np.abs(shap_values[:, :, i]).mean(axis=0)
    print(f"\n{cls}:")
    for j, imp in enumerate(importances):
        print(f"  PC{j+1}: {imp:.4f}")

np.save('outputs/embeddings/tcga_ov_shap_values.npy', shap_values)
print("\nSaved SHAP values to outputs/embeddings/tcga_ov_shap_values.npy")