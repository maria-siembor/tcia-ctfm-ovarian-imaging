"""
Series selection, Stage A (metadata-only).
Refs: Rich et al. 2026 (medRxiv 10.64898/2026.06.15.26354651) for exclusion
keywords; CT-FM paper Supplementary S1 for ImageCount >= 50 threshold.

Junk-pattern exclusion checks SeriesDescription ONLY, never ProtocolName.
ProtocolName describes the whole exam and can contain words like "survey"
or "lung" as part of an institution's naming convention without meaning
this specific series is junk (confirmed via TCGA-13-0724, TCGA-13-0793).

Blank SeriesDescription is NOT excluded, real series can lack a label
(confirmed via TCGA-24-1614/1616). "Recon N:" prefix is NOT excluded,
some sites use it as a normal save-name for primary series, not a marker
of a derived copy (confirmed via TCGA-13-1412).

require_body_part_contains: optional filter on BodyPartExamined. Not
needed for TCGA-OV (uniformly 'OVARY') but required for datasets like
CMB-OV where BodyPartExamined varies (CHEST, KIDNEY, ABDOMENPELVIS, etc.)
and doesn't guarantee ovary-relevant anatomy on its own.
"""

import pandas as pd
import re

EXCLUDE_PATTERNS = [
    r'localizer', r'\bscout\b', r'\bscouts\b', r'\bcal\b',
    r'mipseries', r'\bpjn\b', r'summary\s*series', r'topogram',
    r'\bmips?\b', r'smart\s*prep',
    r'coron', r'\bcor\b', r'sagittal', r'\bsag\b', r'reformat', r'\bdelay',
    r'contrast/bolus\s*agent', r'\baverage\b', r'^\s*=\s*none\s*=\s*$',
]
EXCLUDE_REGEX = re.compile('|'.join(EXCLUDE_PATTERNS), re.IGNORECASE)

LUNG_REGEX = re.compile(r'lung', re.IGNORECASE)
ABD_PEL_REGEX = re.compile(r'abd|pel', re.IGNORECASE)


def select_series_stage_a(dataset_slug: str, min_image_count: int = 50,
                           require_body_part_contains: list = None):
    df = pd.read_csv(f"data/series_lists/{dataset_slug}_ct_series.csv")
    df['SeriesDescription'] = df['SeriesDescription'].fillna('')

    if require_body_part_contains:
        df['BodyPartExamined'] = df['BodyPartExamined'].fillna('')
        body_part_ok = df['BodyPartExamined'].apply(
            lambda x: any(term in x.upper() for term in require_body_part_contains)
        )
        df = df[body_part_ok]

    is_excluded = df['SeriesDescription'].apply(lambda x: bool(EXCLUDE_REGEX.search(x)))
    is_lung_only = df['SeriesDescription'].apply(
        lambda x: bool(LUNG_REGEX.search(x)) and not bool(ABD_PEL_REGEX.search(x))
    )
    df['is_excluded'] = is_excluded | is_lung_only

    candidates = df[(~df['is_excluded']) & (df['ImageCount'].astype(int) >= min_image_count)]
    selected = candidates.sort_values('ImageCount', ascending=False).drop_duplicates(
        subset='PatientID', keep='first'
    )

    out_path = f"data/series_lists/{dataset_slug}_stage_a_selected.csv"
    selected.to_csv(out_path, index=False)
    print(f"[{dataset_slug}] {len(selected)} series selected, "
          f"{selected['PatientID'].nunique()} patients. Saved to {out_path}")

    return selected