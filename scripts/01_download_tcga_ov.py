import pandas as pd
from tcia_utils import nbia

df = pd.DataFrame(nbia.getSeries(collection='TCGA-OV'))
print(f"Total series: {len(df)}")
print(df['Modality'].value_counts())

df_ct = df[df['Modality'] == 'CT']
print(f"CT series: {len(df_ct)}")

df_ct.to_csv('tcga_ov_ct_series.csv', index=False)

uids = df_ct['SeriesInstanceUID'].tolist()
nbia.downloadSeries(uids, path='data', input_type="list")

print("Download complete.")