# Kaggle Upload & Submission Reference

Complete reference for uploading files to Kaggle and submitting to competitions.
Source: [Kaggle CLI Official Docs](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md)

---

## 1. Upload Methods Overview

| Method | What | When to Use |
|--------|------|-------------|
| `kaggle datasets create` | Create new dataset | First time uploading data/code/wheels |
| `kaggle datasets version` | Update existing dataset | Updating solver code, adding wheels |
| `kaggle kernels push` | Push notebook + run it | Submitting/updating your notebook |
| Web UI upload | Manual file upload | When CLI isn't working or for quick edits |
| `kaggle competitions submit` | Submit prediction file | Non-code competitions (not ARC) |

## 2. Dataset Upload (CLI)

### First Time: Create Dataset
```bash
# 1. Create a folder with your files
mkdir my-dataset/
cp my_files/* my-dataset/

# 2. Initialize metadata
kaggle datasets init -p my-dataset/
# Edit my-dataset/dataset-metadata.json:
#   "title": "my-dataset-name"
#   "id": "username/my-dataset-name"

# 3. Upload
kaggle datasets create -p my-dataset/              # flat files only
kaggle datasets create -p my-dataset/ --dir-mode zip  # include subdirectories
```

### Update Existing Dataset
```bash
kaggle datasets version -p my-dataset/ -m "description of changes" --dir-mode zip
```

### Key Options
- `--dir-mode skip` (default): **Ignores all subdirectories** — only uploads loose files
- `--dir-mode zip`: **Zips each subdirectory separately** and uploads as zip files
- `--dir-mode tar`: Same but as tar archives

### IMPORTANT: `--dir-mode zip` Behavior
- Each top-level subdirectory gets zipped **individually** and uploaded as a separate file
- Kaggle **auto-extracts** zips on the server side
- Files inside subdirectories are accessible after extraction
- **Loose files in the root** (not in any subdirectory) are uploaded as-is
- The `dataset-metadata.json` is NOT uploaded as a data file

### Verify Upload
```bash
# Check dataset size and status
kaggle datasets list --mine --search my-dataset
kaggle datasets status username/my-dataset-name
```

## 3. Notebook Upload (CLI)

### Setup
Create a folder with:
```
my-kernel/
  notebook.ipynb          # or script.py
  kernel-metadata.json    # metadata file
```

### kernel-metadata.json Format
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
  "keywords": []
}
```

### Push (Upload + Run)
```bash
kaggle kernels push -p my-kernel/
```

### Override Accelerator
```bash
kaggle kernels push -p my-kernel/ --accelerator NvidiaTeslaP100
```

Available accelerators (Feb 2026):
- `NvidiaTeslaP100` (default GPU)
- `NvidiaTeslaT4`
- `NvidiaTeslaT4Highmem`
- `NvidiaTeslaA100`
- `NvidiaL4`, `NvidiaL4X1`
- `NvidiaH100`
- `NvidiaRtxPro6000`
- `TpuV38`, `Tpu1VmV38`, `TpuV5E8`, `TpuV6E8`

### Monitor
```bash
kaggle kernels status username/kernel-slug
kaggle kernels output username/kernel-slug -p /tmp/output/
```

## 4. Competition Submission

### Regular Competition (submit a file)
```bash
kaggle competitions submit <competition> -f submission.csv -m "description"
kaggle competitions submissions -c <competition>
```

### Code Competition (ARC Prize is this type)
For code competitions, the notebook IS the submission. Steps:
1. Push notebook with `kaggle kernels push`
2. Notebook runs on Kaggle's servers
3. Notebook must write output to `/kaggle/working/` (e.g., `submission.json`)
4. Submit via:
```bash
kaggle competitions submit <competition> -k username/notebook-slug -f submission.json -v <version> -m "description"
```
Or just run the notebook — Kaggle auto-evaluates the output.

## 5. Web UI Upload (Alternative)

### Upload Dataset via Browser
1. Go to https://www.kaggle.com/datasets
2. Click "+ New Dataset"
3. Drag & drop files or click "Upload"
4. Set title, visibility, license
5. Click "Create"

### Upload Notebook via Browser
1. Go to https://www.kaggle.com/code
2. Click "+ New Notebook"
3. Upload `.ipynb` file or paste code
4. Add data sources in the right sidebar
5. Click "Save & Run All"

### Edit Existing Notebook via Browser
1. Go to https://www.kaggle.com/code/username/kernel-slug
2. Click "Edit"
3. Make changes in the editor
4. "Save Version" → "Save & Run All (Commit)"

## 6. Our ARC Prize Workflow

### Files
```
chapter-22/kaggle/
  notebook.ipynb              # Kaggle submission notebook
  kernel-metadata.json        # Kernel config (GPU, datasets, etc.)
  dataset/
    dataset-metadata.json     # Dataset config
    loopagi/                  # Solver code (packaged from loopagi/)
      arc/*.py                # All solver modules
      core/*.py               # Minimal stubs
      bitsandbytes-*.whl      # Bundled wheel (inside loopagi/ dir so it gets zipped together)
  package_for_kaggle.sh       # Script to repackage solver
```

### Update Solver + Push
```bash
# 1. Repackage solver code
bash chapter-22/kaggle/package_for_kaggle.sh

# 2. Re-add wheel (package_for_kaggle.sh wipes the dataset dir!)
cp /tmp/bnb-wheels/bitsandbytes-*.whl chapter-22/kaggle/dataset/loopagi/

# 3. Recreate dataset-metadata.json (also wiped by script!)
cat > chapter-22/kaggle/dataset/dataset-metadata.json << 'EOF'
{
  "title": "loopagi-arc-solver",
  "id": "karales/loopagi-arc-solver",
  "licenses": [{"name": "Apache 2.0"}]
}
EOF

# 4. Upload dataset
kaggle datasets version -p chapter-22/kaggle/dataset/ -m "description" --dir-mode zip

# 5. Verify upload size (should be ~60MB with wheel)
kaggle datasets list --mine --search loopagi

# 6. Push notebook
kaggle kernels push -p chapter-22/kaggle/

# 7. Monitor
kaggle kernels status karales/arc-prize-2026-arc-agi-2-submission
kaggle kernels output karales/arc-prize-2026-arc-agi-2-submission -p /tmp/kaggle-output/
```

### Gotchas
| Issue | Solution |
|-------|----------|
| `package_for_kaggle.sh` wipes `dataset-metadata.json` | Recreate it after running |
| `--dir-mode zip` needed for subdirectories | Without it, subdirs are silently skipped |
| Wheel must be INSIDE a subdirectory | Loose files in root may upload but wheel inside `loopagi/` gets zipped together |
| 409 Conflict on push | Previous kernel version still running — wait |
| Dataset shows size=0 | Still processing — wait 30s and check again |
| `bitsandbytes` version matters | Kaggle transformers requires `>=0.46.1`, use latest (0.49.2) |
| P100/T4 don't support bfloat16 | Use `torch.float16` in BnB config |
