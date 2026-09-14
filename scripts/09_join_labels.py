import sys
sys.path.append("src")

from data.labels import download_clovar_labels, join_with_selected_patients

download_clovar_labels()
join_with_selected_patients(dataset_slug="tcga_ov")