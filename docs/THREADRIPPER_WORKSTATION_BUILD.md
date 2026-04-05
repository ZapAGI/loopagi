# Threadripper PRO Workstation Build

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**Goal:** AMD Threadripper PRO 9965WX (24-core) reference build + ASUS WRX90E-SAGE SE  
**Selected CPU:** Threadripper PRO 9965WX — **$2,699.99 at Micro Center** (SKU: 900050, IN STOCK)

---

## Newest Models: Threadripper PRO 9000 WX (Shimada Peak)

Released **July 23, 2025**. Zen 5 architecture. Drop-in compatible with
WRX90 boards via BIOS update. Up to 26% faster than 7000 WX series.

### Full 9000 WX Lineup

| CPU | Cores | Boost | L3 Cache | TDP | MSRP | Micro Center |
|---|---|---|---|---|---|---|
| **PRO 9995WX** | **96C/192T** | 5.4 GHz | 384 MB | 350W | **$11,699** | [Link](https://www.microcenter.com/product/698655) |
| **PRO 9985WX** | **64C/128T** | 5.4 GHz | 256 MB | 350W | **$7,999** | [Link](https://www.microcenter.com/product/698656) |
| PRO 9975WX | 32C/64T | 5.4 GHz | 128 MB | 350W | $4,099 | [Link](https://www.microcenter.com/product/698657) |
| **PRO 9965WX** | **24C/48T** | **5.4 GHz** | **128 MB** | **350W** | **$2,899** | **[MC Link](https://www.microcenter.com/product/698658) — $2,699.99 IN STOCK ✓** |
| PRO 9955WX | 16C/32T | 5.4 GHz | 64 MB | 350W | $1,649 | Listed |
| PRO 9945WX | 12C/24T | 5.4 GHz | 64 MB | 350W | TBD | — |

### Previous Gen: 7000 WX (Storm Peak) — Cheaper, Still Great

| CPU | Cores | Boost | L3 Cache | TDP | MSRP |
|---|---|---|---|---|---|
| **PRO 7995WX** | **96C/192T** | 5.1 GHz | 384 MB | 350W | **$9,999** |
| **PRO 7985WX** | **64C/128T** | 5.1 GHz | 256 MB | 350W | **$7,349** |
| PRO 7975WX | 32C/64T | 5.3 GHz | 128 MB | 350W | $3,899 |

---

## Reference Build: Threadripper PRO 9965WX (24-Core)

| Spec | Detail |
|---|---|
| **Model** | AMD Ryzen Threadripper PRO 9965WX |
| **Codename** | Shimada Peak |
| **Architecture** | Zen 5 |
| **Cores / Threads** | 24 / 48 |
| **Base Clock** | 4.2 GHz |
| **Boost Clock** | 5.4 GHz |
| **L3 Cache** | 128 MB |
| **TDP** | 350W |
| **Socket** | sTR5 (LGA 6096) |
| **MSRP** | $2,899 |
| **Micro Center Price** | **$2,699.99** (SKU: 900050) |
| **Stock** | **1 IN STOCK** |

**Why 24 cores is the sweet spot for a reference system:**
- 24C/48T is **6× your current i7-7700** (4C/8T) — massive parallelism upgrade
- 5.4 GHz boost + Zen 5 IPC = excellent single-thread for LLM prompt processing
- 128 MB L3 cache = strong for data-heavy workloads
- 350W TDP = same cooling/PSU as any Threadripper PRO (scales to 96-core later)
- **$2,699.99** vs $7,999 (64-core) = save **$5,300** — reinvest in RAM/storage
- Same sTR5 socket = **drop-in upgrade to 64 or 96 cores later** without changing anything else
- Puget Systems: ~17% generational uplift over 7965WX in LLM prompt processing

> **Key insight:** LLM inference is GPU-bound (your RTX 5080 does the heavy
> lifting). 24 cores is more than enough for data prep, code compilation,
> fine-tuning orchestration, and running the full ZapAGI/LoopAGI stack.
> The WRX90 platform lets you upgrade to 64/96 cores later if needed.

---

## Future Upgrade Path (Same Socket, Same Board)

| Upgrade | Cores | Price | When |
|---|---|---|---|
| PRO 9975WX | 32C/64T | $4,099 | When you need more compile/render speed |
| PRO 9985WX | 64C/128T | $7,999 | When you need massive parallelism |
| PRO 9995WX | 96C/192T | $11,699 | Maximum compute density |

All are drop-in replacements on the ASUS WRX90E-SAGE SE — no new board,
RAM, cooler, or PSU needed.

---

## Motherboard: ASUS Pro WS WRX90E-SAGE SE

| Spec | Detail |
|---|---|
| **Socket** | sTR5 (LGA 6096) |
| **Chipset** | WRX90 |
| **Form Factor** | **EEB (305mm × 330mm)** ⚠️ Bigger than ATX! |
| **CPU Support** | Threadripper PRO 9000 & 7000 WX-Series |
| **PCIe Slots** | 7× PCIe 5.0 x16 |
| **PCIe Lanes** | 128 usable PCIe 5.0 |
| **Memory** | 8-channel DDR5 ECC RDIMM, up to 2TB |
| **Memory Speed** | DDR5-6400 (with 9000 WX) |
| **M.2 Slots** | 4× PCIe 5.0 M.2 |
| **Networking** | 10Gb + 2.5Gb LAN |
| **VRM** | 32+3+3+3 power stages |
| **BIOS for 9000** | Version 1106+ required |
| **Special** | IPMI/BMC for remote BIOS flash |

**Pricing:**

| Store | Price | Link |
|---|---|---|
| **Micro Center** | ~$1,099 | [microcenter.com/product/677978](https://www.microcenter.com/product/677978/asus-wrx90e-sage-pro-ws-se-amd-str5-eeb-motherboard) |
| **Newegg** | ~$1,099-1,199 | [newegg.com](https://www.newegg.com/asus-pro-ws-wrx90e-sage-se-eeb-motherboard-amd-wrx90-str5/p/N82E16813119667) |
| **Amazon** | ~$1,099-1,199 | [amazon.com](https://www.amazon.com/Pro-WRX90E-SAGE-Workstation-Motherboard-ThreadripperTM/dp/B0CQRYXWWQ) |

---

## ⚠️ Custom Case: EEB Form Factor Warning

**The WRX90E-SAGE SE is EEB, NOT ATX.**

| Form Factor | Size | Notes |
|---|---|---|
| ATX | 305 × 244mm | Standard desktop |
| **EEB** | **305 × 330mm** | **86mm taller than ATX!** |
| E-ATX | 305 × 330mm | Same as EEB essentially |

Your custom case from the previous parts list needs to be adjusted:
- **Taller frame:** Add ~90mm height for the extra motherboard length
- **Motherboard tray:** Mountain Mods ATX tray WON'T fit — need EEB/E-ATX tray
- **Mountain Mods EEB tray:** Available at [mountainmods.com](https://www.mountainmods.com)
- **Standoff pattern:** EEB uses additional mounting holes beyond ATX
- **Minimum internal height:** 350mm+ for motherboard + cable clearance
- **Frame recommendation:** 500mm × 400mm × 500mm (W×D×H) for this build

---

## Memory: DDR5 ECC RDIMM (NOT Desktop DDR5)

**CRITICAL:** WRX90 requires **ECC Registered DIMMs (RDIMMs)** — regular
desktop DDR5 will NOT work. 8-channel memory for massive bandwidth.

| Config | Capacity | Channels | Bandwidth | Est. Price |
|---|---|---|---|---|
| 8×32GB DDR5-5600 RDIMM | **256GB** | 8-ch | ~358 GB/s | ~$800-1,200 |
| 8×64GB DDR5-5600 RDIMM | **512GB** | 8-ch | ~358 GB/s | ~$1,800-2,400 |
| 8×96GB DDR5-5600 RDIMM | **768GB** | 8-ch | ~358 GB/s | ~$3,000-4,000 |
| 8×128GB DDR5-5600 RDIMM | **1TB** | 8-ch | ~358 GB/s | ~$5,000+ |

**Recommended:** Start with **256GB (8×32GB)** — enough for any LLM
fine-tuning, multi-model inference, and massive dataset processing.
Upgrade to 512GB+ later if you need to run 70B+ models on CPU.

Brands to look for: **Samsung, SK Hynix, Micron** server-grade RDIMMs.
Check the [ASUS QVL](https://www.asus.com/us/motherboards-components/motherboards/workstation/pro-ws-wrx90e-sage-se/) for validated kits.

---

## Cooling: 350W TDP Demands Serious Cooling

The Threadripper PRO 9965WX draws up to **350W** sustained. You need a
high-end cooling solution with an **sTR5 bracket** (larger than AM5).
Note: 24 cores at 350W means more thermal headroom per core than 64/96-core
models — your cooler will handle this more easily.

| Cooler | Type | Coverage | Est. Price | Notes |
|---|---|---|---|---|
| **SilverStone IceGem 360** | 360mm AIO | Full sTR5 IHS | ~$150 | Popular TR choice |
| **ARCTIC Liquid Freezer III 360** | 360mm AIO | sTR5 kit needed | ~$120 | Excellent value |
| **Noctua NH-U14S TR5-SP6** | Air | sTR5 native | ~$110 | Silent, but may limit all-core boost |
| **Custom Loop** | Water | Full coverage | ~$300-500 | Best thermals, quietest |

**Recommendation:** 360mm AIO minimum. Custom loop if you want to sustain
full 350W boost on all 24 cores indefinitely.

---

## PSU: 1200W+ Required

| Load | Watts |
|---|---|
| CPU (TR PRO 9965WX) | up to 350W |
| GPU (RTX 5080) | up to 300W |
| RAM (8×RDIMM) | ~40W |
| Storage, fans, etc. | ~50W |
| **Total peak** | **~740W** |
| **Recommended PSU** | **1200W+ (80+ Platinum)** |

Headroom matters for transient spikes. 1200W gives comfortable overhead.

| PSU | Rating | Price |
|---|---|---|
| **Corsair HX1200i** | 1200W Platinum | ~$250 |
| **Seasonic PRIME TX-1300** | 1300W Titanium | ~$350 |
| **be quiet! Dark Power Pro 13** | 1300W Titanium | ~$350 |

---

## Complete Build Summary

### Reference Build: 24-Core Threadripper PRO 9965WX

| Component | Choice | Est. Price | Where |
|---|---|---|---|
| **CPU** | AMD TR PRO 9965WX (24C/48T) | **$2,699.99** | [Micro Center SKU:900050](https://www.microcenter.com/product/698658) |
| **Motherboard** | ASUS Pro WS WRX90E-SAGE SE | ~$1,099 | [Micro Center](https://www.microcenter.com/product/677978) |
| **RAM** | 256GB DDR5-5600 ECC RDIMM (8×32GB) | ~$1,000 | Newegg/Amazon |
| **CPU Cooler** | 360mm AIO (sTR5 bracket) | ~$150 | Amazon |
| **PSU** | 1200W+ 80+ Platinum | ~$250 | Amazon |
| **GPU** | RTX 5080 16GB (reuse) | — | Already owned |
| **NVMe** | 2TB Lexar XG7000 (reuse) | — | Already owned |
| **Case** | Custom build (EEB compatible) | varies | DIY |
| | **Total (excl. case)** | **~$5,200** | |

### What This Gets You vs Current System

| Metric | Current (i7-7700) | Threadripper PRO 9965WX | Improvement |
|---|---|---|---|
| **Cores/Threads** | 4C / 8T | 24C / 48T | **6× cores** |
| **CPU Boost** | 4.2 GHz (Kaby Lake) | 5.4 GHz (Zen 5) | ~60% IPC + higher clock |
| **PCIe** | Gen 3 ×8 (7.9 GB/s) | Gen 5 ×16 (63 GB/s) | **8× bandwidth** |
| **RAM** | 64GB DDR4-2133 (34 GB/s) | 256GB DDR5-5600 8-ch (358 GB/s) | **10× bandwidth** |
| **PCIe Lanes** | 16 total | 128 usable | **8× lanes** |
| **Multi-GPU** | 1 slot | 7× PCIe 5.0 x16 | Future multi-GPU AI |
| **Memory Max** | 64GB | 2TB | **32× capacity** |

### Impact on ZapAGI / LoopAGI Development

| Workload | Improvement |
|---|---|
| **LLM inference (Ollama)** | Same (GPU-bound) — but model loading 10× faster |
| **LoRA fine-tuning** | Data prep 6× faster, PCIe bottleneck eliminated |
| **CPU LLM inference (70B+ models)** | Now possible — 256GB+ RAM for full model in memory |
| **Parallel eval (ARC 120 tasks)** | 6× cores for data prep parallelism |
| **Code compilation** | 4-6× faster (24 cores vs 4) |
| **Multi-model routing** | 8-ch memory bandwidth for rapid model switching |
| **Future: multi-GPU** | 7 PCIe 5.0 x16 slots for additional GPUs |
| **Future: CPU upgrade** | Drop-in to 64C or 96C on same board |

---

## Micro Center Shopping List

All items available at Micro Center (check in-store stock):

| # | Item | SKU | MC Price | MC Link |
|---|---|---|---|---|
| 1 | **TR PRO 9965WX** (24C) | **900050** | **$2,699.99** | [Link](https://www.microcenter.com/product/698658) |
| 2 | **ASUS WRX90E-SAGE SE** | 677978 | ~$1,099 | [Link](https://www.microcenter.com/product/677978) |
| | **MC Subtotal (CPU+Board)** | | **~$3,799** | |

> **Micro Center Tip:** They often bundle CPU + motherboard at a discount
> ($20-50 off). Ask in-store about combo pricing.

The DDR5 ECC RDIMMs, cooler, and PSU are likely cheaper on Newegg/Amazon.

---

## Sources

- Tom's Hardware: [TR PRO 9000 WX Launch](https://www.tomshardware.com/pc-components/cpus/amd-launches-threadripper-pro-9000-wx-series-cpus-with-up-to-96-zen-5-cores-for-usd11-699-shimada-peak-and-radeon-ai-pro-r9700-arrive-on-july-23)
- Puget Systems: [TR PRO 9000WX Content Creation Review](https://www.pugetsystems.com/labs/articles/amd-ryzen-threadripper-pro-9000wx-content-creation-review/)
- ASUS: [WRX90E-SAGE SE Specs](https://www.asus.com/us/motherboards-components/motherboards/workstation/pro-ws-wrx90e-sage-se/techspec/)
- ASUS: [WRX90E-SAGE SE BIOS](https://www.asus.com/motherboards-components/motherboards/workstation/pro-ws-wrx90e-sage-se/helpdesk_bios?model2Name=Pro-WS-WRX90E-SAGE-SE) (v1106+ for 9000 WX support)

---

*Threadripper PRO Workstation Build — Copyright 2026 Alexandros Karales / ZapAGI.*
