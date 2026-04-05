# Kaggle Notebook Reference Guide

Comprehensive reference for building and submitting Kaggle competition notebooks,
based on research from ARC Prize 2025 winners, Kaggle documentation, and community best practices.

## 1. Filesystem Layout

| Path | Type | Notes |
|------|------|-------|
| `/kaggle/input/` | Read-only | All attached data sources mounted here |
| `/kaggle/input/competitions/<slug>/` | Read-only | Competition data (e.g., `arc-prize-2026-arc-agi-2`) |
| `/kaggle/input/datasets/<owner>/<dataset>/` | Read-only | User-uploaded datasets |
| `/kaggle/input/<model-slug>/` | Read-only | Kaggle Models (HF models uploaded as Kaggle Models) |
| `/kaggle/working/` | Read-write | Output directory, max ~20 GB, persists between runs |
| `/kaggle/temp/` | Read-write | Temporary space, may not persist |

### Key Observations (Learned from Our Errors)
- **Competition data**: Mounted under `/kaggle/input/competitions/<competition-slug>/`, NOT `/kaggle/input/<competition-slug>/`
- **User datasets**: Mounted under `/kaggle/input/datasets/<owner>/<dataset-name>/`, NOT `/kaggle/input/<dataset-name>/`
- **Kaggle Models**: Mounted directly under `/kaggle/input/<model-slug>/` (different from datasets!)
- **Dataset zip extraction**: When uploading with `--dir-mode zip`, Kaggle extracts zips and mounts the CONTENTS, not the zip itself. A zip containing `loopagi/` will have `loopagi/` as a subdirectory under the dataset mount point.

### Debug Pattern
Always add this to Cell 1 to understand the filesystem:
```python
import os
for root, dirs, files in os.walk('/kaggle/input'):
    depth = root.replace('/kaggle/input', '').count(os.sep)
    if depth < 3:
        indent = '  ' * depth
        print(f'{indent}{os.path.basename(root)}/ ({len(files)} files, {len(dirs)} dirs)')
```

## 2. Hardware Profiles

| Accelerator | GPU | VRAM | RAM | Weekly Quota |
|-------------|-----|------|-----|-------------|
| GPU P100 | Tesla P100-PCIE | 16 GB | ~30 GB | 30 hrs shared |
| GPU T4x2 | 2× NVIDIA T4 | 16 GB each | ~30 GB | 30 hrs shared |
| TPU v3-8 | 8 TPU v3 cores | — | — | 20 hrs |

- **Per-session runtime**: ~12 hours (CPU/GPU), ~9-12 hours (TPU)
- **P100**: Compute capability 6.0, supports FP16 but **NOT bfloat16 on CUDA**
- **T4**: Compute capability 7.5, supports FP16, **NOT bfloat16 on CUDA**
- **Important**: Use `torch.float16` not `torch.bfloat16` on Kaggle GPUs

## 3. Environment and Packages

### Pre-installed (as of 2025-2026)
- Python 3.12.x
- PyTorch 2.10+ (with CUDA 12.8)
- transformers (latest)
- accelerate
- **NOT pre-installed**: `bitsandbytes`, `unsloth`, `vllm`, `peft`

### Installing Packages Offline (No Internet)

#### Method 1: Bundle wheels in a Kaggle Dataset
```bash
# On local machine: download wheel
pip download bitsandbytes==0.45.5 --no-deps -d ./wheels/

# Upload as Kaggle dataset (put wheel in a subdirectory)
mkdir -p dataset/wheels/
cp wheels/*.whl dataset/wheels/
# Create dataset-metadata.json in dataset/
kaggle datasets create -p dataset/ --dir-mode zip
```

In notebook:
```python
import subprocess, sys, os
# Find wheel in dataset
for root, _, files in os.walk('/kaggle/input'):
    for f in files:
        if f.startswith('bitsandbytes') and f.endswith('.whl'):
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', os.path.join(root, f)])
            break
```

#### Method 2: pip install (may work if package is in Kaggle's cache)
```python
!pip install bitsandbytes -q
```
This works for many packages even with internet off if they're cached in the Kaggle image.

#### Method 3: Kaggle utility datasets
Community datasets with pre-built wheels exist:
- `pedromoya/wheel-bitsandbytes` (v0.43.0 — **TOO OLD**, no CUDA 12.8)
- Create your own with newer versions

### Version Compatibility Critical
- `bitsandbytes` 0.43.x: Only has CUDA ≤12.4 libs → **FAILS on Kaggle's CUDA 12.8**
- `bitsandbytes` 0.45.x+: Has `libbitsandbytes_cuda128.so` → **WORKS**
- Always verify wheel contains the right CUDA lib:
  ```bash
  python -c "import zipfile; z=zipfile.ZipFile('bitsandbytes-X.Y.Z.whl'); print([n for n in z.namelist() if 'cuda12' in n])"
  ```

## 4. Model Loading Patterns

### Pattern A: Kaggle Model (Recommended for HF models)
Upload a HuggingFace model as a Kaggle Model. It mounts directly:
```python
model = AutoModelForCausalLM.from_pretrained('/kaggle/input/qwen3-8b-4bit/')
```

### Pattern B: Kaggle Dataset with model weights
Upload model files as a dataset. Find them:
```python
# Search for config.json (model marker)
for root, dirs, files in os.walk('/kaggle/input'):
    if 'config.json' in files and any(f.endswith('.safetensors') for f in files):
        MODEL_PATH = root
        break
```

### Pattern C: Pre-quantized models (BnB 4-bit)
Models like `unsloth/Qwen3-8B-unsloth-bnb-4bit` require `bitsandbytes` installed.
```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,  # NOT bfloat16 on P100/T4!
)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    quantization_config=bnb_config,
    device_map="auto",
)
```

### P100 dtype Warning
**P100 does NOT support bfloat16 on CUDA.** Use `torch.float16` instead:
```python
# WRONG on P100:
bnb_4bit_compute_dtype=torch.bfloat16

# CORRECT on P100:
bnb_4bit_compute_dtype=torch.float16
```

## 5. Custom Code as Kaggle Dataset

### Upload Pattern
```bash
# Structure your code as a proper Python package
mkdir -p dataset/mypackage/
cp -r src/mypackage/* dataset/mypackage/

# Add dataset metadata
cat > dataset/dataset-metadata.json << 'EOF'
{
  "title": "my-package",
  "id": "username/my-package",
  "licenses": [{"name": "Apache 2.0"}]
}
EOF

# Upload
kaggle datasets create -p dataset/ --dir-mode zip

# Update
kaggle datasets version -p dataset/ -m "description" --dir-mode zip
```

### Import Pattern in Notebook
Kaggle extracts the zip, so your package is at:
`/kaggle/input/datasets/<owner>/<dataset>/mypackage/`

To make it importable:
```python
import sys, os

# Option A: Add parent directory to path
sys.path.insert(0, '/kaggle/input/datasets/owner/my-dataset/')

# Option B: Symlink (if package is the dataset root itself)
DATASET = '/kaggle/input/datasets/owner/my-dataset'
os.symlink(DATASET, '/kaggle/working/mypackage')
sys.path.insert(0, '/kaggle/working')
```

## 6. Kernel Metadata (kernel-metadata.json)

```json
{
  "id": "username/kernel-slug",
  "title": "kernel-slug",
  "code_file": "notebook.ipynb",
  "language": "python",
  "kernel_type": "notebook",
  "is_private": true,
  "enable_gpu": true,
  "enable_internet": false,
  "competition_sources": ["competition-slug"],
  "dataset_sources": ["owner/dataset-slug"],
  "model_sources": ["owner/model-slug/framework/variation"]
}
```

### Important Notes
- `title` should match `id` slug to avoid warnings
- `enable_internet: false` for competition submissions
- `dataset_sources` uses `owner/dataset-name` format
- `competition_sources` uses competition slug only
- Tags that don't exist on Kaggle will be silently dropped

## 7. CLI Commands

```bash
# Push notebook
kaggle kernels push -p /path/to/kernel-dir/

# Check status
kaggle kernels status owner/kernel-slug

# Get logs
kaggle kernels output owner/kernel-slug -p /tmp/output/

# Upload/update dataset
kaggle datasets create -p /path/to/dataset/ --dir-mode zip
kaggle datasets version -p /path/to/dataset/ -m "message" --dir-mode zip

# Check dataset status
kaggle datasets status owner/dataset-name

# Submit to competition (notebook auto-submits via output)
# The notebook writes submission.json to /kaggle/working/ and Kaggle picks it up
```

### 409 Conflict Error
If `kaggle kernels push` returns 409, the previous version is still running/processing.
Wait for it to finish, then push again.

## 8. Competition Submission Format (ARC Prize)

### ARC-AGI-2
- **File**: `submission.json`
- **Location**: `/kaggle/working/submission.json`
- **Format**: JSON dict, keyed by task_id
- Each task has a list of test entries, each with `attempt_1` and `attempt_2` (2D grids)

```json
{
  "task_id_1": [
    {"attempt_1": [[0,1],[2,3]], "attempt_2": [[0,1],[2,3]]}
  ],
  "task_id_2": [
    {"attempt_1": [[1,0]], "attempt_2": [[1,0]]}
  ]
}
```

## 9. Debugging Checklist

1. **First cell**: Print environment, list `/kaggle/input/` tree
2. **GPU check**: Use `getattr(props, 'total_memory', 0)` (attribute name varies by PyTorch version)
3. **Package install**: Do it early, before any imports that depend on it
4. **Model path**: Search with `os.walk`, don't hardcode paths
5. **dtype**: Use `float16` not `bfloat16` on P100/T4
6. **Time budget**: Leave 1h buffer, track per-task time, have fallback outputs
7. **Error handling**: Wrap every task in try/except with fallback

## 10. Lessons Learned (Our ARC Prize 2026 Submission)

| Version | Error | Root Cause | Fix |
|---------|-------|-----------|-----|
| v1 | `AttributeError: total_mem` | PyTorch 2.10 uses `total_memory` | `getattr(props, 'total_memory', ...)` |
| v2 | `ModuleNotFoundError: loopagi` | Dataset at `datasets/karales/...` not `input/` root | Symlink to `/kaggle/working/` |
| v3 | Same — symlink approach worked | Dataset found, import OK | ✅ |
| v4 | `ImportError: bitsandbytes` | Not pre-installed on Kaggle | Install from wheel |
| v5 | `libbitsandbytes_cuda128 not found` | Wheel v0.43.0 too old for CUDA 12.8 | Need v0.45.5+ |

## References

- [Kaggle DL/LLM Workflows Guide](https://huggingface.co/datasets/John6666/knowledge_base_md_for_rag_1/blob/main/kaggle_20251121.md)
- [ARC Prize 2025 Results](https://arcprize.org/blog/arc-prize-2025-results-analysis)
- [Installing pip packages offline on Kaggle](https://www.kaggle.com/code/panozzaj/installing-pip-packages-on-kaggle-without-internet)
- [Kaggle Competition Docs](https://www.kaggle.com/docs/competitions)
