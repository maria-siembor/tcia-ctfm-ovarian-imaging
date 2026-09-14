import sys
sys.path.append("src")

from data.series_selection import select_series_stage_a

selected = select_series_stage_a(dataset_slug="cmb_ov", require_body_part_contains=['PELVIS'])
print(selected[['PatientID', 'SeriesDescription', 'ImageCount']].to_string())