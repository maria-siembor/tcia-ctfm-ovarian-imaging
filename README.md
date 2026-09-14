# CT-FM Zero-Shot and Adapted Evaluation on Ovarian Cancer CT

Testing whether CT-FM (Pai et al. 2025), a self-supervised 3D CT foundation
model, produces embeddings useful for predicting ovarian cancer molecular
subtype (CLOVAR), and whether it generalizes to imaging data outside its
own pretraining set.

## Background

CT-FM was pretrained on 148,000 CT scans from the Imaging Data Commons,
including the TCGA-OV collection used here (label-free, pixel-level
exposure only, confirmed via the paper's own Supplementary Table S5). To
separate "familiar data" from genuine generalization, this project uses
two datasets:

- **TCGA-OV** (143 patients): pretraining-exposed. Used for development,
  validation, and the labeled CLOVAR subtype benchmark.
- **CMB-OV** (19 patients): NOT in CT-FM's pretraining data. Used as a
  held-out qualitative generalization check.

## Pipeline

1. Download from TCIA (`tcia_utils`)
2. Series selection: metadata filtering (Rich et al. 2026 methodology) +
   geometric validation (orientation, slice spacing) — see
   `SERIES_SELECTION_LOG.md` for the full, evidence-based process,
   including real bugs found and fixed during development
3. DICOM → NIfTI conversion
4. CT-FM embedding extraction (`lighter_zoo`, 512-dim vectors)
5. CLOVAR subtype labels joined from TCGA-OV-Radiogenomics
6. Zero-shot linear probe, classifier comparison, permutation testing,
   SHAP interpretability — see `RESULTS_LOG.md` for full results

## Key results

- **Zero-shot linear probe**: below majority-class baseline. Contextualized
  against Vargas et al. 2017, who also found only a narrow association
  (one of four subtypes) using radiologist-read features, suggesting
  CLOVAR subtype may not be strongly visible in CT imaging at all, not a
  CT-FM-specific failure.
- **Best classifier (Linear SVM)**: 35.1% vs. 29.7% baseline, but
  permutation testing gives p=0.08, suggestive, not robust after
  accounting for testing 5 classifier types.
- **CMB-OV generalization**: embeddings from data CT-FM never saw fall
  within TCGA-OV's normal variation (centroid distance smaller than
  either dataset's internal spread), a modest positive signal, appropriately
  scoped given n=6 and no available labels.

Full methodology, every debugging decision, and literature citations are
in `SERIES_SELECTION_LOG.md` and `RESULTS_LOG.md`.

## Data availability

Raw imaging data is not redistributed here. TCGA-OV and CMB-OV are public
TCIA collections; exact series used are listed by Series Instance UID in
`data/series_lists/*_final_selected.csv` / `*_stage_a_selected.csv`, fully
reproducible via the download scripts in `scripts/`.

## Scope and future work

Not attempted in this iteration, given a 5-day timeline:
- Merlin (secondary foundation model comparison)
- MRI modality (TCGA-OV includes some MR series, not used here)
- Fine-tuning at the encoder level (74 labeled patients is too small to
  safely update CT-FM's weights without overfitting; classifier comparison
  on frozen embeddings was used instead, a more appropriately-scoped test)
- Mapping SHAP-important embedding dimensions back to physical/visual
  image content (would need occlusion or saliency mapping, following
  CT-FM's own OFD method)
- Edge deployment / quantization

## Setup

```
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Scripts in `scripts/` are numbered in pipeline order. Run from the project
root.