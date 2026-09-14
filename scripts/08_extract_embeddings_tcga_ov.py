import sys
import os
import time
import numpy as np
import pandas as pd
sys.path.append("src")

from models.ctfm_wrapper import embed

df = pd.read_csv('data/series_lists/tcga_ov_final_selected.csv')
nifti_dir = 'data/nifti/tcga_ov'
out_dir = 'outputs/embeddings/tcga_ov'
os.makedirs(out_dir, exist_ok=True)

results = []
for i, row in df.iterrows():
    patient_id = row['PatientID']
    nifti_path = os.path.join(nifti_dir, f"{patient_id}.nii.gz")

    if not os.path.exists(nifti_path):
        print(f"MISSING: {patient_id}")
        continue

    start = time.time()
    try:
        vec = embed(nifti_path)
        np.save(os.path.join(out_dir, f"{patient_id}.npy"), vec)
        elapsed = time.time() - start
        results.append({'PatientID': patient_id, 'status': 'ok', 'seconds': elapsed})
        print(f"[{i+1}/{len(df)}] {patient_id}: {elapsed:.1f}s")
    except Exception as e:
        results.append({'PatientID': patient_id, 'status': f'error: {e}', 'seconds': None})
        print(f"[{i+1}/{len(df)}] {patient_id}: ERROR {e}")

    if (i + 1) % 5 == 0:
        pd.DataFrame(results).to_csv('data/series_lists/tcga_ov_embedding_log.csv', index=False)

pd.DataFrame(results).to_csv('data/series_lists/tcga_ov_embedding_log.csv', index=False)
print(pd.DataFrame(results)['status'].apply(lambda x: x.split(':')[0]).value_counts())