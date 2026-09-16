import sys
sys.path.append("src")

from data.dicom_to_nifti import convert_series

convert_series(dataset_slug="tcga_ov")  # no limit, all 136