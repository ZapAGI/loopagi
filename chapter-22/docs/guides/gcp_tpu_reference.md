# GCP TPU VM Reference Guide — ARC Solver

## TPU VM Details

| Property | Value |
|----------|-------|
| **Name** | `arc-solver-tpu` |
| **Type** | `v5litepod-4` |
| **Zone** | `us-west4-a` |
| **Project** | `project-f4a684ca-5029-474c-b74` |
| **Account** | `nycmeplease@gmail.com` |
| **OS** | Ubuntu 22.04 LTS |
| **CPUs** | 112 cores |
| **RAM** | 188GB |
| **Disk** | 100GB |
| **Python** | 3.10.12 |

## Key Findings

### TPU + HuggingFace `model.generate()` Incompatibility
- HuggingFace `model.generate()` uses **dynamic control flow** (while loops, if statements based on generated tokens)
- PyTorch/XLA uses **lazy evaluation** — it traces computation graphs and compiles them
- Dynamic control flow breaks XLA tracing, causing hangs or errors
- **Solution**: Use CPU inference on TPU VMs (112 cores + 188GB RAM handles full 16GB model)

### Version Compatibility
- `torch_xla` version must **exactly match** `torch` major.minor version
- `torch 2.11` + `torch_xla 2.9` = **broken** (`ImportError: undefined symbol`)
- `torch 2.9.1` + `torch_xla 2.9.0` = **working**

### HuggingFace Rate Limiting
- Unauthenticated requests to HF Hub are severely rate-limited
- `from_pretrained()` with remote model name will **stall** even if model is partially cached
- **Solution**: Download model to local dir first with `snapshot_download()`, then load from local path
- Or set `HF_TOKEN` environment variable

## Quick Commands

### SSH into TPU VM
```bash
gcloud compute tpus tpu-vm ssh arc-solver-tpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-west4-a
```

### Run remote command
```bash
gcloud compute tpus tpu-vm ssh arc-solver-tpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-west4-a \
  --command="<command>"
```

### SCP files to TPU VM
```bash
gcloud compute tpus tpu-vm scp \
  /local/path/file.tar.gz \
  arc-solver-tpu:~/file.tar.gz \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-west4-a
```

### Download model on TPU VM
```bash
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('unsloth/Qwen3-8B', local_dir='/home/anubix/qwen3-8b')
"
```

### Run eval
```bash
cd ~ && PYTHONPATH=. python3 chapter-22/gcp/run_tpu_eval.py \
  --model ~/qwen3-8b \
  --challenges ~/arc-agi_evaluation_challenges.json \
  --tasks 5 \
  --output tpu_eval_results.json
```

### Delete TPU VM (when done — saves $$$)
```bash
gcloud compute tpus tpu-vm delete arc-solver-tpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-west4-a
```

## Installed Packages
- `torch==2.9.1`
- `torch_xla==2.9.0`
- `transformers==5.4.0`
- `accelerate==1.13.0`
- `rich==14.3.3`
- `sentencepiece==0.2.1`
- `huggingface_hub==1.8.0`

## File Layout on TPU VM
```
~/
├── loopagi/                          # Solver package
│   └── arc/                          # ARC modules (tpu_bridge.py, etc.)
├── chapter-22/gcp/run_tpu_eval.py    # Eval runner script
├── arc-agi_evaluation_challenges.json # 120 eval tasks
├── qwen3-8b/                         # Model weights (local download)
│   ├── config.json
│   ├── model-00001-of-00004.safetensors
│   ├── model-00002-of-00004.safetensors
│   ├── model-00003-of-00004.safetensors
│   ├── model-00004-of-00004.safetensors
│   ├── tokenizer.json
│   └── ...
└── loopagi-solver.tar.gz             # Upload archive
```

## Cost Estimates
- TPU v5litepod-4: ~$3.22/hr (free tier covers this with $300 credit)
- **IMPORTANT**: Delete VM when not in use!
- Full 120-task eval estimated: 15-20 hours on CPU = ~$50-65
