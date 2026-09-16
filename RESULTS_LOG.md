# TCGA-OV: CT-FM Zero-Shot CLOVAR Subtype Probe

## Setup
- 74/130 selected patients have a CLOVAR subtype label (via TCGA-OV-Radiogenomics,
  Vargas et al. 2016/2017)
- Classes: Differentiated (20), Immunoreactive (13), Mesenchymal (22), Proliferative (19)
- Frozen CT-FM embeddings (512-dim), stratified 5-fold cross-validation
- Majority-class baseline: 29.7%

## Result
No configuration tested beat the majority-class baseline:

| Method | Accuracy |
|---|---|
| Logistic Regression, C=1.0 (default) | 21.5% +/- 9.6% |
| Logistic Regression, C=0.001 | 16.1% +/- 7.9% |
| Logistic Regression, C=0.01 | 22.8% +/- 9.8% |
| Logistic Regression, C=0.1 | 18.9% +/- 7.7% |
| PCA(5) + Logistic Regression | 24.4% +/- 9.2% (best, still below baseline) |
| PCA(10/20/30) + Logistic Regression | 18.9-19.0% |
| **Majority-class baseline** | **29.7%** |

## Interpretation
Tested across a systematic sweep of regularization strengths and PCA
dimensionalities specifically to rule out overfitting (high-dimensional
512-dim features vs. only ~59 training patients per fold) as the sole
explanation. Since no configuration approached, let alone beat, the
trivial baseline, this is not an artifact of one poorly-chosen
hyperparameter.

**Conclusion: CT-FM's self-supervised, label-free zero-shot embeddings do
not linearly encode CLOVAR molecular subtype for this cohort.** This is
a genuine negative result, not a pipeline failure, note that TCGA-OV was
part of CT-FM's pretraining data (pixel-level, label-free exposure per
Supplementary Table S5), so this also indicates that pretraining exposure
without task-specific labels does not by itself produce subtype-relevant
structure in the embedding space.

## Correction on the "benchmark" framing
Earlier framing described this as benchmarking against "Vargas et al.
2017's reported performance." On closer check, that paper does NOT report
an overall 4-class prediction accuracy/AUC. Their actual finding was
narrower: specific individual CT features showed a statistically
significant association with only ONE subtype (mesenchymal, via
diffuse peritoneal involvement and mesenteric infiltration), not a
4-way discriminative signal.

This is actually informative rather than a gap in the comparison: if
expert radiologists, deliberately selecting features with formal
statistical testing, could only find a significant link to one of four
subtypes, it is consistent (not surprising) that an unsupervised,
generic embedding also fails to cleanly separate all four classes.
Both findings point toward the same likely explanation: CLOVAR subtype,
as a full four-way distinction, may not be strongly or cleanly visible
in CT imaging at all, at best a narrow, partial signal for one subtype,
not a robust visual fingerprint for the whole classification scheme.

This motivates the next step: does lightweight fine-tuning (adding
task-specific supervision) allow the same architecture to recover
subtype-relevant structure? A meaningful improvement post-fine-tuning
would demonstrate the representation gap is closeable with supervision;
continued failure would further support the "not strongly visible in
CT at all" explanation over a "CT-FM-specific limitation" explanation.

---

# Classifier comparison and permutation test

## Setup
Same 74 labeled patients, PCA(5) + classifier, 5-fold stratified CV.
Tested: Logistic Regression, Linear SVM, RBF SVM, shallow Random Forest,
small MLP.

## Results
| Classifier | Accuracy |
|---|---|
| Logistic Regression | 24.4% +/- 9.2% |
| **Linear SVM** | **35.1% +/- 6.5%** |
| RBF SVM | 28.6% +/- 9.7% |
| Random Forest (shallow) | 30.9% +/- 10.5% |
| Small MLP | 24.4% +/- 5.6% (did not converge) |
| Majority-class baseline | 29.7% |

Linear SVM was the only result with both a real margin over baseline and
reasonably tight variance.

## Permutation test on Linear SVM
200 label-shuffled reruns of the identical CV pipeline: permutation mean
27.3% (sensibly near the 25% chance level for 4 classes), std 5.8%.
**Empirical p-value: 0.08** (8% of random shuffles matched or exceeded
the real 35.1%).

## Honest interpretation
0.08 is suggestive but does not clear the conventional p<0.05 bar. More
importantly: Linear SVM was selected as the best of 5 classifiers tried,
a multiple-comparisons problem. A Bonferroni-style correction for testing
5 models would require p<0.01 for confidence at the same nominal level;
0.08 does not survive this correction.

**Conclusion: weak, suggestive evidence of above-chance signal in CT-FM's
frozen embeddings for CLOVAR subtype, not strong enough to claim
confidently given the small sample and multiple models tested.** This is
reported as-is rather than rounded up to a positive finding or down to a
null one, an honest middle-ground result is more defensible than either.

---

# SHAP interpretability (Linear SVM, PCA(5) components)

Used KernelExplainer (model-agnostic, appropriate for non-tree SVM) on
the 5 PCA components feeding the Linear SVM. Note: this explains which
*learned PCA directions* the model relies on, not physically-interpretable
anatomical features, no mapping exists from these components back to
original image regions without additional work (e.g. saliency mapping
on the original embedding dimensions).

## Mean |SHAP value| per component, per class
| | PC1 | PC2 | PC3 | PC4 | PC5 |
|---|---|---|---|---|---|
| Differentiated | 0.008 | 0.016 | 0.003 | 0.010 | **0.024** |
| Immunoreactive | **0.022** | 0.018 | 0.004 | 0.004 | **0.027** |
| Mesenchymal | 0.009 | **0.029** | 0.005 | **0.025** | 0.004 |
| Proliferative | **0.022** | **0.031** | 0.004 | **0.032** | 0.003 |

## Pattern
PC3 is uniformly weak across all four classes, contributes little
regardless of subtype. PC2/PC4 dominate for Mesenchymal and
Proliferative; PC1/PC5 dominate for Immunoreactive and Differentiated.
The model relies on different learned directions for different subtypes,
rather than one dominant component driving all predictions, a coherent
structure, though given the weak/borderline overall classification signal
(see permutation test, p=0.08), this should be read as "which components
the model leans on when it does discriminate somewhat," not as strong
evidence those components carry robust, generalizable subtype information.

---

# CMB-OV: qualitative generalization check

## Setup
6 CMB-OV patients survived series selection (from 19 total; most excluded
for wrong anatomy, given CMB-OV's BodyPartExamined is NOT uniformly
ovary-relevant like TCGA-OV, required explicit PELVIS filtering, see
SERIES_SELECTION_LOG.md). No CLOVAR or other labels available without a
dbGaP application, so this is qualitative only: does CT-FM produce
sensible-looking embeddings on data it never encountered during
pretraining.

## Results
- PCA top-2 components explain 47.2% of variance jointly (33.3% + 13.9%),
  meaningful structure, not scattered noise.
- TCGA-OV internal spread (avg distance to its own centroid): 66.56
- CMB-OV internal spread: 58.24 (similar magnitude)
- **Distance between TCGA-OV and CMB-OV centroids: 38.50, smaller than
  either dataset's own internal spread.** CMB-OV's average embedding sits
  within TCGA-OV's normal range of variation, not in a separate region of
  the embedding space.
- Nearest-neighbor cosine similarity (CMB-OV -> closest TCGA-OV patient):
  0.987-0.995.

## Honest correction on the nearest-neighbor result
Checked against a baseline: TCGA-OV's own internal nearest-neighbor
similarity is 0.992 (mean), essentially identical to the CMB-OV cross-
dataset values. Random (non-nearest) TCGA-OV pairs still average 0.968.
**This means the high CMB-OV similarity is not a special generalization
signal, it reflects a generally high baseline similarity across any two
scans in this embedding space** (likely a dominant shared "generic axial
abdomen/pelvis CT" component). The nearest-neighbor check does not add
independent evidence beyond the centroid comparison above.

## Conclusion
The centroid-distance-vs-spread comparison is the genuinely informative
result: CMB-OV, despite being completely absent from CT-FM's pretraining
data, produces embeddings that fall within the normal variation of
TCGA-OV (pretraining-exposed) patients, rather than forming a separate,
out-of-distribution cluster. This is a modest but real positive
generalization finding, appropriately scoped given the small sample
(n=6) and complete absence of labels for this dataset.
