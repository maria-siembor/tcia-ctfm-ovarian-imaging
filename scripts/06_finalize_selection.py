import pandas as pd

selected = pd.read_csv('data/series_lists/tcga_ov_stage_a_selected.csv')
flagged_ids = ['TCGA-10-0934', 'TCGA-10-0936', 'TCGA-25-2393', 'TCGA-61-1737', 'TCGA-61-2016', 'TCGA-61-1998']

final = selected[~selected['PatientID'].isin(flagged_ids)]
final.to_csv('data/series_lists/tcga_ov_final_selected.csv', index=False)

print(f"Excluded {len(flagged_ids)} patients with major spacing gaps.")
print(f"Final selection: {len(final)} patients.")