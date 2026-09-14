import numpy as np
import glob
from sklearn.metrics.pairwise import cosine_similarity

tcga_files = sorted(glob.glob('outputs/embeddings/tcga_ov/*.npy'))
X_tcga = np.array([np.load(f) for f in tcga_files])

sims = cosine_similarity(X_tcga)
np.fill_diagonal(sims, np.nan)

print(f"TCGA-OV internal nearest-neighbor similarity (baseline):")
nearest_sims = np.nanmax(sims, axis=1)
print(f"  mean: {np.mean(nearest_sims):.3f}, min: {np.min(nearest_sims):.3f}, max: {np.max(nearest_sims):.3f}")

print(f"\nTCGA-OV overall pairwise similarity (any two random patients):")
all_sims = sims[~np.isnan(sims)]
print(f"  mean: {np.mean(all_sims):.3f}, std: {np.std(all_sims):.3f}")