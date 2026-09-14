"""Load CT-FM and extract embeddings from preprocessed NIfTI volumes."""

import torch
from lighter_zoo import SegResEncoder
from monai.transforms import (
    Compose, LoadImage, EnsureType, Orientation,
    ScaleIntensityRange, CropForeground, Resize
)

_model = None
_preprocess = None

# Bounds memory: without this, a large volume (e.g. 597 slices) blows up
# to ~18GB+ during the forward pass since the whole volume is encoded at
# once (no sliding window in this simple usage path). Resize to a fixed,
# moderate size instead, we only need one pooled embedding per scan, not
# pixel-level output, so some resolution loss here is an acceptable
# tradeoff given the CPU memory constraint.
RESIZE_TARGET = (160, 160, 160)


def _get_model():
    global _model
    if _model is None:
        _model = SegResEncoder.from_pretrained("project-lighter/ct_fm_feature_extractor")
        _model.eval()
    return _model


def _get_preprocess():
    global _preprocess
    if _preprocess is None:
        _preprocess = Compose([
            LoadImage(ensure_channel_first=True),
            EnsureType(),
            Orientation(axcodes="SPL"),
            ScaleIntensityRange(a_min=-1024, a_max=2048, b_min=0, b_max=1, clip=True),
            CropForeground(),
            Resize(spatial_size=RESIZE_TARGET),
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