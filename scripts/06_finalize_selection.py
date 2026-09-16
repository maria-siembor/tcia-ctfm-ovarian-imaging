import pandas as pd

NONUNIFORMITY_THRESHOLD = 20 

selected = pd.read_csv('data/series_lists/tcga_ov_stage_a_selected.csv')
conversion_log = pd.read_csv('data/series_lists/tcga_ov_conversion_log.csv')

flagged_ids = conversion_log.loc[
    conversion_log['itk_nonuniformity'].fillna(0) > NONUNIFORMITY_THRESHOLD, 'PatientID'
].tolist()

final = selected[~selected['PatientID'].isin(flagged_ids)]
final.to_csv('data/series_lists/tcga_ov_final_selected.csv', index=False)

print(f"Excluded {len(flagged_ids)} patients with ITK nonuniformity > {NONUNIFORMITY_THRESHOLD} "
      f"(major inter-slice spacing gaps): {flagged_ids}")
print(f"Final selection: {len(final)} patients.")
