import pandas as pd
from tcia_utils import nbia

df = pd.DataFrame(nbia.getSeries(collection='CMB-OV'))
print(f"Total series: {len(df)}")
print(df['Modality'].value_counts())

df_ct = df[df['Modality'] == 'CT']
print(f"CT series: {len(df_ct)}")

df_ct.to_csv('cmb_ov_ct_series.csv', index=False)

uids = df_ct['SeriesInstanceUID'].tolist()
nbia.downloadSeries(uids, path='data/cmb_ov', input_type="list")

print("CMB-OV download complete.")