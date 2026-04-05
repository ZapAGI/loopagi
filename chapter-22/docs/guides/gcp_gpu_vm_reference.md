# GCP GPU VM Reference Guide — ARC Solver

## Project Info

| Property | Value |
|----------|-------|
| **Project ID** | `project-f4a684ca-5029-474c-b74` |
| **Account** | `nycmeplease@gmail.com` |
| **Credits** | $300 free tier |

---

## GPU Options Available (with $300 credits)

### Best Options for Our Use Case (Qwen3-8B, 16GB model)

| GPU | VRAM | Machine Type | Est. $/hr | Inference Speed | Best For |
|-----|------|-------------|-----------|----------------|----------|
| **NVIDIA L4** | 24GB GDDR6 | `g2-standard-4` | ~$0.70 | ~5-8s/call | ✅ **Best choice** — enough VRAM for full model |
| **NVIDIA T4** | 16GB GDDR6 | `n1-standard-4` + T4 | ~$0.55 | ~8-15s/call | ✅ Good — needs 4-bit quant (same as Kaggle) |
| **NVIDIA V100** | 16GB HBM2 | `n1-standard-8` + V100 | ~$2.50 | ~5-8s/call | ❌ Too expensive for our budget |
| **NVIDIA P100** | 16GB HBM2 | `n1-standard-4` + P100 | ~$1.50 | ~15-20s/call | ❌ Old, no bfloat16 support |
| **NVIDIA A100** | 40/80GB | `a2-highgpu-1g` | ~$3.67 | ~2-3s/call | ❌ Quota=0, too expensive |

### Recommendation

**NVIDIA L4 (24GB GDDR6)** is the best option:
- 24GB VRAM fits Qwen3-8B in full precision (16GB model + KV cache)
- Cheapest accelerator-optimized option (~$0.70/hr)
- Ada Lovelace architecture — supports bfloat16, FP8, INT8
- $300 credits = ~428 hours of runtime

**NVIDIA T4 (16GB GDDR6)** is the budget fallback:
- Matches Kaggle T4 hardware exactly
- 16GB VRAM requires 4-bit quantization (bitsandbytes)
- ~$0.55/hr → $300 credits = ~545 hours

---

## Regional GPU Quotas (us-central1)

```
NVIDIA_T4_GPUS:     limit=1
NVIDIA_L4_GPUS:     limit=1
NVIDIA_V100_GPUS:   limit=1
NVIDIA_P100_GPUS:   limit=1
NVIDIA_A100_GPUS:   limit=0  (not available)
```

## GPU Availability by Zone (US only, T4 and L4)

### NVIDIA L4
| Zone | Available |
|------|-----------|
| us-central1-a | ✅ |
| us-central1-b | ✅ |
| us-central1-c | ✅ |
| us-east1-b,c,d | ✅ |
| us-east4-a,c | ✅ |
| us-west1-a,b,c | ✅ |
| us-west4-a,c | ✅ |

### NVIDIA T4
| Zone | Available |
|------|-----------|
| us-central1-a,b,c,f | ✅ |
| us-east1-b,c,d | ✅ |
| us-east4-a,b,c | ✅ |
| us-west1-a,b | ✅ |
| us-west2-b,c | ✅ |
| us-west3-b | ✅ |
| us-west4-a,b | ✅ |

---

## Commands Reference

### 1. Create GPU VM — NVIDIA L4 (Recommended)

```bash
# L4 uses G2 accelerator-optimized machine type (GPU is built-in)
gcloud compute instances create arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a \
  --machine-type=g2-standard-4 \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --image-family=common-gpu \
  --image-project=deeplearning-platform-release \
  --maintenance-policy=TERMINATE \
  --metadata="install-nvidia-driver=True"
```

**g2-standard-4 specs**: 4 vCPUs, 16GB RAM, 1x NVIDIA L4 (24GB)

### 2. Create GPU VM — NVIDIA T4 (Budget Fallback)

```bash
# T4 uses N1 general-purpose + attached GPU
gcloud compute instances create arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a \
  --machine-type=n1-standard-8 \
  --boot-disk-size=100GB \
  --boot-disk-type=pd-balanced \
  --image-family=common-gpu \
  --image-project=deeplearning-platform-release \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --maintenance-policy=TERMINATE \
  --metadata="install-nvidia-driver=True"
```

**n1-standard-8 + T4 specs**: 8 vCPUs, 30GB RAM, 1x NVIDIA T4 (16GB)

### 3. SSH into GPU VM

```bash
gcloud compute ssh arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a
```

### 4. Run Remote Command

```bash
gcloud compute ssh arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a \
  --command="<command>"
```

### 5. SCP Files to GPU VM

```bash
gcloud compute scp /local/path/file.tar.gz \
  arc-solver-gpu:~/file.tar.gz \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a
```

### 6. SCP Files FROM GPU VM

```bash
gcloud compute scp arc-solver-gpu:~/results.json \
  /local/path/results.json \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a
```

### 7. Stop VM (Pause — saves GPU costs, keeps disk)

```bash
gcloud compute instances stop arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a
```

### 8. Start VM (Resume)

```bash
gcloud compute instances start arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a
```

### 9. Delete VM (Permanent — saves all costs)

```bash
gcloud compute instances delete arc-solver-gpu \
  --project=project-f4a684ca-5029-474c-b74 \
  --zone=us-central1-a \
  --quiet
```

### 10. List Running Instances

```bash
gcloud compute instances list \
  --project=project-f4a684ca-5029-474c-b74
```

### 11. Check GPU Quota

```bash
gcloud compute regions describe us-central1 \
  --project=project-f4a684ca-5029-474c-b74 \
  --format="json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for q in data.get('quotas', []):
    n = q.get('metric','')
    if 'GPU' in n.upper() or 'NVIDIA' in n.upper():
        print(f\"{n}: limit={q.get('limit')}, usage={q.get('usage')}\")
"
```

---

## Setup Steps After VM Creation

### Step 1: Verify GPU is available
```bash
nvidia-smi
```

### Step 2: Install Python dependencies
```bash
pip install torch transformers accelerate bitsandbytes sentencepiece protobuf rich jinja2 huggingface_hub
```

### Step 3: Upload solver code
```bash
# From local machine:
gcloud compute scp /tmp/loopagi-solver.tar.gz arc-solver-gpu:~/ \
  --project=project-f4a684ca-5029-474c-b74 --zone=us-central1-a

# On VM:
cd ~ && tar xzf loopagi-solver.tar.gz
```

### Step 4: Download model
```bash
# For L4 (24GB) — full precision:
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('unsloth/Qwen3-8B', local_dir='/home/$USER/qwen3-8b')
"

# For T4 (16GB) — use 4-bit quantized:
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('unsloth/Qwen3-8B-bnb-4bit', local_dir='/home/$USER/qwen3-8b-4bit')
"
```

### Step 5: Smoke test
```bash
python3 -c "
import torch
print(f'CUDA: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f}GB')
"
```

### Step 6: Run evaluation
```bash
cd ~ && PYTHONPATH=. python3 chapter-22/gcp/run_tpu_eval.py \
  --model ~/qwen3-8b \
  --challenges ~/arc-agi_evaluation_challenges.json \
  --tasks 5 \
  --output eval_results.json
```

---

## Deep Learning VM Images

| Image Family | Description |
|-------------|-------------|
| `common-gpu` | General GPU image with CUDA pre-installed |
| `pytorch-latest-gpu` | PyTorch + CUDA pre-installed |
| `tf-latest-gpu` | TensorFlow + CUDA |

Use `--image-family=common-gpu --image-project=deeplearning-platform-release` for the most flexible option.

To list available images:
```bash
gcloud compute images list --project=deeplearning-platform-release --filter="family:common-gpu OR family:pytorch" --format="table(name,family)" | head -20
```

---

## Cost Management

| Action | Cost Impact |
|--------|------------|
| VM running with L4 | ~$0.70/hr |
| VM running with T4 | ~$0.55/hr |
| VM stopped | ~$0.04/hr (disk only) |
| VM deleted | $0.00 |
| 100GB pd-balanced disk | ~$0.10/GB/month |

**Tips**:
- **Stop the VM** when not actively using it (`gcloud compute instances stop`)
- **Delete the VM** when completely done
- Monitor spending: `https://console.cloud.google.com/billing`
- Set budget alerts in Cloud Console to avoid surprises

---

## Troubleshooting

### "Quota exceeded" error
- Check quotas with command #11 above
- Request quota increase in Cloud Console: IAM & Admin → Quotas
- Try a different zone or GPU type

### "ZONE_RESOURCE_POOL_EXHAUSTED"
- Zone is out of capacity for that GPU
- Try another zone (see availability tables above)

### GPU not detected after VM creation
- NVIDIA drivers may still be installing (takes 2-5 min)
- Check: `sudo journalctl -u google-startup-scripts -f`
- Manual install: `sudo /opt/deeplearning/install-driver.sh`

### SSH connection slow
- First SSH takes longer (key exchange)
- Use `--command="..."` for non-interactive commands
- Add `--ssh-flag="-o ServerAliveInterval=30"` for long sessions

### Out of VRAM
- L4 (24GB): Can fit Qwen3-8B full precision + KV cache
- T4 (16GB): Must use 4-bit quantization via bitsandbytes
- Use `torch.cuda.empty_cache()` between tasks
- Use `device_map={"":0}` to force single GPU
