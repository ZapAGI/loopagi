# Coolputer Version B: Full Liquid Block Build

## Every Component Water-Cooled + Chest Freezer Chiller + Server Rack Cage

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Base Unit:** Frigidaire EFRF1013 10 cu ft Black ($413.10)  

---

## Concept

Every heat-generating component gets its own **dedicated water block**:
CPU, GPU, RAM (all 8 DIMMs), NVMe, VRM, and chipset. Chilled coolant
from the freezer's reservoir flows through all blocks in an optimized
parallel/series loop. The motherboard sits in a sealed cold chamber
inside the freezer (air-cooled environment, NOT submerged). An external
server rack cage houses the PSU, radiator, and control systems.

**Key difference from Version A:** Components are NOT submerged. They
are air-cooled in a sealed cold chamber with water blocks providing
precision cooling to each component. This is cleaner, easier to
maintain, and allows standard cable management.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│              FRIGIDAIRE EFRF1013 (BLACK)                   │
│              44"W × 25.4"D × 33.3"H                       │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  UPPER ZONE: COLD CHAMBER (sealed, 10-15°C air)     │  │
│  │                                                     │  │
│  │   Motherboard (EEB, vertical mount)                 │  │
│  │   ├── CPU Water Block (Heatkiller IV PRO TR)        │  │
│  │   ├── GPU Water Block (Bykski RTX 5080)             │  │
│  │   ├── RAM Water Block ×2 (EK Momentum² Quad, 8 DIMMs)│ │
│  │   ├── NVMe Water Block (Alphacool M.2)              │  │
│  │   ├── VRM Water Block (Heatkiller DIY universal)    │  │
│  │   └── Chipset Water Block (universal 40mm)          │  │
│  │                                                     │  │
│  │   120mm recirculation fan (sealed air movement)     │  │
│  │   Desiccant packs (humidity control)                │  │
│  │                                                     │  │
│  └─────────────────────┬───────────────────────────────┘  │
│                        │ THERMAL BARRIER (2" XPS foam)     │
│  ┌─────────────────────┴───────────────────────────────┐  │
│  │  LOWER ZONE: CRYO CORE (freezer-chilled, 0-5°C)    │  │
│  │                                                     │  │
│  │   Stainless steel reservoir (10-15L)                │  │
│  │   D5 Pump                                           │  │
│  │   Coolant: 60% water / 40% propylene glycol         │  │
│  │   Temperature probes (DS18B20)                      │  │
│  │                                                     │  │
│  │   FREEZER EVAPORATOR COILS chill this zone          │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │  Insulated coolant tubing +
                           │  power cables through sealed
                           │  pass-through in side wall
                           ▼
┌──────────────────────────────────────────────────────────┐
│           EXTERNAL SERVER RACK CAGE (12U)                  │
│           Mounted on right side of freezer                 │
│                                                           │
│  ┌─── 1U ───┐  I/O Panel (USB, HDMI, DP, Ethernet)       │
│  ┌─── 2U ───┐  360mm Radiator + 3× 120mm Fans            │
│  ┌─── 1U ───┐  Quick-Connect Tubing Manifold              │
│  ┌─── 2U ───┐  ESP32 Controller + OLED Displays + LEDs    │
│  ┌─── 3U ───┐  PSU (1200W) + Power Distribution           │
│  ┌─── 2U ───┐  Cable Management / Expansion               │
│  ┌─── 1U ───┐  NVMe External Caddy (backup/secondary)     │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## Coolant Flow Path (Parallel + Series Hybrid)

```
CRYO CORE (Reservoir, 0-5°C)
    │
    ▼  D5 Pump
    │
    ├─── BRANCH A (High-Power, Parallel) ─────────────────┐
    │    │                                                 │
    │    ├──▶ CPU Water Block (350W) ──▶──┐               │
    │    │                                 │               │
    │    └──▶ GPU Water Block (300W) ──▶──┤               │
    │                                      │               │
    │                                      ▼               │
    │                                   Y-Merge            │
    │                                      │               │
    ├─── BRANCH B (Low-Power, Series) ─────┤               │
    │    │                                 │               │
    │    ▶ RAM Block L (4 DIMMs) ──▶       │               │
    │    ▶ RAM Block R (4 DIMMs) ──▶       │               │
    │    ▶ NVMe Block ──▶                  │               │
    │    ▶ VRM Block ──▶                   │               │
    │    ▶ Chipset Block ──▶───────────────┘               │
    │                                                      │
    │                      ┌───────────────────────────────┘
    │                      ▼
    │              EXTERNAL RACK
    │              360mm Radiator + Fans
    │              (pre-cools returning coolant)
    │                      │
    │                      ▼
    └──────────── Back to RESERVOIR (Cryo Core)
```

**Why parallel for CPU+GPU:** Both are high-heat components (350W + 300W).
In series, the GPU would receive coolant already warmed by 5-10°C from
the CPU. Parallel ensures both get 0-5°C coolant simultaneously.

**Why series for RAM/NVMe/VRM/Chipset:** These are low-power components
(5-30W each). The slight temperature rise through the series chain is
negligible (~1-2°C per component). Fewer fittings and simpler plumbing.

---

## Water Block Selection (All Components)

| Component | Block | Manufacturer | Connections | Est. Price |
|---|---|---|---|---|
| **CPU (sTR5)** | Heatkiller IV PRO for Threadripper (Cu/Ni) | Watercool | G1/4" in/out | ~$150 |
| **GPU (RTX 5080)** | Bykski Full-Cover Block | Bykski | G1/4" in/out | ~$100 |
| **RAM (4 DIMMs) ×2** | EK-Quantum Momentum² Quad RAM Set D-RGB | EKWB | G1/4" in/out per set | ~$220 ea / $440 |
| **RAM (4 DIMMs) ×2** | Alphacool Core DDR5 (budget alt.) | Alphacool | G1/4" in/out | ~$70 ea / $140 |
| **NVMe M.2** | Alphacool Core M.2 NVMe PCIe 5.0 | Alphacool | G1/4" in/out | ~$50 |
| **VRM** | Heatkiller VRM-Block (universal DIY) | Watercool | G1/4" in/out | ~$60 |
| **Chipset** | Barrow Universal 40mm Chipset Block | Barrow | G1/4" in/out | ~$25 |

**Premium path (EK RAM):** CPU + GPU + RAM(EK) + NVMe + VRM + Chipset = **~$825**  
**Budget path (Alphacool RAM):** CPU + GPU + RAM(AC) + NVMe + VRM + Chipset = **~$525**

---

## Fitting & Tubing Requirements

With 7 water blocks, you need significantly more fittings than a standard loop:

| Item | Qty | Price/ea | Total |
|---|---|---|---|
| G1/4" Compression Fittings (10/16mm) | 22 | ~$4.50 | ~$99 |
| G1/4" 90° Rotary Fittings | 8 | ~$6 | ~$48 |
| G1/4" Y-Splitter (for parallel branches) | 2 | ~$8 | ~$16 |
| G1/4" Ball Valve (drain) | 2 | ~$10 | ~$20 |
| G1/4" Fill Port + Plug | 1 | ~$6 | ~$6 |
| G1/4" Quick-Disconnect Set (rack ↔ freezer) | 2 | ~$15 | ~$30 |
| EK-Tube ZMT 15.9/9.5mm (3m) | 3 | ~$18 | ~$54 |
| **Fittings + Tubing Subtotal** | | | **~$273** |

**Quick-disconnect fittings** at the rack pass-through allow you to
disconnect the external radiator loop from the internal freezer loop
for maintenance without draining the entire system.

---

## Cold Chamber Design (Upper Zone)

The motherboard sits in the **upper zone** of the freezer, separated
from the cryo core by a 2" XPS foam thermal barrier.

**Chamber temperature:** 10-15°C (passively chilled by proximity to
cryo core + insulated from outside ambient). The water blocks do the
actual component cooling — the chamber air just needs to be cool enough
to prevent condensation issues.

**Motherboard mounting:**
- Vertical mount on 2020 aluminum extrusion frame
- EEB tray bolted to extrusion
- GPU on PCIe riser cable, mounted parallel to motherboard
- All water blocks installed before mounting frame in freezer

**Sealed chamber:**
- XPS foam barrier below (to cryo core)
- Freezer walls on 3 sides (already insulated)
- Removable XPS foam lid on top (under freezer lid)
- Cable pass-through with sealed grommets to external rack
- Coolant tubing pass-through with foam-insulated penetrations

**Humidity control:**
- Sealed chamber drastically limits humidity ingress
- Desiccant packs (silica gel, 50g × 4) absorb residual moisture
- DHT22 sensor monitors humidity — alert if >60% RH
- Conformal coating on motherboard around socket area as final defense

---

## External Rack: Radiator + PSU + I/O

### Why the Radiator Is in the Rack (Not the Freezer)

The 360mm radiator generates **warm exhaust air** (30-40°C). Putting
it inside the freezer would force the compressor to fight that heat.
By placing it in the external rack:
- Warm air exhausts to room ambient
- Freezer compressor only handles residual heat in the coolant
- Radiator pre-cools returning coolant by 10-20°C before it enters
  the cryo reservoir

### Rack Layout (12U)

```
┌─────────────────────────────────────┐
│ 1U  │ I/O Panel                      │  ← USB, HDMI, DP, Ethernet
├─────┤                                │     panel-mount bulkheads
│ 2U  │ 360mm Radiator (horizontal)    │  ← 3× Arctic P12 fans
│     │ + Fan shroud                   │     push config, exhaust up
├─────┤                                │
│ 1U  │ Quick-Connect Manifold         │  ← QD fittings for coolant
│     │ + Flow indicator               │     easy maintenance disconnect
├─────┤                                │
│ 2U  │ ESP32 + 2× OLED + LED ctrl    │  ← Monitoring + dew point
│     │ + STC-1000 backup thermostat   │     control + RGB
├─────┤                                │
│ 3U  │ ATX PSU (1200W)               │  ← Fan exhaust rear
│     │ + Power distribution           │     surge protector
│     │ + Cable management             │
├─────┤                                │
│ 2U  │ Expansion / Storage            │  ← Secondary NVMe caddy
│     │ + Spare cables                 │     future add-ons
├─────┤                                │
│ 1U  │ Blank / Ventilation            │
└─────────────────────────────────────┘
```

---

## Expected Performance

| Metric | Standard AIO | Coolputer V1 (5-zone) | Coolputer V-B (full block) |
|---|---|---|---|
| **CPU Full Load** | 70-85°C | 40-55°C | **25-40°C** |
| **GPU Full Load** | 65-80°C | 50-70°C (air in zone) | **25-40°C** |
| **RAM** | 60-95°C | 60-95°C (uncooled) | **10-20°C** |
| **NVMe** | 50-70°C | 50-70°C (uncooled) | **10-20°C** |
| **VRM** | 60-90°C | 60-90°C (uncooled) | **10-20°C** |
| **Components cooled** | CPU only | CPU + maybe GPU | **ALL 7 components** |

**The key advantage of Version B** over Version A (submersion) and
Version V1 (basic zones): **Every single heat source has precision
liquid cooling at sub-ambient temperatures.** The RAM, NVMe, and VRM
cooling is particularly important for the WRX90E-SAGE SE, where DDR5
RDIMMs can hit 95°C without active cooling.

---

## Parts List — Version B Full Liquid Block

### Cooling System

| # | Item | Qty | Est. Price | Source |
|---|---|---|---|---|
| 1 | Frigidaire EFRF1013 10 cu ft Black | 1 | **$413.10** | Home Depot Midtown Manhattan |
| 2 | Heatkiller IV PRO TR (Cu/Ni) — CPU | 1 | ~$150 | Watercool / Newegg |
| 3 | Bykski RTX 5080 Full-Cover Block — GPU | 1 | ~$100 | Amazon |
| 4 | EK-Quantum Momentum² Quad RAM Set D-RGB | 2 | ~$440 | EKWB |
| 5 | Alphacool Core M.2 NVMe PCIe 5.0 — NVMe | 1 | ~$50 | Alphacool / Amazon |
| 6 | Heatkiller VRM-Block Universal — VRM | 1 | ~$60 | Watercool |
| 7 | Barrow Universal Chipset Block — Chipset | 1 | ~$25 | Amazon |
| 8 | Barrow D5 Pump + Top | 1 | ~$75 | Amazon |
| 9 | All Fittings + Tubing (see table above) | — | ~$273 | Amazon |
| 10 | Stainless Steel Reservoir 10L | 1 | ~$30 | Amazon |
| 11 | Propylene Glycol (1 gal) + Distilled Water + Biocide | — | ~$35 | Amazon / Local |
| 12 | XPS Foam Board 2" (barriers) | 1 sheet | ~$30 | Home Depot |
| 13 | Spray Foam + Weatherstripping + Neoprene | — | ~$40 | Home Depot |
| 14 | Pipe Insulation Foam (all cold tubing) | 6 | ~$18 | Home Depot |
| 15 | Conformal Coating (MG 419D) | 1 | ~$18 | Amazon |
| 16 | 2020 Aluminum Extrusion Kit (frame) | 1 | ~$30 | Amazon |
| 17 | EEB Motherboard Tray + Hardware | 1 | ~$40 | Mountain Mods |
| 18 | PCIe 5.0 Riser Cable 300mm | 1 | ~$40 | Amazon |
| | **Internal Cooling Subtotal** | | **~$1,870** | |

### External Server Rack

| # | Item | Qty | Est. Price | Source |
|---|---|---|---|---|
| 19 | NavePoint 12U Open Frame Rack | 1 | ~$90 | Amazon |
| 20 | Alphacool NexXxoS 360mm Radiator | 1 | ~$65 | Amazon |
| 21 | Arctic P12 PWM PST (5-pack) | 1 | ~$30 | Amazon |
| 22 | Quick-Disconnect Fittings (set of 2) | 2 | ~$30 | Amazon |
| 23 | ATX PSU Rack Shelf (2U) | 1 | ~$15 | Amazon |
| 24 | USB/HDMI/DP/Ethernet Panel Mount | 1 set | ~$25 | Amazon |
| 25 | ESP32 + Sensors + OLEDs + LEDs + Relay | 1 kit | ~$50 | Amazon |
| 26 | STC-1000 Thermostat | 1 | ~$12 | Amazon |
| 27 | L-Brackets + Bolts + Vibration Isolators | 1 set | ~$20 | Home Depot |
| 28 | Illuminated Power Button | 1 | ~$8 | Amazon |
| | **External Rack Subtotal** | | **~$345** | |

### Total

| Category | Cost |
|---|---|
| **Cooling System (internal)** | ~$1,870 |
| **External Rack** | ~$345 |
| **Version B Total (case + cooling)** | **~$2,215** |

### Grand Total with PC Components

| Component | Price |
|---|---|
| Coolputer Version B (above) | ~$2,215 |
| TR PRO 9965WX (24C/48T) | $2,699.99 |
| ASUS Pro WS WRX90E-SAGE SE | ~$1,099 |
| 256GB DDR5 ECC RDIMM (8×32GB) | ~$1,000 |
| 1200W PSU (80+ Platinum) | ~$250 |
| RTX 5080 (reuse) | — |
| 2TB NVMe (reuse) | — |
| **Grand Total** | **~$7,265** |

---

## Version B vs Version A Comparison

| Feature | Version A (Submersion) | Version B (Full Block) |
|---|---|---|
| **Cooling method** | Mineral oil immersion | Water blocks on every component |
| **Components in fluid?** | Yes — fully submerged | No — air + liquid blocks |
| **Maintenance** | Messy (oil changes) | Clean (coolant flush) |
| **Component swap** | Drain oil → messy | Drain loop → clean |
| **RAM/VRM cooling** | Excellent (fluid contact) | Excellent (dedicated blocks) |
| **Noise** | Near silent | Near silent (only rad fans) |
| **Aesthetics** | Components in oil = unique | Clean build, RGB RAM blocks |
| **Cost (cooling only)** | ~$920 | ~$2,215 |
| **Complexity** | Medium | Hard (many blocks + fittings) |
| **Best for** | YouTube wow factor | Daily driver, easy maintenance |

---

*Coolputer Version B — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
