"""
Series selection, Stage B: DICOM header inspection.
Reads SliceThickness + ImageOrientationPatient from one representative file
per Stage A-selected series. Checks real distributions before deciding any
exclusion cutoff, same approach as Stage A.
"""

import os
import pandas as pd
import pydicom


def inspect_headers(dataset_slug: str):
    df = pd.read_csv(f"data/series_lists/{dataset_slug}_stage_a_selected.csv")
    data_dir = f"data/raw/{dataset_slug}" if os.path.exists(f"data/raw/{dataset_slug}") else f"data/{dataset_slug}"

    records = []
    for _, row in df.iterrows():
        uid = row['SeriesInstanceUID']
        folder = os.path.join(data_dir, uid)
        if not os.path.isdir(folder):
            records.append({'PatientID': row['PatientID'], 'SeriesInstanceUID': uid,
                             'SliceThickness': None, 'Orientation': None, 'error': 'folder not found'})
            continue

        dcm_files = [f for f in os.listdir(folder) if f.endswith('.dcm')]
        if not dcm_files:
            records.append({'PatientID': row['PatientID'], 'SeriesInstanceUID': uid,
                             'SliceThickness': None, 'Orientation': None, 'error': 'no dcm files'})
            continue

        ds = pydicom.dcmread(os.path.join(folder, dcm_files[0]), stop_before_pixels=True)
        slice_thickness = getattr(ds, 'SliceThickness', None)
        orientation = getattr(ds, 'ImageOrientationPatient', None)

        records.append({
            'PatientID': row['PatientID'],
            'SeriesInstanceUID': uid,
            'SliceThickness': float(slice_thickness) if slice_thickness else None,
            'Orientation': list(orientation) if orientation else None,
            'error': None,
        })

    result = pd.DataFrame(records)
    out_path = f"data/series_lists/{dataset_slug}_stage_b_headers.csv"
    result.to_csv(out_path, index=False)
    print(f"[{dataset_slug}] Inspected {len(result)} series, saved to {out_path}")
    print(result['SliceThickness'].describe())
    print(f"Errors: {result['error'].notna().sum()}")
    return result