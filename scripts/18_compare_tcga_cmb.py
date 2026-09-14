import numpy as np
import pandas as pd
import glob
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity

tcga_files = sorted(glob.glob('outputs/embeddings/tcga_ov/*.npy'))
cmb_files = sorted(glob.glob('outputs/embeddings/cmb_ov/*.npy'))

tcga_ids = [f.split('/')[-1].split('\\')[-1].replace('.npy', '') for f in tcga_files]
cmb_ids = [f.split('/')[-1].split('\\')[-1].replace('.npy', '') for f in cmb_files]

X_tcga = np.array([np.load(f) for f in tcga_files])
X_cmb = np.array([np.load(f) for f in cmb_files])

print(f"TCGA-OV: {X_tcga.shape}, CMB-OV: {X_cmb.shape}")

X_all = np.vstack([X_tcga, X_cmb])
labels = ['TCGA-OV'] * len(X_tcga) + ['CMB-OV'] * len(X_cmb)

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_all)

print(f"PCA explained variance: {pca.explained_variance_ratio_}")

tcga_pca = X_pca[:len(X_tcga)]
cmb_pca = X_pca[len(X_tcga):]

pd.DataFrame({'PC1': tcga_pca[:, 0], 'PC2': tcga_pca[:, 1], 'dataset': 'TCGA-OV', 'PatientID': tcga_ids}).to_csv(
    'outputs/embeddings/pca_comparison.csv', index=False)
pd.DataFrame({'PC1': cmb_pca[:, 0], 'PC2': cmb_pca[:, 1], 'dataset': 'CMB-OV', 'PatientID': cmb_ids}).to_csv(
    'outputs/embeddings/pca_comparison_cmb.csv', index=False)

tcga_centroid = X_tcga.mean(axis=0)
cmb_centroid = X_cmb.mean(axis=0)
centroid_distance = np.linalg.norm(tcga_centroid - cmb_centroid)
tcga_spread = np.mean(np.linalg.norm(X_tcga - tcga_centroid, axis=1))
cmb_spread = np.mean(np.linalg.norm(X_cmb - cmb_centroid, axis=1))

print(f"\nTCGA-OV centroid spread (avg distance to centroid): {tcga_spread:.2f}")
print(f"CMB-OV centroid spread: {cmb_spread:.2f}")
print(f"Distance between TCGA-OV and CMB-OV centroids: {centroid_distance:.2f}")

sims = cosine_similarity(X_cmb, X_tcga)
print("\nNearest TCGA-OV neighbor for each CMB-OV patient:")
for i, cmb_id in enumerate(cmb_ids):
    best_idx = sims[i].argmax()
    print(f"  {cmb_id} -> {tcga_ids[best_idx]} (cosine sim: {sims[i][best_idx]:.3f})")