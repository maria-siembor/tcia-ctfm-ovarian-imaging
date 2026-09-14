import sys
sys.path.append("src")

from models.ctfm_wrapper import embed
import glob

# Test on the first available patient
nifti_files = glob.glob("data/nifti/tcga_ov/*.nii.gz")
print(f"Found {len(nifti_files)} NIfTI files")

test_file = nifti_files[0]
print(f"Testing on: {test_file}")

vec = embed(test_file)
print(f"Embedding shape: {vec.shape}")
print(f"Sample values: {vec[:5]}")