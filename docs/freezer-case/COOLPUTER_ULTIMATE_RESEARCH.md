# Coolputer Ultimate — Deep Research: Modular + Glycol + Full Blocks

## The Definitive Build for a Permanent Keeper AI Workstation

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Build Philosophy:** Fresh components, permanent keeper, no recycled parts  
**Chosen Method:** Modular multi-freezer + propylene glycol loop + full liquid blocks + car heater core HX  

---

## CRITICAL FINDING: The Compressor Capacity Problem

### The Math That Changes Everything

A typical 10 cu ft chest freezer (including our Frigidaire EFRF1013)
has a **1/4 to 1/3 HP compressor** with a cooling capacity of:

- **~800-1,500 BTU/hr** = **~235-440W of heat removal**

Our Threadripper PRO 9965WX + RTX 5080 at full load generates:

- **CPU:** 350W TDP
- **GPU:** 300W TDP  
- **VRM/RAM/NVMe/Chipset:** ~50W combined
- **D5 Pump:** ~20W
- **Total:** **~720W of heat**

**The freezer compressor can only remove 235-440W. Our PC generates 720W.**

This means at sustained full load, the compressor runs 100% and
**cannot keep up** — coolant temperature will slowly rise until it
reaches thermal equilibrium well above ambient. The freezer alone
is not enough.

### The Solution: Dual-Stage Cooling (MANDATORY)

This is why the car heater core heat exchanger you already have is
**not optional — it's essential.** We need TWO stages of cooling:

```
┌─────────────────────────────────────────────────────┐
│                   DUAL-STAGE COOLING                 │
│                                                       │
│  STAGE 1: Car Heater Core + Fans (External Rack)     │
│  ├── Removes: ~300-500W (depending on airflow/ΔT)    │
│  ├── Cools returning hot coolant from ~35°C → ~25°C   │
│  └── Reduces load on freezer compressor               │
│                                                       │
│  STAGE 2: Copper Coil in Freezer (Cold Zone)          │
│  ├── Removes: ~300-440W (compressor capacity)         │
│  ├── Chills coolant from ~25°C → ~5-10°C              │
│  └── Delivers sub-ambient coolant to blocks           │
│                                                       │
│  COMBINED: 600-940W removal capacity > 720W load      │
│  ✅ System can sustain full load indefinitely          │
└─────────────────────────────────────────────────────┘
```

**Without the heater core, the build WILL overheat under sustained
AI workloads.** Every previous "PC in a freezer" project that failed
hit this exact problem — they assumed the freezer could handle the
full heat load alone.

---

## Propylene Glycol Coolant — The Science

### Why Propylene Glycol (PG), Not Ethylene Glycol (EG)

| Property | Propylene Glycol | Ethylene Glycol |
|---|---|---|
| **Toxicity** | Non-toxic (food grade) | **Toxic / lethal** |
| **Thermal conductivity** | Slightly lower | Higher |
| **Viscosity** | Higher (more pump work) | Lower |
| **Cost** | ~$7/gal (RV antifreeze) | ~$12/gal (automotive) |
| **Verdict** | **Use this** — safe, cheap, available at HD | Avoid — one leak = poison |

### PG Concentration vs Performance

Based on Dynalene technical data and Alliance Chemical engineering guides:

| PG Concentration | Freeze Point | Thermal Conductivity | Specific Heat | Viscosity at 5°C | Verdict |
|---|---|---|---|---|---|
| **0% (pure water)** | 0°C | 0.60 W/mK | 4.18 kJ/kgK | 1.5 cP | Freezes in our system! |
| **20%** | -8°C | 0.52 W/mK | 4.02 kJ/kgK | 3.0 cP | Marginal freeze protection |
| **30%** | -13°C | 0.46 W/mK | 3.90 kJ/kgK | 4.5 cP | **Best balance** — good thermal + safe margin |
| **40%** | -22°C | 0.41 W/mK | 3.70 kJ/kgK | 7.0 cP | Safe but noticeably thicker |
| **50%** | -33°C | 0.37 W/mK | 3.50 kJ/kgK | 12.0 cP | Overkill — too viscous, poor thermal |

### Recommended: 30% Propylene Glycol

- **Freeze protection to -13°C** — our coolant runs ~5-15°C under load,
  never reaches -13°C. If the PC is OFF and freezer runs, coolant
  could drop to -18°C → close to danger zone. Solution: STC-1000
  thermostat limits freezer to -10°C minimum.
- **Thermal conductivity: 0.46 W/mK** — 77% of pure water. Acceptable.
- **Viscosity: 4.5 cP at 5°C** — D5 pump handles this easily (rated
  for glycol solutions up to 50%).
- **Specific heat: 3.90 kJ/kgK** — 93% of water. Excellent thermal mass.

### Coolant Recipe

```
COOLPUTER GLYCOL COOLANT — 30% PG
──────────────────────────────────
For 5 liters total:
  • 1.5L propylene glycol (USP grade or RV antifreeze)
  • 3.5L distilled water
  • 1× silver kill coil (antimicrobial) OR 3 drops Mayhems biocide
  • Optional: 1 drop blue/green dye for leak visibility

Sources:
  • Prime Guard RV Antifreeze (HD #314176974) — $7/gal (premixed ~50% PG)
    → Use 3L of this + 2L distilled water = ~30% PG
  • OR Pure PG USP (Amazon, Sanco) — $22/gal (100% PG)
    → Use 1.5L PG + 3.5L distilled water = 30% PG
```

---

## CPU Water Block: The sTR5 (LGA4844) Problem

### Socket Compatibility Crisis

The AMD Threadripper PRO 9000 series uses the **sTR5 (LGA4844)** socket.
This is the SAME socket as Threadripper PRO 7000 series.

**Critical finding from Level1Techs forum + Reddit r/threadripper:**

| Water Block | Socket | Fits sTR5? | Price | Notes |
|---|---|---|---|---|
| **Watercool Heatkiller IV PRO for TR** | sTR4 | **Bracket adapter needed** | ~$130-150 | Premium quality. sTR4 block fits sTR5 with Asetek-compatible bracket (included in AMD box). Confirmed working by community. |
| **Comino WCB Set for WRX90E-SAGE SE** | sTR5 | **YES — purpose-built** | ~$200-300 (est.) | **Only dedicated WRX90E VRM+CPU block set.** But requires 50-unit minimum order. Not available for single purchase as of early 2025. |
| **Bykski CPU-XPR-C-M** | AM4/AM5 | **NO** | ~$45 | AM4/AM5 only, does NOT fit Threadripper |
| **EK Magnitude Threadripper** | sTR4 | **Bracket adapter needed** | ~$180-220 | Works with sTR5 via Asetek bracket. |
| **Alphacool Eisblock XPX Aurora TR** | sTR4/sTR5 | **YES** | ~$90-110 | Budget option. Confirmed sTR5 compatible. |

### Recommendation: Watercool Heatkiller IV PRO for Threadripper

- **Best-in-class cooling** for the massive Threadripper IHS
- **Pure copper cold plate** with precision-milled microchannels
- **G1/4" threads** (×4 ports) — standard PC fitting compatibility
- **sTR4 mounting** → fits sTR5 with Asetek-compatible bracket (in AMD box)
- **Flow restriction:** Moderate (~0.15 bar drop at 1 GPM)
- Price: ~$130-150 from watercool.de or performance-pcs.com

### Budget Alternative: Alphacool Eisblock XPX Aurora TR

- Confirmed sTR5 compatible
- ~$90-110, available on Amazon
- Copper cold plate, G1/4" threads
- Slightly less cooling performance than Heatkiller

---

## VRM Water Cooling: The WRX90E-SAGE SE Challenge

### The Problem

The ASUS WRX90E-SAGE SE has a **massive** VRM section — 16+2 power
stages spread across two large heatsink areas. No off-the-shelf VRM
block fits this exact board.

### Options

| Approach | Cost | Difficulty | Effectiveness |
|---|---|---|---|
| **Comino WCB VRM Coldplate** | ~$100-200 | Easy (purpose-built) | Excellent — but 50-unit MOQ |
| **Universal VRM Blocks (×2)** | ~$50-80 total | Medium (DIY fit) | Good — need thermal pad shimming |
| **Copper Shim + Thermal Tape** | ~$15-20 | Easy | Moderate — passive improvement |
| **Keep Stock Heatsinks + Fan** | $0 | None | Adequate if case airflow exists |

### Recommended: Keep Stock VRM Heatsinks + Add Airflow

The WRX90E-SAGE SE comes with **chunky VRM heatsinks** and a
**dedicated VRM fan header** (pre-connected). In a freezer at 0-5°C
ambient, these stock heatsinks will work excellently. The cold air
inside the freezer chamber handles VRM cooling passively.

**Skip the VRM water blocks.** The complexity and cost of fitting
universal blocks to this specific board isn't worth it when the
entire chamber is at near-freezing temperatures. Focus water cooling
budget on CPU + GPU where the real heat is.

---

## Car Heater Core Integration (Stage 1 Heat Exchanger)

### What You Already Have

You mentioned you have a water-to-air car-style heat exchanger
radiator already. This is the most critical component in the
dual-stage system.

### Typical Car Heater Core Specs

| Spec | Value |
|---|---|
| **Size** | ~6-8" × 6-8" × 2-3" |
| **Material** | Copper tubes + aluminum fins, or all-aluminum |
| **Inlet/Outlet** | 5/8" barb (standard automotive) |
| **Capacity** | 5-10 kW (massively overkill for 720W) |
| **Flow restriction** | Very low (designed for high-flow automotive pumps) |

### Connecting Heater Core to PC Loop

The challenge: PC water blocks use **G1/4" threads** with 3/8" ID
tubing. Heater cores use **5/8" barbs**.

**Adapter Chain:**
```
PC Block (G1/4") → Barrow G1/4" to 3/8" barb → 3/8" ID tubing
→ 3/8" to 5/8" barb reducer → 5/8" silicone hose (6")
→ Heater Core 5/8" inlet
→ Heater Core 5/8" outlet → 5/8" to 3/8" barb reducer
→ 3/8" ID tubing → Next component
```

**Parts needed (Amazon):**
- 2× 5/8" to 3/8" barb reducer (brass, ~$4 each)
- 1 ft of 5/8" silicone hose (for the short heater core connection)
- 2× hose clamps (5/8" size)
- Total: **~$15**

### Fan Setup for Heater Core

Mount 2-3× 120mm fans (Arctic P12) on one side of the heater core
using zip ties or a 3D-printed shroud. This creates an active
air-to-water heat exchanger capable of removing 300-500W.

**Key insight:** The heater core sits in the **external rack** at
room temperature (~22°C ambient). Your coolant returns from the PC
blocks at ~30-40°C. The heater core + fans cool it to ~25-28°C
BEFORE it enters the freezer cold zone. This dramatically reduces
the load on the freezer compressor.

---

## Optimal Loop Design: Dual-Branch with Dual-Stage Cooling

### Why Dual-Branch?

With 5+ water blocks in the loop, a single D5 pump experiences
significant flow restriction. Forums (HardForum, Overclock.net)
consistently show:

- **1-3 blocks:** Single D5 at ~150-200 L/hr — excellent
- **4-5 blocks:** Single D5 at ~80-120 L/hr — adequate
- **6-7 blocks:** Single D5 at ~50-80 L/hr — marginal

With 5 components (CPU, GPU, 2×RAM, NVMe) plus the heater core
and copper coil, we have significant restriction. Solution:
**split into two parallel branches.**

### The Coolputer Ultimate Flow Path

```
                    ┌──────────────────────────┐
                    │    EXTERNAL RACK          │
                    │  ┌──────────────────┐     │
                    │  │ CAR HEATER CORE  │     │
                    │  │ + 3× 120mm FANS  │     │
     HOT RETURN ────┤  │ (Stage 1: ~35→25°C)   │
     (~35°C)        │  └────────┬─────────┘     │
                    │           │                │
                    │     ┌─────┤ D5 PUMP        │
                    │     │     │ (in reservoir)  │
                    │     │     │                │
                    └─────┼─────┼────────────────┘
                          │     │
          ═══ INSULATED TUBING PASS-THROUGH ═══
                          │     │
                    ┌─────┼─────┼────────────────┐
                    │     │  FREEZER COLD ZONE    │
                    │     │                       │
                    │  ┌──┴──────────────────┐    │
                    │  │  COPPER COIL         │    │
                    │  │  (20ft 3/8" in cold) │    │
                    │  │  Stage 2: ~25→5°C    │    │
                    │  └──┬──────────────────┘    │
                    │     │                       │
                    │  ┌──┴──┐    ┌──────────┐    │
                    │  │ Y   │    │ BRANCH B │    │
                    │  │SPLIT│───►│ GPU Block│    │
                    │  │     │    │ RAM ×2   │    │
                    │  └──┬──┘    │ NVMe     │    │
                    │     │       └────┬─────┘    │
                    │  ┌──┴──────┐     │          │
                    │  │BRANCH A │     │          │
                    │  │CPU Block│     │          │
                    │  └────┬────┘     │          │
                    │       │          │          │
                    │    ┌──┴──────────┴──┐       │
                    │    │   Y-MERGE       │       │
                    │    └────────┬────────┘       │
                    │             │                │
                    └─────────────┼────────────────┘
                                  │
              ═══ INSULATED TUBING PASS-THROUGH ═══
                                  │
                           HOT RETURN → HEATER CORE
```

### Flow Path Summary

1. **D5 Pump** (in reservoir, external rack) pushes coolant
2. → **Through insulated pass-through** into freezer
3. → **Copper coil** (20 ft, submerged in freezer cold air) chills to ~5°C
4. → **Y-Split** into two parallel branches:
   - **Branch A:** CPU block only (highest restriction, highest heat)
   - **Branch B:** GPU → RAM1 → RAM2 → NVMe (series, lower restriction each)
5. → **Y-Merge** rejoins branches
6. → **Through insulated pass-through** back to external rack
7. → **Car heater core** (pre-cools from ~35°C to ~25°C)
8. → **Back to reservoir/pump**

### Why This Order?

- **Copper coil BEFORE blocks:** Coolant is chilled first, then
  delivered cold to all components. Maximum sub-ambient benefit.
- **CPU on its own branch:** The Heatkiller TR has the highest flow
  restriction. Giving it a dedicated branch ensures adequate flow.
- **GPU/RAM/NVMe in series:** Each has relatively low restriction.
  In series they see slightly warmer coolant down the chain but
  GPU gets the coldest (first in branch).
- **Heater core AFTER blocks, BEFORE coil:** Pre-cools the hottest
  coolant before it hits the freezer, reducing compressor load.

---

## Modular Multi-Freezer Advantage

### Why Use a Second Freezer?

The Frigidaire EFRF1013 is the **PC chamber** — components live here
in cold air. A second smaller freezer becomes the **cryo reservoir**:

| Unit | Role | Contents |
|---|---|---|
| **Frigidaire 10 cu ft (primary)** | PC Chamber | Motherboard, CPU block, GPU block, RAM, NVMe, all on mounting frame |
| **Mini Freezer 3.5-5 cu ft (secondary)** | Cryo Reservoir | SS stock pot reservoir + copper coil + D5 pump (submersed in pot) |
| **External Rack (12U)** | Power + Cooling Stage 1 | PSU, heater core + fans, STC-1000, ESP32, I/O panel |

### Advantage of Separate Cryo Reservoir

1. **The copper coil + reservoir can be at -15°C** while the PC
   chamber is at 0-5°C. Different freezers, different set points.
2. **The pump heat (~20W) is absorbed by the cryo reservoir** —
   doesn't warm the PC chamber at all.
3. **If the PC freezer needs maintenance,** disconnect the
   quick-disconnects and open it without disturbing the cryo loop.
4. **Acoustic isolation:** Compressor noise from two smaller freezers
   is less intrusive than one large one.

### When to Use Single vs Dual Freezer

| Scenario | Configuration |
|---|---|
| **Budget build, testing** | Single Frigidaire only — reservoir + coil inside same freezer |
| **Maximum performance** | Dual freezer — dedicated cryo reservoir at -15°C |
| **Maximum YouTube content** | Dual freezer — more dramatic, more episodes |

---

## Water Block Selection — Optimized List

Based on the sTR5 compatibility research and dual-branch design:

### Branch A: CPU

| Component | Block | Price | Source | Notes |
|---|---|---|---|---|
| **CPU (TR PRO 9965WX)** | Watercool Heatkiller IV PRO TR (Cu/Ni) | ~$140 | watercool.de / performance-pcs.com | sTR4 mount, sTR5 compatible via Asetek bracket |

### Branch B: GPU → RAM → NVMe

| Component | Block | Price | Source | Notes |
|---|---|---|---|---|
| **GPU (RTX 5080)** | Bykski N-RTX5080-X (full cover) | ~$90-120 | bykski.us / Amazon | Check exact GPU model for compatibility |
| **RAM (DDR5 RDIMM) ×2** | Alphacool Core DDR5 Block | ~$70 ea ($140) | Amazon | Budget-friendly, one per 4-DIMM bank |
| **NVMe (PCIe 5.0)** | Alphacool Core M.2 NVMe Block | ~$45 | Amazon | Single M.2 slot coverage |

### NOT Water-Cooled (Freezer Air Handles These)

| Component | Cooling | Why |
|---|---|---|
| **VRM** | Stock heatsink + freezer cold air (0-5°C) | Stock WRX90E-SAGE heatsinks are massive. Freezer air is sub-ambient. |
| **Chipset** | Stock heatsink + freezer cold air | Same reasoning — under 5W heat load, trivial in cold air |

### Total Water Block Cost: ~$415-445

Compared to Version B original estimate of $650-700 for 7 blocks.
**Savings: ~$235-255** by smartly choosing which components need
blocks and which don't.

---

## Fittings Strategy

### Fitting Count

| Location | Type | Qty |
|---|---|---|
| CPU block (2 ports) | G1/4" compression | 2 |
| GPU block (2 ports) | G1/4" compression | 2 |
| RAM block ×2 (2 ports each) | G1/4" compression | 4 |
| NVMe block (2 ports) | G1/4" compression | 2 |
| Y-split (3 ports) | G1/4" T-fitting or manifold | 2 (split + merge) |
| Reservoir (2 ports) | Bulkhead + barb | 2 |
| Copper coil transitions | Compression to barb | 4 |
| Heater core transitions | 5/8" barb reducers | 2 |
| Pass-throughs (freezer wall) | Bulkhead fittings | 4 |
| Drain valves | G1/4" ball valve | 2 |
| **Total G1/4" compression:** | | **~16** |
| **Total adapters/barbs:** | | **~10** |
| **Total ball valves:** | | **2** |

### Recommended Fittings (Budget)

| Item | Source | Price |
|---|---|---|
| Barrow G1/4" to 10/16mm compression (16-pack bulk) | Amazon/AliExpress | ~$35-45 (~$2.50 ea) |
| Barrow G1/4" 90° rotary (6-pack) | Amazon | ~$20 |
| Barrow G1/4" T-fitting (×2) | Amazon | ~$8 |
| Barrow G1/4" ball valve (×2) | Amazon | ~$12 |
| 5/8" to 3/8" brass barb reducer (×2) | Home Depot / Amazon | ~$8 |
| Everbilt 1/2" bulkhead unions (×4) | Home Depot | ~$24 |
| **Total fittings:** | | **~$107-117** |

---

## Tubing Strategy

### Inside Freezer (Cold Zone): EPDM Rubber

- **EK ZMT 15.9/9.5mm** or **Tygon Norprene A-60-G**
- EPDM rubber does NOT become brittle at sub-zero temps
- Matte black, no plasticizer leaching
- ~$15 per 3m coil, need 2 coils = **~$30**

### Outside Freezer (Room Temp): Standard Soft Tubing

- **PrimoChill PrimoFlex 3/8" ID / 5/8" OD** or equivalent
- Standard soft tubing is fine at room temp
- ~$12 per 10 ft, need 1 roll = **~$12**

### Insulation on Pass-Through Tubing

- **Armaflex self-seal pipe insulation** from Home Depot
- Wrap ALL tubing that transitions between cold and warm zones
- Prevents condensation on cold tubing in warm air
- Already in Home Depot shopping list

---

## Thermal Analysis: Expected Performance

### Operating Temperatures (Steady-State, Full Load)

| Point in Loop | Without Heater Core | With Heater Core | With Heater Core + Cryo Reservoir |
|---|---|---|---|
| **Coolant leaving copper coil** | 10-15°C | 5-8°C | **0-3°C** |
| **CPU (full load 350W)** | 45-60°C | 35-45°C | **25-35°C** |
| **GPU (full load 300W)** | 50-65°C | 40-50°C | **30-40°C** |
| **RAM (under load)** | 15-25°C | 10-20°C | **5-15°C** |
| **NVMe (under load)** | 15-30°C | 10-25°C | **5-20°C** |
| **VRM (stock heatsink, cold air)** | 15-30°C | 15-30°C | **10-20°C** |
| **Coolant returning to heater core** | 25-35°C | 25-35°C | **20-30°C** |
| **Compressor duty cycle** | **100%** (overloaded) | **60-80%** | **40-60%** |

**Key takeaway:** The dual-stage system (heater core + freezer)
delivers **25-35°C CPU temps under full 350W load** — compared to
70-85°C with a standard AIO. That's **40-50°C cooler.**

With the cryo reservoir variant, we approach **25°C under full load**
— territory usually reserved for phase-change or LN2 cooling.

### Idle Temperatures

When the PC is idle (~50-80W total), the freezer compressor easily
handles the load. Coolant drops to near-freezing:

| Component | Idle Temp |
|---|---|
| CPU | **5-15°C** |
| GPU | **5-10°C** |
| RAM | **2-8°C** |
| NVMe | **2-8°C** |

---

## Condensation Prevention — Complete Strategy

Sub-ambient cooling means surfaces below dew point. Condensation
kills electronics. Here's the complete prevention strategy:

### 1. Sealed Cold Chamber (Inside Freezer)

- Line freezer interior with **2" XPS foam panels** to create a
  sealed chamber
- **Great Stuff spray foam** fills ALL gaps between panels and walls
- **Frost King neoprene tape** seals the lid edge
- Goal: no ambient air enters the cold zone

### 2. Conformal Coating on Motherboard

- **MG Chemicals 419D** acrylic conformal coating (~$18)
- Spray on the motherboard **around the CPU socket area, RAM slots,
  and PCIe slots** — anywhere condensation could form
- Do NOT coat the socket pins themselves or the slot contacts
- Let cure 24 hours before installation

### 3. Desiccant Inside the Chamber

- **Silica gel packets (50g × 6)** placed around the chamber
- Absorb any residual moisture trapped during initial seal
- Replace every 6 months (or bake to regenerate)

### 4. Cable Pass-Through Sealing

- All cables pass through **rubber grommets** in the freezer wall
- **Automotive RTV silicone** around each cable at the pass-through
- **Armaflex wrap** on all cold tubing where it exits the freezer

### 5. Monitoring (ESP32)

- **DHT22 humidity sensor** inside the cold chamber
- ESP32 logs humidity level — if it rises above 40%, alert
- Automated: if humidity > 60%, power off PC and alert

---

## Electricity Cost Analysis

### Power Consumption

| Component | Watts | Daily Hours | Daily kWh |
|---|---|---|---|
| **Freezer compressor (60% duty)** | ~100W × 60% = 60W avg | 24 | 1.44 |
| **D5 Pump** | 20W | 24 | 0.48 |
| **Heater core fans (3×)** | 5W total | 24 | 0.12 |
| **ESP32 + sensors** | 2W | 24 | 0.05 |
| **Cooling system total** | ~87W avg | 24 | **2.09 kWh/day** |

### Annual Cooling Cost (NYC electricity ~$0.22/kWh)

- Daily: 2.09 kWh × $0.22 = **$0.46/day**
- Monthly: **~$14/month**
- Annual: **~$168/year**

For comparison, a server room AC unit costs $50-100/month to cool
a similar heat load. The Coolputer cooling system is remarkably
efficient.

---

## Component Longevity for a Keeper Build

Since this is a **permanent build with all-new components that you
keep forever,** here's the expected lifespan of each cooling component:

| Component | Expected Life | Maintenance |
|---|---|---|
| **Frigidaire freezer compressor** | 10-15 years | None (sealed system) |
| **D5 Pump** | 50,000+ hours (~5-6 years 24/7) | Replace after 5 years |
| **Copper coil** | 20+ years | Flush with distilled water annually |
| **Water blocks (Cu/Ni)** | 10+ years | Flush annually, inspect O-rings |
| **Car heater core** | 10+ years | Flush annually |
| **EPDM tubing** | 5-7 years | Replace when stiff/discolored |
| **Glycol coolant** | 2-3 years | Drain and replace with fresh mix |
| **Brass fittings** | 20+ years | Inspect O-rings every 2 years |
| **STC-1000 thermostat** | 10+ years | None |
| **ESP32** | 10+ years | None (solid state) |

### Annual Maintenance Schedule

| Month | Task | Time |
|---|---|---|
| **January** | Drain and replace glycol coolant | 2 hours |
| **January** | Inspect all O-rings, replace if worn | 1 hour |
| **January** | Replace desiccant packets | 15 min |
| **July** | Check coolant level, top up if needed | 15 min |
| **July** | Clean heater core fins (compressed air) | 15 min |
| **July** | Check ESP32 sensor readings vs calibration | 30 min |

Total annual maintenance: **~4 hours/year**

---

## References & Sources

| Topic | Source | Key Finding |
|---|---|---|
| PG thermal properties | Dynalene Tech Data Sheet | 30% PG optimal for sub-ambient PC cooling |
| PG thermal properties | Alliance Chemical Guide | 30-50% PG standard for thermal systems |
| PG thermal properties | KasperCalc PG Calculator | Interactive Cp values per temperature/concentration |
| sTR5 water blocks | Level1Techs Forum | Heatkiller IV PRO confirmed working on sTR5 |
| sTR5 water blocks | Reddit r/threadripper | Comino is only dedicated WRX90E block — 50-unit MOQ |
| WRX90E VRM cooling | Reddit r/threadripper | Stock heatsinks adequate; no single-unit VRM blocks available |
| Comino WCB set | Comino.com product sheet | Cu-Steel construction, VRM coldplate with level-varied contact |
| D5 pump multi-block | HardForum, Overclock.net | Single D5 adequate for 5-6 blocks; dual branch recommended for 7+ |
| D5 pump parallel vs series | Tom's Hardware Forum | Series pumps = more head pressure; parallel = more flow |
| Chest freezer capacity | Wilprep Kitchen BTU calc | 10 cu ft freezer: ~800-1500 BTU/hr = ~235-440W cooling |
| Car heater core as radiator | Overclock.net, Instructables | Proven concept, 5-10 kW capacity, 5/8" barbs standard |
| Condensation prevention | Overclock.net Sub-Ambient thread | Mounting putty + conformal coat + sealed chamber = proven |
| EK parallel vs serial | EKWB Blog | Parallel branches reduce restriction, improve flow distribution |

---

*Coolputer Ultimate Research — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
