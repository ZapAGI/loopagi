# Coolputer Rack Edition — 42U Insulated Zone Cooling System

## The Innovation: Everything Inside One Rack

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Build Philosophy:** Fresh components, permanent keeper, no recycled parts  
**Innovation:** Full 42U server rack with thermally insulated compartments,
dedicated compressor chiller, 24" water-to-air radiator, and complete
power infrastructure sharing a 30A/120V apartment service.

---

## Concept Overview

No more chest freezers. No external units. **Everything lives inside
a single 42U server rack** — the PC, the cooling, the power, the
controls. Each zone is thermally insulated from the others with rigid
foam panels, creating isolated thermal environments within the rack.

```
┌─────────────────────────────────────────────────┐
│           COOLPUTER RACK EDITION                 │
│           42U Server Rack (79" tall)             │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ ZONE F: POWER & CONTROL (6U) — Top          │ │
│  │ PSU, PDU, ESP32, Network, I/O Panel          │ │
│  │ Temperature: Room ambient (~22°C)            │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ═══ XPS FOAM BARRIER (1U) ═══               │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ZONE E: HEAT REJECTION (8U)                  │ │
│  │ 24" Radiator + Fans (hot air vented out)     │ │
│  │ Temperature: ~25-35°C (actively vented)      │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ═══ XPS FOAM BARRIER (1U) ═══               │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ZONE D: PUMP & RESERVOIR (4U)                │ │
│  │ D5 Pump, SS Reservoir, Fill Port, Drain      │ │
│  │ Temperature: ~15-20°C (insulated)            │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ═══ XPS FOAM BARRIER (1U) ═══               │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ZONE C: COLD ZONE — PC COMPONENTS (12U)      │ │
│  │ Motherboard + CPU/GPU/RAM/NVMe blocks        │ │
│  │ FULLY INSULATED — 2" XPS all 6 sides         │ │
│  │ Temperature: 5-15°C (sub-ambient)            │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ═══ XPS FOAM BARRIER (1U) ═══               │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ZONE B: CHILLER UNIT (8U)                    │ │
│  │ Penguin Chillers 1/2 HP or 1 HP              │ │
│  │ Self-contained compressor + titanium HX      │ │
│  │ Temperature: Room ambient (needs ventilation) │ │
│  ├─────────────────────────────────────────────┤ │
│  │ ZONE A: BASE (1U)                            │ │
│  │ Heavy-duty shelf, cable management            │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  TOTAL: 6+1+8+1+4+1+12+1+8+1 = 43U             │
│  (Uses full 42U + casters add clearance)         │
└─────────────────────────────────────────────────┘
```

---

## Why This Design Is Innovative

### Problems with the Freezer Approach (Solved)

| Problem (Freezer) | Solution (Rack Edition) |
|---|---|
| Chest freezer compressor only removes 235-440W | Penguin Chiller removes 1,465-2,930W |
| Awkward horizontal layout | Professional vertical 42U rack |
| Difficult maintenance (reach into deep chest) | Front-access slide-out shelves per zone |
| No thermal isolation between zones | 2" XPS foam barriers between every zone |
| External rack needed for power/I/O | Everything inside one unit |
| Looks DIY/hacky | Looks like a professional data center rack |
| Hard to transport | Standard rack with casters |
| Condensation risk (open freezer air) | Sealed insulated cold zone with desiccant |
| Single compressor, limited capacity | Industrial chiller with titanium HX, glycol-rated |

---

## Zone-by-Zone Design

### Zone A: Base (1U)

**Purpose:** Foundation and cable management.

| Component | Spec | Price | Source |
|---|---|---|---|
| Heavy-duty rack shelf (1U) | NavePoint 1U fixed shelf, 150lb cap | ~$25 | Amazon |
| Cable management panel | 1U brush strip panel | ~$12 | Amazon |

### Zone B: Chiller Unit (8U)

**Purpose:** Dedicated refrigeration compressor that chills glycol
coolant to sub-ambient temperatures. Replaces the chest freezer.

#### Chiller Selection

| Model | Cooling Capacity | Power Draw | Amps | Price | Dimensions | Weight |
|---|---|---|---|---|---|---|
| **Penguin 1/2 HP** | 5,000 BTU/hr (1,465W) | 450W | 3.9A | **$999** | 16.25"×14.75"×12" | 39 lbs |
| **Penguin 1 HP** | 10,000 BTU/hr (2,930W) | 830W | 7.2A | **$1,899** | 19.25"×19.75"×14.25" | 58 lbs |
| **Penguin 1 HP HE** | 11,500 BTU/hr (3,370W) | 830W | 7.2A | **$2,199** | 19.25"×19.75"×14.25" | 60 lbs |

#### Recommended: Penguin Chillers 1/2 HP Water Chiller ($999.99)

**Why 1/2 HP is enough:**
- Our PC generates ~720W of heat
- The 24" radiator pre-cools returning coolant, removing ~300-500W
- The chiller only needs to handle the remaining ~220-420W
- The 1/2 HP provides **1,465W of cooling** — 2-3× our actual load
- **Lower power draw** (450W vs 830W) — lower electricity cost
- **Lower noise** (56 dBA vs 59 dBA)
- **Lighter** (39 lbs vs 58 lbs)

**Key Specs:**
- **Inlet/Outlet:** 1" Female NPT
- **Set point range:** 37°F–100°F with water; lower with glycol
- **Heat exchanger:** Titanium coils in PVC shell — glycol safe
- **Power:** 110-120V single phase, 3.9A
- **Made in USA** (Tennessee) — 1 year warranty

**Upgrade path:** If you later add a second GPU, swap to 1 HP model.

#### Zone B Mounting

| Component | Spec | Price | Source |
|---|---|---|---|
| Penguin Chillers 1/2 HP | 5,000 BTU/hr, titanium, 120V | $999.99 | penguinchillers.com |
| Heavy-duty rack shelf (4U) | StarTech ADJSHELFHDV, 330lb cap | ~$65 | Amazon |
| 1" NPT to 3/4" barb adapters ×2 | Brass, connects to loop | ~$8 | Home Depot |

**Important:** This zone needs ventilation — the chiller's condenser
rejects heat to ambient air. Keep rack sides OPEN in this zone.

### Zone C: Cold Zone — PC Components (12U)

**Purpose:** The motherboard and all water-cooled components live here
in a sealed, insulated chamber at 5-15°C.

#### Insulation Construction

2" XPS rigid foam on all six sides creates a box-within-the-rack:

```
COLD ZONE CROSS-SECTION (front view)
┌──────────────────────────────────────┐
│  2" XPS foam (top barrier/ceiling)    │
│  ┌────────────────────────────────┐  │
│  │                                │  │
│  │  2" XPS    COLD AIR     2" XPS │  │
│  │  (left)    5-15°C      (right) │  │
│  │            ┌──────┐            │  │
│  │            │MOBO  │            │  │
│  │            │+ GPU │            │  │
│  │            │mount │            │  │
│  │            └──────┘            │  │
│  │                                │  │
│  └────────────────────────────────┘  │
│  2" XPS foam (bottom barrier/floor)   │
└──────────────────────────────────────┘
```

**Internal dimensions after insulation:**
- Rack internal width: ~17.75" → after 4" foam: **~13.75" usable**
- Rack depth: ~31-39" → after 4" foam: **~27-35" usable**
- 12U height: 21" → after 4" foam: **~17" usable**
- WRX90E-SAGE SE (EEB): 12" × 13" — **fits with room for tubing**

#### PC Mounting

| Component | Spec | Price | Source |
|---|---|---|---|
| Rack-mount motherboard tray | Rosewill RSV-4U or custom aluminum | ~$40 | Amazon |
| Standoffs + screws | Standard EEB mounting kit | ~$8 | Amazon |
| PCIe riser cable | Thermaltake Premium 600mm PCIe 4.0 x16 | ~$60 | Amazon |
| GPU vertical mount bracket | Custom L-bracket | ~$20 | Amazon |

#### Water Blocks

| Component | Block | Price | Source |
|---|---|---|---|
| **CPU (TR PRO 9965WX)** | Watercool Heatkiller IV PRO TR | ~$140 | watercool.de |
| **GPU (RTX 5080)** | Bykski N-RTX5080-X full cover | ~$100 | bykski.us |
| **RAM (DDR5) ×2** | Alphacool Core DDR5 Block | ~$140 | Amazon |
| **NVMe (PCIe 5.0)** | Alphacool Core M.2 NVMe Block | ~$45 | Amazon |
| **VRM / Chipset** | Stock heatsinks (cold air = 5-15°C) | $0 | — |

#### Condensation Prevention

| Method | Implementation | Cost |
|---|---|---|
| Sealed XPS chamber | 2" panels + spray foam at seams | ~$40 |
| Conformal coating | MG Chemicals 419D (avoid contacts) | ~$18 |
| Desiccant | 50g silica gel packets ×6 | ~$10 |
| Humidity monitoring | DHT22 + ESP32 alert >40% RH | ~$8 |
| Cable grommet seals | Rubber grommets + RTV silicone | ~$15 |

### Zone D: Pump & Reservoir (4U)

**Purpose:** Central fluid management.

| Component | Spec | Price | Source |
|---|---|---|---|
| EK-Quantum Kinetic TBE 300 D5 | D5 pump + reservoir combo | ~$170 | EKWB |
| 2U vented rack shelf | Adjustable depth | ~$30 | Amazon |
| Fill port | G1/4" stop plug (quick-fill) | ~$5 | Amazon |
| Drain valve | Barrow G1/4" ball valve | ~$8 | Amazon |
| Quick-disconnect fittings ×2 | Koolance QD3 set | ~$30 | Amazon |

### Zone E: Heat Rejection — 24" Radiator (8U)

**Purpose:** Your 24" water-to-air heat exchanger with fans. Primary
heat rejection to room air. Pre-cools hot coolant before chiller.

#### Your Radiator (Already Owned)

| Spec | Value |
|---|---|
| **Size** | ~24" (length) |
| **Connections** | 3/4" barb or NPT (in/out) |
| **Construction** | Copper tubes + aluminum fins |
| **Capacity** | 20,000-100,000+ BTU/hr (massive overkill) |
| **Purpose** | Pre-cool from ~35°C to ~25°C |
| **Cost** | $0 (already owned) |

#### Fan Setup

| Component | Spec | Price | Source |
|---|---|---|---|
| Arctic P12 PWM fans (5-pack) | 120mm, PST daisy-chain | ~$27 | Amazon |
| Additional Arctic P12 (1) | 6th fan if needed | ~$9 | Amazon |
| Fan mounting | Zip ties or printed shroud | ~$5 | — |
| Fan controller | Arctic PWM hub or ESP32 PWM | ~$10 | Amazon |

#### Fitting Adapters (Radiator to Loop)

| Adapter | Qty | Price | Source |
|---|---|---|---|
| 3/4" barb to 3/8" barb reducer (brass) | 2 | ~$10 | Home Depot |
| OR: 3/4" NPT to G1/4" adapter chain | 2 sets | ~$16 | Amazon |

**Zone E MUST be ventilated** — fans push warm air out of the rack.

### Zone F: Power & Control (6U)

**Purpose:** All electrical infrastructure, monitoring, I/O.

---

## Power Budget: 30A / 120V Apartment (Shared)

### Apartment Power Reality

**Your apartment has 30A / 120V total service** — this is shared
across ALL apartment loads (fridge, lights, router, etc.). There is
no dedicated circuit. Standard wall outlets are **NEMA 5-15R (15A)**.

```
APARTMENT TOTAL: 30A × 120V = 3,600W
× 80% NEC continuous = 2,880W safe continuous

ESTIMATED EXISTING APARTMENT LOADS:
──────────────────────────────────────────────────
Appliance                    Watts    Amps @120V
──────────────────────────────────────────────────
Refrigerator                   150W     1.3A
Lights / misc electronics      200W     1.7A
Router / modem                  30W     0.3A
Phone chargers / small stuff    50W     0.4A
──────────────────────────────────────────────────
Apartment baseline             430W     3.7A
──────────────────────────────────────────────────

COOLPUTER RACK EDITION DRAW:
──────────────────────────────────────────────────
Component                    Watts    Amps @120V
──────────────────────────────────────────────────
PC (TR PRO 9965WX + RTX 5080)  780W     6.5A
  (720W PC ÷ 92% PSU efficiency)
Penguin Chiller (1/2 HP)        450W     3.9A
D5 Pump                          20W     0.2A
Radiator fans (×6)               12W     0.1A
ESP32 + sensors                   5W     0.1A
Monitor (32" 4K)                 60W     0.5A
──────────────────────────────────────────────────
Coolputer total              1,327W    11.3A
──────────────────────────────────────────────────

COMBINED: Apartment + Coolputer
──────────────────────────────────────────────────
Apartment baseline               430W     3.7A
Coolputer Rack Edition         1,327W    11.3A
──────────────────────────────────────────────────
TOTAL                         1,757W    15.0A
Remaining (of 2,880W safe)    1,123W     9.0A
──────────────────────────────────────────────────

✅ 1,757W of 2,880W = 61% utilization — SAFE
✅ Headroom for AC window unit (~500W) or microwave spikes
⚠️  Do NOT run microwave (1,200W) + full PC load simultaneously
    (would hit 2,957W = 24.6A, close to the 24A continuous limit)
```

### Two-Circuit Split Strategy

Your apartment panel likely has **2-4 individual 15A circuits**.
Each wall outlet circuit handles 15A (80% = 12A continuous).
**Split the Coolputer load across TWO wall outlets on DIFFERENT
circuits** to avoid tripping a single 15A breaker:

```
WALL OUTLET A (Circuit 1 — 15A breaker)
┌─────────────────────────────────────┐
│ Rack PDU (15A, NEMA 5-15P input)    │
│ ├── PC PSU (Corsair HX1500i): 6.5A  │
│ ├── D5 Pump (via relay): 0.2A       │
│ ├── Radiator fans: 0.1A             │
│ ├── ESP32 + sensors: 0.1A           │
│ └── Monitor: 0.5A                   │
│ TOTAL: 7.4A of 12A continuous ✅    │
└─────────────────────────────────────┘

WALL OUTLET B (Circuit 2 — 15A breaker)
┌─────────────────────────────────────┐
│ Penguin Chiller (direct plug): 3.9A  │
│ TOTAL: 3.9A of 12A continuous ✅    │
│                                      │
│ ⚠️ Chiller startup surge can hit    │
│    ~12A for 1-2 seconds — needs its  │
│    own circuit to avoid tripping     │
└─────────────────────────────────────┘

HOW TO VERIFY SEPARATE CIRCUITS:
1. Plug a lamp into Outlet A
2. Go to breaker panel, flip breakers one at a time
3. When lamp goes off, that's Circuit 1
4. Plug lamp into Outlet B, repeat
5. If Outlet B is on a DIFFERENT breaker = ✅
6. If same breaker, find an outlet on a different circuit
```

### Why the Chiller Gets Its Own Circuit

Compressor motors have a **startup (locked-rotor) current surge**
that can be 3-5× the running amps for 1-2 seconds:
- Penguin 1/2 HP running: 3.9A
- Penguin 1/2 HP startup surge: **~12-15A** (momentary)

If the chiller shares a 15A circuit with the PC (already drawing
6.5A), a compressor startup could spike to 18-21A and **trip the
breaker**. Giving the chiller its own circuit solves this.

### No Electrician Needed

Since we're using existing apartment wall outlets (standard NEMA
5-15R), there is **no electrician install required.** Just plug in.
This saves ~$300 from the original estimate.

### PSU Selection

| Model | Wattage | Efficiency | Connector | Price | Source |
|---|---|---|---|---|---|
| **Corsair HX1500i (2025)** | 1500W | 80+ Platinum | ATX 3.1 + 12V-2×6 | ~$350 | Micro Center |
| Corsair AX1600i | 1600W | 80+ Titanium | ATX (older) | ~$500 | Amazon |
| Seasonic PRIME TX-1600 | 1600W | 80+ Titanium | ATX 3.0 | ~$480 | Amazon |
| be quiet! Dark Power 13 | 1600W | 80+ Titanium | ATX 3.0 | ~$400 | Amazon |

**Recommended: Corsair HX1500i (2025)**
- ATX 3.1 — native 12V-2×6 connector for RTX 5080
- 1500W — plenty for TR PRO + RTX 5080 + 850W headroom
- 80+ Platinum — 92% efficient at 50% load
- iCUE monitoring — real-time power data
- **$350** — best value premium 2025 PSU

### PDU Selection

| Model | Specs | Price | Source |
|---|---|---|---|
| **Tripp Lite PDUMH15** | Metered, 15A, 12 outlets, 5-15P, 1U | ~$130 | Amazon |
| CyberPower CPS1215RMS | Basic, 15A, 12 outlets, 5-15P, 1U | ~$55 | Amazon |
| Tripp Lite RS-1215-RA | Basic, 15A, 12 rear outlets, 5-15P, 1U | ~$65 | Amazon |

**Recommended: Tripp Lite PDUMH15** — 15A metered PDU with digital
amp display. Standard NEMA 5-15P plug fits any apartment wall outlet.
The metered display shows real-time draw so you always know your
load. The Penguin Chiller plugs directly into a SEPARATE wall
outlet (not through the PDU).

### Monitoring & Control

| Component | Spec | Price | Source |
|---|---|---|---|
| ESP32 DevKit V1 | WiFi + BLE, controls everything | ~$8 | Amazon |
| DHT22 sensors ×3 | Humidity/temp per zone | ~$12 | Amazon |
| DS18B20 probes ×4 | Coolant temp at 4 loop points | ~$10 | Amazon |
| Barrow G1/4" flow meter | Coolant flow rate | ~$15 | Amazon |
| 0.96" OLED display | Front-panel status readout | ~$6 | Amazon |
| 2-channel relay module | Safety shutoff for pump/chiller | ~$8 | Amazon |
| 1U blank panel | Mount controls behind it | ~$10 | Amazon |

### I/O Panel

| Component | Spec | Price | Source |
|---|---|---|---|
| 1U blank panel | For I/O pass-throughs | ~$10 | Amazon |
| USB 3.2 panel-mount ×4 | Type-A and Type-C | ~$20 | Amazon |
| HDMI 2.1 panel-mount ×2 | Monitor connections | ~$15 | Amazon |
| RJ45 coupler | 10GbE pass-through | ~$5 | Amazon |
| Power button + LED | Panel-mount | ~$8 | Amazon |

---

## Complete Cooling Loop — Flow Path

```
FLOW ORDER:
1. D5 Pump (Zone D) pushes glycol
2. → Penguin Chiller (Zone B) cools ~25°C → ~5°C
3. → Cold Zone (Zone C): CPU → GPU → RAM ×2 → NVMe
4. → Hot coolant (~35°C) exits Cold Zone
5. → 24" Radiator + fans (Zone E) cools ~35°C → ~25°C
6. → Back to reservoir/pump (Zone D)
7. → Repeat

WHY THIS ORDER:
• Pump → Chiller → Blocks: coldest coolant hits components first
• Blocks → Radiator → Pump: pre-cools before chiller input
• Radiator removes ~300-500W to room air
• Chiller only handles remaining ~200-400W
• Compressor runs at partial capacity = quiet, efficient, long-life
```

---

## Thermal Performance (Full 720W Load)

| Measurement Point | Temperature |
|---|---|
| Coolant leaving chiller | **3-8°C** |
| Coolant entering CPU block | **5-10°C** |
| CPU die (350W load) | **25-35°C** |
| GPU die (300W load) | **30-40°C** |
| RAM (under load) | **8-18°C** |
| NVMe (under load) | **10-20°C** |
| VRM (stock heatsink, cold air) | **15-30°C** |
| Coolant leaving PC (hot return) | **30-38°C** |
| Coolant after radiator | **22-28°C** |
| Cold zone air temperature | **5-15°C** |
| Chiller duty cycle | **40-60%** |

### vs Standard Cooling

| Component | Standard AIO | Coolputer Rack | Improvement |
|---|---|---|---|
| CPU (350W) | 70-85°C | **25-35°C** | 40-50°C cooler |
| GPU (300W) | 75-90°C | **30-40°C** | 45-50°C cooler |
| RAM | 45-60°C | **8-18°C** | 37-42°C cooler |
| NVMe | 55-70°C | **10-20°C** | 45-50°C cooler |
| VRM | 70-90°C | **15-30°C** | 55-60°C cooler |

---

## 42U Rack Specification

### Recommended: NavePoint 42U 4-Post Open Frame

| Spec | Value |
|---|---|
| **Model** | NavePoint 42U 1000mm 4-Post Open Frame |
| **Dimensions** | 39.38"L × 23.31"W × 79.06"H |
| **Material** | Cold rolled steel, black powder coat |
| **Weight capacity** | 881 lbs |
| **Standard** | EIA-310-E (19" rack) |
| **Depth** | Adjustable (1000mm model) |
| **Casters** | Included (locking) |
| **Price** | **~$300-350** |
| **Source** | Amazon / navepoint.com |

**Why open frame:** Zones B and E need ventilation. Open frame allows
airflow where needed, and you add insulation panels only where needed.

---

## Glycol Coolant: 30% Propylene Glycol

| Property | Value |
|---|---|
| Concentration | 30% PG / 70% distilled water |
| Freeze point | -13°C (9°F) |
| Thermal conductivity | 0.46 W/mK (77% of water) |
| Specific heat | 3.90 kJ/kgK (93% of water) |
| Viscosity at 5°C | 4.5 cP (D5 handles easily) |

**Recipe (5L):** 3L RV antifreeze (~50% PG) + 2L distilled water
+ silver kill coil or biocide. ~$11 total.

The Penguin Chiller has titanium HX — fully glycol compatible.

---

## Insulation Materials

| Material | Size | R-Value | Price | Source |
|---|---|---|---|---|
| Owens Corning FOAMULAR 250 XPS | 2"×4'×8' | R-10 | ~$45 | Home Depot |
| Great Stuff Big Gap Filler ×2 | 20 oz can | — | ~$16 | Home Depot |
| Frost King neoprene tape ×2 | 3/8"×1/2"×10' | — | ~$10 | Home Depot |
| Reflective foil tape | 2"×50 yd | — | ~$12 | Home Depot |
| MG Chemicals 419D conformal coat | Spray can | — | ~$18 | Amazon |
| Silica gel packets ×6 | 50g each | — | ~$10 | Amazon |
| Rubber grommets kit | Assorted | — | ~$8 | Amazon |
| Permatex RTV silicone | 3 oz tube | — | ~$8 | Home Depot |

---

## Complete Bill of Materials

### Rack & Structure — $538

| # | Item | Price |
|---|---|---|
| 1 | NavePoint 42U 1000mm 4-Post Open Frame Rack | $330 |
| 2 | Heavy-duty 4U rack shelf (chiller) | $65 |
| 3 | 2U vented rack shelf (pump) | $30 |
| 4 | 1U rack shelves ×2 (PSU, misc) | $50 |
| 5 | 1U blank panels ×4 (barriers) | $24 |
| 6 | 1U brush strip panels ×2 | $24 |
| 7 | Cage nuts + screws kit (100pc) | $15 |

### Cooling System — $1,254

| # | Item | Price |
|---|---|---|
| 8 | Penguin Chillers 1/2 HP Water Chiller | $999.99 |
| 9 | EK-Quantum Kinetic TBE 300 D5 pump/res | $170 |
| 10 | 24" Radiator (already owned) | $0 |
| 11 | Arctic P12 PWM fans (5-pack) | $27 |
| 12 | Arctic P12 single (6th fan) | $9 |
| 13 | 1" NPT to 3/4" barb adapters ×2 | $8 |
| 14 | 3/4" to 3/8" barb reducers ×2 | $10 |
| 15 | Koolance QD3 quick-disconnect ×2 | $30 |

### Water Blocks & Fittings — $547

| # | Item | Price |
|---|---|---|
| 16 | Watercool Heatkiller IV PRO TR (CPU) | $140 |
| 17 | Bykski N-RTX5080-X (GPU full cover) | $100 |
| 18 | Alphacool Core DDR5 Block ×2 (RAM) | $140 |
| 19 | Alphacool Core M.2 NVMe Block | $45 |
| 20 | Barrow G1/4" compression fittings 16-pk | $40 |
| 21 | Barrow G1/4" 90° rotary 6-pk | $20 |
| 22 | Barrow G1/4" T-fittings ×2 | $8 |
| 23 | Barrow G1/4" ball valve ×2 | $12 |
| 24 | EK ZMT 15.9/9.5mm tubing (3m ×2) | $30 |
| 25 | PrimoChill soft tubing (10ft) | $12 |

### Coolant — $29

| # | Item | Price |
|---|---|---|
| 26 | Prime Guard RV Antifreeze (1 gal) | $7 |
| 27 | Distilled water (2 gal) | $4 |
| 28 | Silver kill coil | $8 |
| 29 | Mayhems biocide (backup) | $10 |

### Insulation — $127

| # | Item | Price |
|---|---|---|
| 30 | FOAMULAR 250 XPS (2"×4'×8') | $45 |
| 31 | Great Stuff spray foam ×2 | $16 |
| 32 | Frost King neoprene tape ×2 | $10 |
| 33 | Reflective foil tape | $12 |
| 34 | MG Chemicals 419D conformal coat | $18 |
| 35 | Silica gel packets ×6 | $10 |
| 36 | Rubber grommets kit | $8 |
| 37 | RTV silicone | $8 |

### Power Infrastructure — $480

| # | Item | Price |
|---|---|---|
| 38 | Tripp Lite PDUMH15 (1U, 15A metered PDU) | $130 |
| 39 | Corsair HX1500i PSU (ATX 3.1) | $350 |
| — | Electrician / dedicated circuit | $0 (not needed) |
| — | Chiller plugs direct to separate wall outlet | $0 |

### Monitoring — $69

| # | Item | Price |
|---|---|---|
| 42 | ESP32 DevKit V1 | $8 |
| 43 | DHT22 sensors ×3 | $12 |
| 44 | DS18B20 temp probes ×4 | $10 |
| 45 | Barrow G1/4" flow meter | $15 |
| 46 | 0.96" OLED display | $6 |
| 47 | 2-channel relay module | $8 |
| 48 | 1U blank panel (controls) | $10 |

### I/O Panel — $58

| # | Item | Price |
|---|---|---|
| 49 | 1U blank panel (I/O mount) | $10 |
| 50 | USB 3.2 panel-mount ×4 | $20 |
| 51 | HDMI 2.1 panel-mount ×2 | $15 |
| 52 | RJ45 coupler (10GbE) | $5 |
| 53 | Power button + LED | $8 |

---

## Total Cost Summary

### Cooling + Infrastructure Only

| Category | Cost |
|---|---|
| Rack & Structure | $538 |
| Cooling System | $1,254 |
| Water Blocks & Fittings | $547 |
| Coolant | $29 |
| Insulation | $127 |
| Power Infrastructure | $480 |
| Monitoring | $69 |
| I/O Panel | $58 |
| **TOTAL** | **$3,102** |

*Savings vs original estimate: $368 (no electrician, 15A PDU)*

### Complete System (Including PC Hardware)

| Category | Cost |
|---|---|
| Cooling + Infrastructure | $3,102 |
| TR PRO 9965WX (24-core) | $2,700 |
| ASUS WRX90E-SAGE SE | $1,100 |
| RTX 5080 (16GB) | $1,000 |
| DDR5 RDIMM 128GB (4×32GB) | $500 |
| PCIe 5.0 NVMe 2TB | $250 |
| **TOTAL COMPLETE SYSTEM** | **~$8,652** |

---

## Electricity Cost (NYC ~$0.22/kWh)

### Cooling Only

| Component | Watts Avg | kWh/day |
|---|---|---|
| Chiller (50% duty) | 225W | 5.40 |
| D5 Pump | 20W | 0.48 |
| Radiator fans | 12W | 0.29 |
| ESP32 | 5W | 0.12 |
| **Cooling total** | **262W** | **6.29** |

- **Daily:** $1.38
- **Monthly:** **$41**
- **Annual:** **$496**

### Full System (PC + Cooling)

- PC avg load (~60%): ~430W × 16 hrs + cooling 24 hrs = ~13.77 kWh/day
- **Monthly:** ~$91
- **Annual:** ~$1,106

---

## Assembly Order (5-Day Build)

### Day 1: Rack + Insulation
1. Assemble 42U rack, install casters, level
2. Install all shelves at zone positions
3. Cut XPS foam panels for Cold Zone (6 sides)
4. Install bottom + side insulation panels
5. Cut + install XPS barrier panels between zones

### Day 2: Cooling Infrastructure
6. Place Penguin Chiller on Zone B shelf
7. Mount 24" radiator in Zone E with brackets
8. Mount fans to radiator
9. Install D5 pump/reservoir on Zone D shelf
10. Run tubing between zones (loose fittings)
11. Connect chiller + radiator to loop via adapters

### Day 3: PC Build
12. Apply conformal coating to motherboard — cure 24 hours
13. Install CPU, RAM, NVMe on motherboard
14. Mount motherboard on rack tray in Cold Zone
15. Install CPU/GPU/RAM/NVMe water blocks
16. Connect all blocks with tubing
17. Install PCIe riser, mount GPU

### Day 4: Electrical + Fill
18. Electrician installs 30A circuit + L5-30R receptacle
19. Mount PDU, connect to wall
20. Install PSU on shelf, connect to PDU
21. Run PSU cables through insulation pass-throughs
22. Fill loop with 30% PG coolant
23. Run pump 1 hour — leak check
24. Power on chiller, set to 5°C
25. Monitor temps with DS18B20 probes

### Day 5: Seal + Test + Commission
26. Close top insulation on Cold Zone
27. Seal all seams with spray foam + foil tape
28. Install desiccant packets
29. Install ESP32 + sensors + OLED
30. Power on PC — BIOS temp check
31. Boot OS, run Cinebench R24 stress test 30 min
32. Install I/O panel
33. Cable management pass
34. Configure ESP32 WiFi dashboard + alerts

---

## Safety

### Electrical
- 30A circuit with GFCI protection recommended
- All power inside rack — no exposed wiring
- PDU dual breakers protect against overload
- ESP32 relay shutoff if coolant >50°C

### Thermal
- Chiller has built-in overtemp protection
- ESP32 monitors cold zone humidity — alerts >40% RH
- Conformal coating protects PCB from condensation
- Sealed cold zone + desiccant prevents moisture

### Leak Protection
- Quick-disconnects at zone boundaries contain leaks
- Drip tray in bottom of Cold Zone
- Leak detection tape around CPU block area
- Ball valve drains at lowest points

### Fire
- XPS foam is flammable — no exposed heating elements nearby
- PSU is 80+ Platinum — minimal heat
- Smoke detector on top of rack

---

## Maintenance (Keeper Build)

| Frequency | Task | Time |
|---|---|---|
| Monthly | Check ESP32 dashboard | 5 min |
| Quarterly | Inspect tubing, clean radiator fins | 20 min |
| Annually | Drain/replace glycol, inspect O-rings | 3 hours |
| Annually | Replace desiccant, verify sensors | 45 min |
| Every 2 years | Replace EPDM tubing if needed | 2 hours |
| Every 5 years | Replace D5 pump (preventive) | 1 hour |

**Total: ~5 hours/year maintenance**

---

## Future Expansion

| Upgrade | Changes | Cost |
|---|---|---|
| 2nd GPU | Add block, widen loop, maybe 1 HP chiller | +$300-1,100 |
| 2nd PC | Duplicate Cold Zone (2nd rack) | +$4,000-6,000 |
| Sub-zero coolant | 40% PG, lower chiller set point | +$200-400 |
| UPS | APC SMT1500RM2U (2U rack-mount) | +$550 |
| Remote monitoring | ESP32 → MQTT → Grafana | $0 (software) |
| RGB (YouTube) | LED strips in Cold Zone + acrylic panel | +$20 |

---

## Rack Placement Diagrams

### Diagram 1: Full 42U Front View — Exact U Positions

```
    ┌─── 19" RACK WIDTH (23.31" frame) ───┐
    │                                       │
U42 ├═══════════════════════════════════════┤ ─┐
    │  [PDU] Tripp Lite PDUMH15 (1U)       │  │
U41 ├───────────────────────────────────────┤  │
    │  [PSU] Corsair HX1500i on shelf      │  │
U40 ├───────────────────────────────────────┤  │ ZONE F
    │  [I/O] USB/HDMI/Ethernet panel (1U)  │  │ POWER &
U39 ├───────────────────────────────────────┤  │ CONTROL
    │  [MON] ESP32 + OLED + relays (1U)    │  │ (6U)
U38 ├───────────────────────────────────────┤  │ ~22°C
    │  [BRUSH] Cable management (1U)       │  │ Room Temp
U37 ├───────────────────────────────────────┤ ─┘
    ║▓▓▓▓▓ XPS FOAM BARRIER (1U) ▓▓▓▓▓▓▓▓▓║
U36 ╠═══════════════════════════════════════╣ ─┐
    │                                       │  │
U35 │   ┌───────────────────────────────┐   │  │
    │   │                               │   │  │
U34 │   │     24" WATER-TO-AIR          │   │  │
    │   │     HEAT EXCHANGER            │   │  │
U33 │   │     (RADIATOR)                │   │  │ ZONE E
    │   │                               │   │  │ HEAT
U32 │   │     3/4" IN ──┐  ┌── 3/4" OUT│   │  │ REJECTION
    │   │               │  │           │   │  │ (8U)
U31 │   └───────────────┼──┼───────────┘   │  │ 25-35°C
    │                   │  │               │  │ VENTED
U30 │  [FAN] [FAN] [FAN]│  │[FAN] [FAN]   │  │
    │   ←── AIRFLOW OUT ←──── AIRFLOW OUT  │  │
U29 │   Arctic P12 ×5-6 (exhaust to room)  │  │
    │                                       │  │
U28 ├───────────────────────────────────────┤ ─┘
    ║▓▓▓▓▓ XPS FOAM BARRIER (1U) ▓▓▓▓▓▓▓▓▓║
U27 ╠═══════════════════════════════════════╣ ─┐
    │                                       │  │
U26 │  ┌─────────────────────────────────┐  │  │ ZONE D
    │  │  EK D5 Pump + Reservoir (300mm) │  │  │ PUMP &
U25 │  │  Fill Port ◉    Drain Valve ◉   │  │  │ RESERVOIR
    │  │  [QD3 Quick-Disconnect × 2]     │  │  │ (4U)
U24 │  └─────────────────────────────────┘  │  │ 15-20°C
    │  ── Vented 2U Shelf ──                │  │
U23 ├───────────────────────────────────────┤ ─┘
    ║▓▓▓▓▓ XPS FOAM BARRIER (1U) ▓▓▓▓▓▓▓▓▓║
U22 ╠═══════════════════════════════════════╣ ─┐
    ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║  │
U21 ║░  ┌─────────────────────────────┐  ░░║  │
    ║░  │  ASUS WRX90E-SAGE SE (EEB)  │  ░░║  │
U20 ║░  │  12" × 13" motherboard      │  ░░║  │
    ║░  │                              │  ░░║  │
U19 ║░  │  [CPU BLOCK]  ← Heatkiller  │  ░░║  │
    ║░  │   IV PRO TR                  │  ░░║  │
U18 ║░  │                              │  ░░║  │
    ║░  │  [RAM1 BLK] [RAM2 BLK]      │  ░░║  │
U17 ║░  │   Alphacool    Alphacool     │  ░░║  │ ZONE C
    ║░  │                              │  ░░║  │ COLD ZONE
U16 ║░  │  [NVMe BLOCK] ← Alphacool   │  ░░║  │ PC COMPS
    ║░  │   M.2 Core                   │  ░░║  │ (12U)
U15 ║░  │                              │  ░░║  │ ★ 5-15°C ★
    ║░  └──────────┬───────────────────┘  ░░║  │ INSULATED
U14 ║░             │ PCIe Riser Cable      ░░║  │
    ║░  ┌──────────┴───────────────────┐  ░░║  │
U13 ║░  │  RTX 5080 (VERTICAL MOUNT)   │  ░░║  │
    ║░  │  [GPU BLOCK] ← Bykski Full   │  ░░║  │
U12 ║░  │   Cover N-RTX5080-X          │  ░░║  │
    ║░  └──────────────────────────────┘  ░░║  │
U11 ║░  ── Motherboard Tray (Rosewill) ── ░░║  │
    ║░  [DESICCANT ×6]  [DHT22 SENSOR]    ░║  │
U10 ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║ ─┘
    ║▓▓▓▓▓ XPS FOAM BARRIER (1U) ▓▓▓▓▓▓▓▓▓║
U9  ╠═══════════════════════════════════════╣ ─┐
    │                                       │  │
U8  │  ┌─────────────────────────────────┐  │  │
    │  │                                 │  │  │
U7  │  │  PENGUIN CHILLERS 1/2 HP        │  │  │
    │  │  Water Chiller                  │  │  │ ZONE B
U6  │  │  16.25" × 14.75" × 12"         │  │  │ CHILLER
    │  │                                 │  │  │ (7U)
U5  │  │  1" NPT IN ──┐  ┌── 1" NPT OUT │  │  │ VENTILATED
    │  │               │  │              │  │  │ (open sides)
U4  │  │  [TITANIUM HX + COMPRESSOR]    │  │  │
    │  │                                 │  │  │
U3  │  └─────────────────────────────────┘  │  │
    │  ── Heavy-Duty 4U Shelf (330 lb) ──   │  │
U2  │     ↑↑↑ VENTILATION REQUIRED ↑↑↑     │  │
    ├───────────────────────────────────────┤ ─┘
U1  │  [BASE] Heavy-duty shelf + cable mgmt │  ZONE A
    ╘═══════════════════════════════════════╛  BASE (1U)
    ████████████ LOCKING CASTERS ████████████
```

### Diagram 2: Side Cross-Section View — Insulation & Airflow

```
    FRONT OF RACK                    BACK OF RACK
    (you face this)                  (against wall)
    ◄──── 39.38" depth (1000mm) ────►

    ┌────────────────────────────────────────┐
U42 │ PDU ─── power cables to all zones ─── │ ← Zone F
U41 │ PSU ─── ATX cables down to Cold Zone  │   Room temp
U40 │ I/O Panel (USB/HDMI/ETH accessible)   │   ~22°C
U39 │ ESP32 ─── sensor wires to all zones   │
U38 │ Brush strip (cables pass through)     │
U37 │                                        │
    ╠════════════════════════════════════════╣
U36 ║▓▓▓▓▓▓▓ XPS 2" FOAM BARRIER ▓▓▓▓▓▓▓▓▓║
    ╠════════════════════════════════════════╣
U35 │         ┌──────────────┐               │ ← Zone E
U34 │  FANS   │  24" RADIATOR│    AIR ───►   │   Hot air
U33 │ ○ ○ ○   │  (mounted    │   EXHAUST     │   exits
U32 │ ○ ○ ○   │   vertically)│   OUT BACK    │   through
U31 │  push   │  3/4" IN/OUT │   ───────►    │   open back
U30 │  air    │              │               │
U29 │ through └──────────────┘               │
U28 │                                        │
    ╠════════════════════════════════════════╣
U27 ║▓▓▓▓▓▓▓ XPS 2" FOAM BARRIER ▓▓▓▓▓▓▓▓▓║
    ╠════════════════════════════════════════╣
U26 │     D5 Pump ◉──── Reservoir           │ ← Zone D
U25 │     Fill ◉              Drain ◉       │   Pump area
U24 │     QD ◉ (quick-disconnect)  QD ◉    │   15-20°C
U23 │                                        │
    ╠════════════════════════════════════════╣
U22 ║▓▓▓▓▓▓▓ XPS 2" FOAM BARRIER ▓▓▓▓▓▓▓▓▓║
    ╠════════════════════════════════════════╣
    ║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║
    ║░ 2"  ┌────────────────────────┐  2" ░░║ ← Zone C
    ║░ XPS │   MOTHERBOARD + GPU    │  XPS ░║   ★ COLD ★
    ║░     │   (all water blocks    │      ░║   5-15°C
    ║░ L   │    connected)          │   R  ░║   SEALED
    ║░ E   │                        │   I  ░║
    ║░ F   │   Tubing IN ─┐ ┌─ OUT │   G  ░║   2" XPS
    ║░ T   │   (from       │ │     │   H  ░║   on ALL
    ║░     │    chiller)   │ │(to  │   T  ░║   6 sides
    ║░ W   │              │ │rad) │      ░║
    ║░ A   └──────────────┼─┼─────┘      ░║   Grommets
    ║░ L   Tubing passes  │ │  through   ░║   seal all
    ║░ L   foam via sealed│ │  grommets  ░║   pass-throughs
    ║░░░░░░░░░░░░░░░░░░░░░┼─┼░░░░░░░░░░░░║
    ╠══════════════════════╪═╪════════════╣
U9  ║▓▓▓▓▓▓▓ XPS 2" FOAM ▓┼▓┼▓▓▓▓▓▓▓▓▓▓▓║
    ╠══════════════════════╪═╪════════════╣
U8  │        Tubing runs   │ │            │ ← Zone B
U7  │     ┌────────────────┘ └──┐         │   Chiller
U6  │     │  PENGUIN CHILLER    │         │   MUST be
U5  │     │  1" NPT IN    OUT  │         │   ventilated
U4  │     │  [compressor +     │         │   (open sides)
U3  │     │   condenser coils] │         │
U2  │     └────────────────────┘         │
    │     ↑ AIR IN from   AIR OUT ↑      │
U1  │     ↑ open sides   open sides ↑    │ ← Zone A
    ╘════════════════════════════════════════╛
    ████ CASTERS (locking, +3" height) ████
```

### Diagram 3: Cold Zone Detail — Top-Down View (Looking Down Into Zone C)

```
                    ◄──── ~13.75" usable after foam ────►
    ┌──────────────────────────────────────────────────────┐
    │  2" XPS FOAM (back wall)                              │
    │  ┌──────────────────────────────────────────────────┐ │
    │  │                                                   │ │
    │  │  TUBING IN ◉────┐                                │ │
    │  │  (cold, ~5°C)   │                                │ │
    │  │                  ▼                                │ │
    │  │  ┌──────────────────────┐   ┌───────────────┐    │ │
    │  │  │  CPU WATER BLOCK     │   │ NVMe BLOCK    │    │ │
    │  │  │  Heatkiller IV PRO   │   │ Alphacool M.2 │    │ │
    │  │  │  (Branch A — solo)   │   │               │    │ │
2"  │  │  └────────┬─────────────┘   └───────┬───────┘    │ │ 2"
XPS │  │           │                          │            │ │ XPS
    │  │           │ Y-MERGE                  │            │ │
    │  │  ┌────────┴──────────────────────────┘            │ │
    │  │  │                                                │ │
    │  │  │  ┌────────────┐  ┌────────────┐               │ │
    │  │  │  │ RAM BLOCK 1│  │ RAM BLOCK 2│               │ │
    │  │  │  │ Alphacool  │  │ Alphacool  │               │ │
    │  │  │  │ DDR5 Core  │  │ DDR5 Core  │               │ │
    │  │  │  └─────┬──────┘  └──────┬─────┘               │ │
    │  │  │        └────────┬───────┘                      │ │
    │  │  │                 │                              │ │
    │  │  │  ┌──────────────┴──────────────────────┐      │ │
    │  │  │  │        GPU WATER BLOCK               │      │ │
    │  │  │  │  Bykski N-RTX5080-X (full cover)    │      │ │
    │  │  │  │  (Branch B — GPU→RAM1→RAM2→NVMe)    │      │ │
    │  │  │  └──────────────┬──────────────────────┘      │ │
    │  │  │                 │                              │ │
    │  │  └── Y-SPLIT ──────┘                              │ │
    │  │                    │                              │ │
    │  │  TUBING OUT ◉──────┘                              │ │
    │  │  (hot, ~35°C)                                     │ │
    │  │                                                   │ │
    │  │  [DHT22]  [DESICCANT] [DESICCANT] [DESICCANT]    │ │
    │  │  humidity   silica      silica      silica        │ │
    │  │  sensor     gel ×2     gel ×2      gel ×2         │ │
    │  │                                                   │ │
    │  └──────────────────────────────────────────────────┘ │
    │  2" XPS FOAM (front — removable access panel)         │
    └──────────────────────────────────────────────────────┘

    LEGEND:
    ◉ = Rubber grommet sealed with RTV silicone
    All tubing inside cold zone: EK ZMT (EPDM, cold-rated)
    All surfaces: Conformal coated (MG Chemicals 419D)
```

### Diagram 4: Cooling Loop Plumbing — Full Routing

```
    ZONE F (Power)       No plumbing in this zone
    ─────────────────────────────────────────────
    ZONE E (Radiator)
    ┌─────────────────────────────────────────┐
    │                                          │
    │  HOT IN                    WARM OUT      │
    │  (~35°C)                   (~25°C)       │
    │    │                          ▲          │
    │    ▼                          │          │
    │  ┌──┐  ══════════════════  ┌──┐          │
    │  │3/4"  24" RADIATOR      │3/4"         │
    │  │barb│  + 5× FANS         │barb│         │
    │  └─┬┘  ══════════════════  └─┬┘          │
    │    │  3/4"→3/8" reducer      │           │
    │    │                          │           │
    └────┼──────────────────────────┼───────────┘
    ═════╪══ XPS BARRIER ═══════════╪═══════════
    ┌────┼──────────────────────────┼───────────┐
    │    │    ZONE D (Pump)         │           │
    │    ▼                          │           │
    │  ┌────────────────────────────┴─┐         │
    │  │         RESERVOIR             │         │
    │  │    ┌─────────────┐           │         │
    │  │    │   D5 PUMP   │           │         │
    │  │    └──────┬──────┘           │         │
    │  └───────────┼──────────────────┘         │
    │   Fill ◉     │              Drain ◉       │
    │   Port       │              Valve         │
    │         [QD] ● (quick-disconnect)         │
    └──────────────┼────────────────────────────┘
    ═══════════════╪═ XPS BARRIER ══════════════
    ┌──────────────┼────────────────────────────┐
    │   ZONE B     │  (Chiller)                 │
    │              ▼                             │
    │  ┌───────────────────────────────┐        │
    │  │    PENGUIN CHILLER 1/2 HP     │        │
    │  │                               │        │
    │  │  1" NPT IN     1" NPT OUT    │        │
    │  │  (~25°C) ──►  ──► (~5°C)     │        │
    │  │  1"→3/4" adapter on each side │        │
    │  └──────────┬─────────┬──────────┘        │
    │             │         │                    │
    │        [QD] ●         ● [QD]               │
    └─────────────┼─────────┼───────────────────┘
    ══════════════╪═════════╪═ XPS BARRIER ═════
    ┌─────────────┼─────────┼───────────────────┐
    │  ZONE C     │ COLD    │                   │
    │  (sealed    ▼ ZONE    │                   │
    │  insulated)           │                   │
    │                       │                   │
    │  COLD IN (~5°C)       │                   │
    │    │                  │                   │
    │    ├──── Y-SPLIT ─────┤                   │
    │    │                  │                   │
    │    ▼                  ▼                   │
    │  BRANCH A           BRANCH B              │
    │  ┌───────┐   ┌──────────────────┐         │
    │  │  CPU  │   │  GPU → RAM1 →    │         │
    │  │ Block │   │  RAM2 → NVMe     │         │
    │  └───┬───┘   └────────┬─────────┘         │
    │      │                │                   │
    │      └── Y-MERGE ─────┘                   │
    │             │                              │
    │         HOT OUT (~35°C)                    │
    │             │                              │
    └─────────────┼──────────────────────────────┘
    ══════════════╪══ (through barrier) ═════════
                  │
                  └──► UP TO ZONE E (Radiator)
```

### Diagram 5: Electrical Wiring — Two-Circuit Layout

```
    APARTMENT BREAKER PANEL
    ┌───────────────────────┐
    │  CIRCUIT 1    CIRCUIT 2│
    │  (15A)       (15A)    │
    │    │            │      │
    └────┼────────────┼──────┘
         │            │
    ═════╪════════════╪══════════════════════
         │            │
         │            │    WALL OUTLET B
         │            └──── (different wall)
         │                       │
         │                 ┌─────┴──────────┐
    WALL OUTLET A          │ PENGUIN CHILLER │
         │                 │ Direct plug     │
    ┌────┴─────────┐       │ 120V / 3.9A    │
    │ RACK PDU     │       │ (startup ~12A) │
    │ Tripp Lite   │       └────────────────┘
    │ PDUMH15      │
    │ (15A metered)│
    │ ┌──────────┐ │
    │ │ OUTLET 1 ├─┼──► Corsair HX1500i PSU ──► Motherboard
    │ ├──────────┤ │                          ──► CPU (8-pin)
    │ │ OUTLET 2 ├─┼──► D5 Pump (via relay)  ──► GPU (12V-2×6)
    │ ├──────────┤ │
    │ │ OUTLET 3 ├─┼──► Fan Hub (Arctic P12 ×6)
    │ ├──────────┤ │
    │ │ OUTLET 4 ├─┼──► ESP32 (5V USB adapter)
    │ ├──────────┤ │
    │ │ OUTLET 5 ├─┼──► Monitor (32" 4K)
    │ ├──────────┤ │
    │ │ OUTLET 6 ├─┼──► (spare)
    │ ├──────────┤ │
    │ │  7-12    │ │    (expansion)
    │ └──────────┘ │
    │              │
    │ AMP DISPLAY: │
    │ ┌──────────┐ │
    │ │  7.4 A   │ │    ← real-time monitoring
    │ └──────────┘ │
    └──────────────┘

    TOTAL DRAW ON CIRCUIT 1:  7.4A of 12A (62%) ✅
    TOTAL DRAW ON CIRCUIT 2:  3.9A of 12A (33%) ✅
    COMBINED APARTMENT:      ~15A of 24A (63%) ✅
```

### Diagram 6: Component Physical Dimensions in Rack

```
    RACK INTERNAL: 17.75"W × 31-39"D (adjustable)

    ZONE F — 6U (10.5" height)
    ┌───────────────────────────────────────┐
    │ PDU: 19"W × 1.75"H (1U, rack ears)   │
    │ PSU: 8.6"W × 3.4"H × 7.9"D          │
    │ I/O + ESP32: 19"W × 1.75"H (1U)      │
    │ Brush panel: 19"W × 1.75"H (1U)      │
    │                                        │
    │ NOTE: PSU sits on 1U shelf. ATX cables │
    │ route DOWN through barrier grommets    │
    │ to Cold Zone below.                    │
    └───────────────────────────────────────┘

    ZONE E — 8U (14" height)
    ┌───────────────────────────────────────┐
    │ RADIATOR: ~24"L × 12-18"H × 2-3"D   │
    │ Mount: L-brackets bolted to rear rails│
    │ FANS: 5-6× 120mm (4.7"×4.7" each)   │
    │ Mount: Zip-tied to radiator fins      │
    │                                        │
    │ NOTE: Radiator mounted VERTICALLY     │
    │ against rear rails. Fans on room side,│
    │ blowing air THROUGH radiator and OUT  │
    │ the open back of the rack.            │
    └───────────────────────────────────────┘

    ZONE D — 4U (7" height)
    ┌───────────────────────────────────────┐
    │ RESERVOIR: ~3"D × 12"H (300mm tube)  │
    │ D5 PUMP: Integrated in reservoir base │
    │ Mount: Reservoir + pump on 2U shelf   │
    │ held upright with bracket/zip-ties    │
    │                                        │
    │ FILL PORT: G1/4 at top of reservoir   │
    │ accessible from front of rack.        │
    │ DRAIN: Ball valve at bottom, routed   │
    │ to front for easy access.             │
    └───────────────────────────────────────┘

    ZONE C — 12U (21" height, ~17" usable after foam)
    ┌───────────────────────────────────────┐
    │ MOBO: 12"W × 13"D (EEB form factor)  │
    │ GPU:  ~10.5"L × 4.4"H (2.5 slot)    │
    │ Riser: 600mm PCIe 4.0 x16 cable      │
    │                                        │
    │ INSULATION:                             │
    │   Top/Bottom: 2" XPS cut to 17.75"W   │
    │   Left/Right: 2" XPS cut to 21"H      │
    │   Front: 2" XPS (removable panel)     │
    │   Back: 2" XPS (fixed, tubing holes)  │
    │                                        │
    │ Mobo tray slides into rack rails.      │
    │ GPU mounts vertically via riser cable. │
    │ All tubing exits through BACK panel    │
    │ via rubber grommets sealed with RTV.   │
    └───────────────────────────────────────┘

    ZONE B — 7U (12.25" height)
    ┌───────────────────────────────────────┐
    │ CHILLER: 16.25"W × 14.75"D × 12"H   │
    │ Mount: On 4U heavy-duty shelf         │
    │ Clearance: ~1.5" on each side         │
    │                                        │
    │ ⚠️  VENTILATION: Rack sides MUST be   │
    │ open in this zone. Condenser coils    │
    │ reject heat to room air. Blocked      │
    │ airflow = compressor overheat.        │
    │                                        │
    │ POWER: Standard 120V plug exits rear  │
    │ of rack to separate wall outlet.      │
    │ TUBING: 1" NPT on chiller → adapters │
    │ → 3/8" tubing runs UP to Cold Zone.   │
    └───────────────────────────────────────┘

    ZONE A — 1U (1.75" height)
    ┌───────────────────────────────────────┐
    │ Heavy-duty shelf for cable management │
    │ Velcro straps for power cord routing  │
    └───────────────────────────────────────┘
```

---

## References

| Topic | Source | Key Finding |
|---|---|---|
| Penguin 1/2 HP Chiller | penguinchillers.com | 5,000 BTU/hr, 450W, $999, titanium HX, glycol-safe |
| Penguin 1 HP Chiller | penguinchillers.com | 10,000 BTU/hr, 830W, $1,899, titanium HX |
| NavePoint 42U Rack | Amazon / navepoint.com | 39"×23"×79", 881 lb cap, ~$330 |
| Tripp Lite PDUMH30 | Amazon | 30A metered PDU, 12 outlets, L5-30P, 1U, ~$175 |
| Corsair HX1500i (2025) | Micro Center | ATX 3.1, 1500W, 80+ Platinum, ~$350 |
| NEMA L5-30 specs | NEC / electrical forums | 30A/120V locking, 10 AWG wire, data center standard |
| XPS foam insulation | Owens Corning | FOAMULAR 250, R-10 per 2", closed-cell |
| PG glycol properties | Dynalene / Alliance Chemical | 30% PG optimal: -13°C freeze, 0.46 W/mK |

---

*Coolputer Rack Edition — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
