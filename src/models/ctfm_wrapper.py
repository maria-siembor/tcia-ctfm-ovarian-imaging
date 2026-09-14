"""Load CT-FM and extract embeddings from preprocessed NIfTI volumes.
Preprocessing parameters are loaded from configs/preprocessing.yaml,
see that file for citations and rationale behind each value."""

import yaml
import torch
from lighter_zoo import SegResEncoder
from monai.transforms import (
    Compose, LoadImage, EnsureType, Orientation,
    ScaleIntensityRange, CropForeground, Resize
)

_model = None
_preprocess = None
_config = None


def _get_config():
    global _config
    if _config is None:
        with open("configs/preprocessing.yaml") as f:
            _config = yaml.safe_load(f)
    return _config


def _get_model():
    global _model
    if _model is None:
        _model = SegResEncoder.from_pretrained("project-lighter/ct_fm_feature_extractor")
        _model.eval()
    return _model


def _get_preprocess():
    global _preprocess
    if _preprocess is None:
        cfg = _get_config()
        _preprocess = Compose([
            LoadImage(ensure_channel_first=True),
            EnsureType(),
            Orientation(axcodes=cfg['orientation']),
            ScaleIntensityRange(
                a_min=cfg['hu_clip']['min'],
                a_max=cfg['hu_clip']['max'],
                b_min=cfg['hu_clip']['rescale_to'][0],
                b_max=cfg['hu_clip']['rescale_to'][1],
                clip=True,
            ),
            CropForeground() if cfg['crop_foreground'] else lambda x: x,
            Resize(spatial_size=tuple(cfg['resize_target'])),
        ])
    return _preprocess


def embed(nifti_path: str):
    """Returns a 512-dim embedding vector for one NIfTI volume."""
    model = _get_model()
    preprocess = _get_preprocess()

    input_tensor = preprocess(nifti_path)

    with torch.no_grad():
        output = model(input_tensor.unsqueeze(0))[-1]
        embedding = torch.nn.functional.adaptive_avg_pool3d(output, 1).squeeze()

    return embedding.numpy()