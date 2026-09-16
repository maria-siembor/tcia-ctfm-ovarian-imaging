"""DICOM series -> NIfTI conversion, one file per selected series."""

import os
import sys
import tempfile
import contextlib
import pandas as pd
import SimpleITK as sitk


@contextlib.contextmanager
def capture_c_stderr():
    stderr_fd = sys.stderr.fileno()
    saved_stderr_fd = os.dup(stderr_fd)
    tmp = tempfile.TemporaryFile(mode='w+')
    os.dup2(tmp.fileno(), stderr_fd)
    try:
        yield tmp
    finally:
        os.dup2(saved_stderr_fd, stderr_fd)
        os.close(saved_stderr_fd)


def convert_series(dataset_slug: str, limit: int = None):
    df = pd.read_csv(f"data/series_lists/{dataset_slug}_stage_a_selected.csv")
    if limit:
        df = df.head(limit)

    data_dir = f"data/raw/{dataset_slug}" if os.path.exists(f"data/raw/{dataset_slug}") else f"data/{dataset_slug}"
    out_dir = f"data/nifti/{dataset_slug}"
    os.makedirs(out_dir, exist_ok=True)

    reader = sitk.ImageSeriesReader()
    results = []
    log_path = f"data/series_lists/{dataset_slug}_conversion_log.csv"

    for i, (_, row) in enumerate(df.iterrows()):
        uid = row['SeriesInstanceUID']
        patient_id = row['PatientID']
        series_folder = os.path.join(data_dir, uid)
        out_path = os.path.join(out_dir, f"{patient_id}.nii.gz")

        try:
            dicom_files = reader.GetGDCMSeriesFileNames(series_folder)
            reader.SetFileNames(dicom_files)

            with capture_c_stderr() as tmp:
                image = reader.Execute()
                tmp.seek(0)
                warning_text = tmp.read()

            nonuniformity = None
            if 'nonuniformity' in warning_text.lower():
                try:
                    last_line = [l for l in warning_text.splitlines() if 'nonuniformity' in l.lower()][-1]
                    nonuniformity = float(last_line.strip().split(':')[-1])
                except (ValueError, IndexError):
                    nonuniformity = -1

            sitk.WriteImage(image, out_path)
            results.append({
                'PatientID': patient_id,
                'status': 'ok',
                'size': image.GetSize(),
                'itk_nonuniformity': nonuniformity,
            })
        except Exception as e:
            results.append({'PatientID': patient_id, 'status': f'error: {e}', 'size': None,
                             'itk_nonuniformity': None})

        if (i + 1) % 10 == 0:
            pd.DataFrame(results).to_csv(log_path, index=False)
            print(f"  ...progress saved at {i + 1}/{len(df)}")

    result_df = pd.DataFrame(results)
    result_df.to_csv(log_path, index=False)

    print(result_df['status'].apply(lambda x: x.split(':')[0]).value_counts())
    flagged = result_df[result_df['itk_nonuniformity'].fillna(0) > 20]
    print(f"Flagged (ITK nonuniformity > 20): {len(flagged)}")
    if len(flagged) > 0:
        print(flagged[['PatientID', 'itk_nonuniformity']].sort_values('itk_nonuniformity', ascending=False))

    return result_df
