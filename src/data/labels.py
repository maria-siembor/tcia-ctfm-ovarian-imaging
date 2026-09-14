"""Download and join CLOVAR subtype labels from TCGA-OV-Radiogenomics."""

import os
import requests
import pandas as pd

CLOVAR_URL = "https://www.cancerimagingarchive.net/wp-content/uploads/CLOVARScores121715.csv"


def download_clovar_labels(out_dir: str = "data/labels"):
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "clovar_scores.csv")

    resp = requests.get(CLOVAR_URL)
    resp.raise_for_status()
    with open(out_path, 'wb') as f:
        f.write(resp.content)

    df = pd.read_csv(out_path)
    df = df.rename(columns={df.columns[0]: 'PatientID'})
    print(f"Downloaded {len(df)} patients with CLOVAR labels to {out_path}")
    return df


def get_hard_label(row):
    """Convert the 4 boolean category columns into a single subtype label."""
    categories = ['Differentiated', 'Immunoreactive', 'Mesenchymal', 'Proliferative']
    for cat in categories:
        col = f'{cat}Category'
        if str(row[col]).strip().upper() == 'TRUE':
            return cat
    return None  # ambiguous / ties with the released category columns


def join_with_selected_patients(dataset_slug: str = "tcga_ov"):
    labels = pd.read_csv("data/labels/clovar_scores.csv")
    labels = labels.rename(columns={labels.columns[0]: 'PatientID'})
    labels['subtype'] = labels.apply(get_hard_label, axis=1)

    selected = pd.read_csv(f"data/series_lists/{dataset_slug}_final_selected.csv")

    merged = selected.merge(labels[['PatientID', 'subtype']], on='PatientID', how='left')

    n_with_label = merged['subtype'].notna().sum()
    print(f"{n_with_label}/{len(merged)} selected patients have a CLOVAR label")
    print(merged['subtype'].value_counts(dropna=False))

    out_path = f"data/series_lists/{dataset_slug}_with_clovar_labels.csv"
    merged.to_csv(out_path, index=False)
    print(f"Saved to {out_path}")
    return merged