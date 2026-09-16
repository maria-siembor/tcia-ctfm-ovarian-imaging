# TCGA-OV Series Selection — Stage A Log

## Method
Metadata-only filtering of `SeriesDescription` against an exclusion keyword
list, applied to `SeriesDescription` alone (never `ProtocolName`, see
rationale below), plus a minimum `ImageCount >= 50` threshold. One series
per patient retained: the surviving candidate with the highest `ImageCount`.

## Sources
- Rich et al. 2026, "TCIA Radiology Image Processing for AI and Radiomics",
  medRxiv DOI 10.64898/2026.06.15.26354651 — base exclusion keyword list
  (localizer, scout, topogram, smart prep, mip, etc.), demonstrated on
  TCGA-KIRC, same TCIA multi-institutional heterogeneity as TCGA-OV.
- Pai et al. 2025 (CT-FM paper), Supplementary S1 — `ImageCount >= 50`
  threshold, matched to CT-FM's own pretraining inclusion criteria since
  our task benchmarks that specific model.
- `BodyPartExamined == 'OVARY'` confirmed uniform across all 820 series
  (checked directly), so anatomy keywords were NOT required in
  `SeriesDescription` — many legitimate series omit them since body part
  is already established at the collection level.

## Key decisions made during validation against real data

**Exclusion checks `SeriesDescription` only, never `ProtocolName`.**
Initially checked both combined. Found this wrongly excluded valid series:
`TCGA-13-0793`'s real 119-image `CHEST ABD PEL W/ CONTRAST` series was
dropped because its `ProtocolName` also covered a separate lung-windowed
reconstruction. `TCGA-13-0724`'s real 85-image `CHEST/ABDOMEN/PELVIS`
series was dropped because `ProtocolName` was `SURVEY-Chest-Abd-Pel`
(an institution's protocol name, not a scout image). Both fixed by
restricting all exclusion checks to `SeriesDescription`.

**Blank `SeriesDescription` is allowed, not excluded.**
`TCGA-24-1614` (53 images) and `TCGA-24-1616` (63 images) have real,
sizeable series with no description text ever submitted. An earlier blanket
blank-string exclusion wrongly dropped both.

**`= NONE =` (the literal placeholder string) IS excluded, distinct from
a genuinely blank field.** `TCGA-25-1878` and `TCGA-25-1322` only have
`Contrast/Bolus Agent: ...` and `= NONE =` labeled series, no real
diagnostic series submitted at all.

**"Recon N:" prefix is NOT excluded.**
`TCGA-13-1412`'s `Recon 2: ABDOMEN PELVIS C+` (126 images) is a real
primary series; some sites apparently use "Recon N:" as a normal save-name
prefix, not a marker of a derived/duplicate copy. An earlier blanket
`recon\s*\d` exclusion wrongly dropped several patients' only real series.

**Lung-only series excluded, but only via `SeriesDescription`.**
`TCGA-13-0793`'s `"1.25 lung"` (a lung-windowed reconstruction) is
correctly excluded; the patient's real abdomen/pelvis series was found
instead once the ProtocolName-contamination bug (above) was fixed.

## Remaining known limitation (documented, not further pursued)
**7/143 patients (4.9%) have no series that survives Stage A:**
- `TCGA-61-2097`, `TCGA-13-0921` — only delayed-phase/bolus-tracking/
  topogram series submitted, genuinely no primary diagnostic series
  available in the public archive for these patients.
- `TCGA-25-1878`, `TCGA-25-1322`, `TCGA-25-1323`, `TCGA-25-1313`,
  `TCGA-25-1317`, `TCGA-25-1325` — only `Contrast/Bolus Agent: ...` /
  `= NONE =` labeled series available. Unconfirmed whether this reflects
  genuinely non-diagnostic series or a site-specific mislabeling similar
  to the "survey"/"lung" cases above; not further investigated since
  resolving it would require opening individual DICOM headers, deferred
  as an open question rather than guessed at.

**Final Stage A yield: 136/143 patients (95.1%).**

## Known gap: Stage B not yet applied
This filtering used only `SeriesDescription` + `ImageCount`, fields
available in the series-list metadata. `SliceThickness` and voxel-spacing/
orientation checks require reading actual DICOM headers or converted
NIfTI files, and are NOT possible at this stage. See Stage B (planned,
post DICOM→NIfTI conversion).

---

# TCGA-OV Series Selection — Stage B Log

## Method
DICOM header inspection (`SliceThickness`, `ImageOrientationPatient`) on one
representative file per Stage A-selected series (136 total). Not possible
from series-list metadata alone, these fields only exist in the DICOM files
themselves. Run directly on downloaded DICOM headers, no NIfTI conversion
needed for this check.

## Results

**SliceThickness**: all 136 series between 1.0mm and 7.5mm (median 5.0mm).
Comfortably under Rich et al. 2026's 10mm exclusion threshold; nothing
excluded on this criterion.

**Orientation**: `ImageOrientationPatient` checked against the standard
axial pattern `[1,0,0,0,1,0]` (row direction along patient-right, column
direction along patient-anterior).

**2 non-axial series found and fixed:**
- `TCGA-25-2393`: selected series was `"AP Routine 3.0 B40f cor"` (137
  images), orientation `[1,0,0,0,0,-1]` = coronal. The "cor" abbreviation
  wasn't caught by Stage A's `coronal` keyword match.
- `TCGA-25-2042`: selected series was `"Coronl AP Routine"` (91 images),
  same coronal orientation. "Coronl" (typo/truncation of "Coronal") also
  wasn't caught.

**Fix applied to Stage A** (not a Stage B override): widened the exclusion
pattern from `r'coronal'` to `r'coron'` (stem, catches "coronal", "Coronl")
plus `r'\bcor\b'` (catches the trailing "cor" abbreviation). Re-ran Stage A;
both patients' selection automatically moved to their real axial series
(`TCGA-25-2393` → "AP Routine 5.0 B40f", 101 images; `TCGA-25-2042` →
"AP Routine 5.0 B40f", 91 images), no manual override needed.

**Verification**: full orientation re-check across all 136 series post-fix
confirms 100% axial (three groups differing only in decimal-precision
formatting across scanners: `[1.00000,...]`, `[1.000000,...]`, `[1,0,0,0,1,0]`
all represent the same orientation).

## Final Stage A+B combined result
**136/143 TCGA-OV patients (95.1%)**, each with one verified primary
series: axial orientation, SliceThickness 1.0–7.5mm, ImageCount >= 50,
free of scout/localizer/topogram/delay/reformat/bolus-placeholder content.

## Note on Stage B scope
Only `SliceThickness` and orientation were checked. Reconstruction kernel
filtering (Rich et al.'s B5-B8/bone exclusion) was deliberately NOT applied,
kernel naming isn't standardized across scanner vendors and blind
application risked excluding valid series (see Stage A log). Remains a
documented open question, not resolved.

---

# TCGA-OV Series Selection — Stage C Log (final exclusion, post-conversion)

## Method
DICOM→NIfTI conversion (`scripts/05_convert_tcga_ov.py`, via
`src/data/dicom_to_nifti.py`) captures ITK's own C++-level series-reader
warnings during `sitk.ImageSeriesReader.Execute()`. When the slice
spacing along the z-axis is irregular (missing slices, inconsistent
inter-slice gaps), ITK emits a "nonuniform sampling" warning together
with a numeric severity estimate, logged per patient as
`itk_nonuniformity` in `data/series_lists/tcga_ov_conversion_log.csv`.
Slice thickness and orientation (Stage A/B) do not catch this: a series
can be uniformly axial with a valid slice thickness value in its header
and still have irregular real-world spacing between slices, both due to
missing/duplicated slices in what was submitted to the archive.

**Threshold**: `itk_nonuniformity > 20` (`scripts/06_finalize_selection.py`,
`NONUNIFORMITY_THRESHOLD`). Not derived from an external source; chosen by
inspecting the full distribution of logged values across all 136 converted
series, which showed a clear gap between the bulk of series (single-digit
or low-teens values) and 6 clear outliers.

## Result
**6/136 patients excluded**, all with `itk_nonuniformity` far above the
single-digit/low-teens range typical of the rest of the cohort:
`TCGA-10-0934` (371.6), `TCGA-10-0936` (322.6), `TCGA-25-2393` (165.9),
`TCGA-61-1737` (70.6), `TCGA-61-2016` (65.5), `TCGA-61-1998` (24.9).

Note on `TCGA-25-2393`: this is the same patient whose *original* selected
series was coronal and was fixed in Stage B (see above). The Stage B fix
moved its selection to a genuine axial series ("AP Routine 5.0 B40f");
that axial series is what is excluded here, for an unrelated reason
(irregular slice spacing, not orientation). The two issues are independent
and both happen to affect this one patient.

**Final Stage A+B+C combined result: 130/143 TCGA-OV patients (90.9%)**,
each with one verified primary series: axial orientation, SliceThickness
1.0–7.5mm, ImageCount >= 50, regular inter-slice spacing (ITK
nonuniformity <= 20), free of scout/localizer/topogram/delay/reformat/
bolus-placeholder content. This is the cohort used for every downstream
result in `RESULTS_LOG.md` (`data/series_lists/tcga_ov_final_selected.csv`).

---

# Why These Checks: Literature Justification

## Why SliceThickness matters
Slice thickness is one of the most consistently reported sources of
non-biological variability in CT-derived features across the radiomics
literature. Mackin et al. (2015, *Invest Radiol* 50:757–765) used a
controlled phantom scanned across 18 different scanners and found that
radiomic feature variability driven by acquisition parameters, including
slice thickness, was comparable in magnitude to genuine tumor-driven
variability in real non-small-cell lung cancer cases, meaning acquisition
differences alone can be as large as the biological signal being studied.
Larue et al. (2017, *Acta Oncol* 56:1544–1553) showed slice thickness
specifically affects feature stability through a comprehensive phantom
study varying scanners, tube currents, and slice thicknesses together.
Mechanistically, this comes down to the partial volume effect: a thicker
slice averages more distinct tissue into each voxel along the z-axis,
reducing textural fidelity and biasing intensity/shape features, an effect
Rich et al. (2026) describe directly in their own TCGA-KIRC pipeline
("excessive slice thickness increases partial volume effects and reduces
textural fidelity"), which is the direct precedent used for our 10mm
threshold.

## Why orientation consistency matters
Rich et al. (2026) reorient every volume to a canonical coordinate system
specifically because, without it, "voxel axes correspond to different
anatomical directions" across series pulled from different institutions,
undermining consistent spatial interpretation for anything downstream
(cropping, resampling, model input). A coronal or sagittal series
accidentally treated as axial isn't just lower quality, it's geometrically
incompatible: CT-FM's own preprocessing (Orientation to "SPL", confirmed
from their HuggingFace model card) and its 3mm slice-thickness/1mm
in-plane resampling spec both assume the input volume is a genuine axial
acquisition. Feeding it a mislabeled coronal series wouldn't produce a
subtly worse embedding, it would produce a meaningless one, the physical
axes the model expects to see wouldn't correspond to the axes actually
present in the data.

## Why this matters more, not less, for a heterogeneous multi-institutional
## dataset like TCGA-OV
TCIA's own collection page states imaging was submitted from many sites
worldwide with no enforced acquisition standard. This is exactly the
condition under which Mackin et al. and Larue et al.'s phantom-measured
variability is most likely to actually appear in real data, and exactly
why Rich et al. built a dedicated series-selection stage rather than
assuming metadata alone was trustworthy. Our own Stage A/B process
independently reproduced their core finding: text-based filtering alone
missed 2 of 136 non-axial series (the "cor"/"Coronl" cases), which only a
geometry-based check caught, directly mirroring their stated rationale for
including a voxel-spacing/orientation safeguard rather than relying on
`SeriesDescription` text alone.

## References
- Mackin, D., Fave, X., Zhang, L., et al. (2015). Measuring computed
  tomography scanner variability of radiomics features. *Investigative
  Radiology*, 50(11), 757–765. https://doi.org/10.1097/rli.0000000000000180
- Larue, R.T.H.M., Van Timmeren, J.E., De Jong, E.E.C., et al. (2017).
  Influence of gray level discretization on radiomic feature stability for
  different CT scanners, tube currents and slice thicknesses: a
  comprehensive phantom study. *Acta Oncologica*, 56(11), 1544–1553.
  https://doi.org/10.1080/0284186x.2017.1351624
- Rich, J., Kang, R., Jin, D., Subramanian, S., Duddalwar, V., & Pachter, L.
  (2026). TCIA Radiology Image Processing for AI and Radiomics. *medRxiv*.
  https://doi.org/10.64898/2026.06.15.26354651
- Pai, S., Hadzic, I., Bontempi, D., et al. (2025). Vision Foundation
  Models for Computed Tomography (CT-FM). Preprint / project-lighter
  HuggingFace model cards (orientation and spacing specification).
