import sys
sys.path.append("src")

from data.series_selection import select_series_stage_a

selected = select_series_stage_a(dataset_slug="tcga_ov")
print(selected[['PatientID', 'SeriesDescription', 'ImageCount']].head(20).to_string())