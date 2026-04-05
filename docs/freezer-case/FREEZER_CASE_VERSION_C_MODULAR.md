# Coolputer Version C: Modular Multi-Freezer System

## Linked Freezer Units + External Server Rack Cage

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Primary Unit:** Frigidaire EFRF1013 10 cu ft Black ($413.10)  

---

## Concept

Instead of cramming everything into one freezer, use **multiple dedicated
thermal units** linked by insulated tubing, plus an **external open-frame
server rack cage** bolted to the side of the main freezer. Each unit is
optimized for a single thermal role.

**The modular approach:**
- **Unit A (Main):** Frigidaire 10 cu ft — motherboard cold chamber
- **Unit B (Cryo):** Mini chest freezer 3.5-5 cu ft — coolant reservoir chiller
- **Unit C (Rack):** 12U open-frame server rack — PSU, radiator, heat exchange, I/O, control

Units A and B are linked by insulated coolant tubing. Unit C is bolted
to the side of Unit A. The result looks like a **mini data center rack**
with a freezer-chilled compute node.

---

## Why Modular?

| Advantage | Explanation |
|---|---|
| **No internal barriers needed** | Each freezer IS the compartment — no XPS foam engineering |
| **Dedicated compressors per zone** | Unit A's compressor keeps the chamber cold; Unit B's chills the reservoir |
| **Redundancy** | If Unit B fails, Unit A + rack radiator still cool the PC |
| **Scalability** | Add more cryo units for more cooling capacity |
| **Easier maintenance** | Disconnect any unit without disturbing others |
| **Smaller freezers are cheap** | A 3.5 cu ft used mini freezer = $30-60 |
| **YouTube episode per unit** | Each unit gets its own build episode |
| **Professional aesthetic** | Looks like actual data center infrastructure |

---

## System Architecture

### Physical Layout (Top-Down View)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌───────────────────────────┐  ┌────────────────┐  ┌───────────┐  │
│  │                           │  │                │  │           │  │
│  │   UNIT A: MAIN FREEZER   │  │  UNIT C:       │  │  UNIT B:  │  │
│  │   Frigidaire EFRF1013    │──│  SERVER RACK   │  │  CRYO     │  │
│  │   10 cu ft (Black)       │  │  12U Open      │  │  FREEZER  │  │
│  │                           │  │  Frame         │  │  3.5-5    │  │
│  │   Motherboard Chamber    │  │                │  │  cu ft    │  │
│  │   CPU+GPU+RAM+NVMe       │  │  PSU           │  │           │  │
│  │   (water blocks or       │  │  Radiator      │  │  Coolant  │  │
│  │    submerged — your       │  │  Fans          │  │  Reservoir│  │
│  │    choice)               │  │  I/O Panel     │  │  D5 Pump  │  │
│  │                           │  │  ESP32         │  │           │  │
│  │   44"W × 25.4"D          │  │  19"W × 20"D   │  │  22"W ×   │  │
│  │                           │  │                │  │  19"D     │  │
│  │                           │  │                │  │           │  │
│  └───────────────────────────┘  └────────────────┘  └───────────┘  │
│                                                                     │
│  Total footprint: ~85"W × 25"D (about 7 feet wide)                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Side View (Cross-Section)

```
          UNIT A                    UNIT C              UNIT B
    ┌──────────────┐          ┌──────────────┐    ┌──────────────┐
    │   LID        │          │  12U RACK    │    │   LID        │
    │ ┌──────────┐ │          │ ┌──────────┐ │    │ ┌──────────┐ │
    │ │Motherboard│ │  cables  │ │I/O Panel │ │    │ │(air space)│ │
    │ │+ blocks   │ │◀═══════▶│ │Radiator  │ │    │ │          │ │
    │ │+ GPU      │ │  tubing  │ │PSU       │ │    │ │Reservoir │ │
    │ │          │ │          │ │ESP32     │ │    │ │+ Pump    │ │
    │ │          │ │          │ │Cable mgmt│ │    │ │(chilled) │ │
    │ └──────────┘ │          │ └──────────┘ │    │ └──────────┘ │
    │  Freezer     │          │              │    │  Freezer     │
    │  coils chill │          │              │    │  coils chill │
    │  chamber air │          │              │    │  reservoir   │
    └──────────────┘          └──────────────┘    └──────────────┘
     Compressor A                                  Compressor B
```

---

## Coolant Flow Path

```
UNIT B (Cryo Freezer)
┌──────────────────────┐
│  Reservoir (0-5°C)   │
│  D5 Pump             │
└──────────┬───────────┘
           │  Insulated tubing (~3-6 ft run)
           ▼
UNIT A (Main Freezer)
┌──────────────────────┐
│  CPU Water Block      │
│  GPU Water Block      │
│  RAM Blocks (×2)      │
│  NVMe Block          │
│  VRM Block           │
│  Chipset Block       │
└──────────┬───────────┘
           │  Insulated tubing through wall
           ▼
UNIT C (Server Rack)
┌──────────────────────┐
│  360mm Radiator       │
│  (pre-cools by       │
│   10-20°C)           │
└──────────┬───────────┘
           │  Insulated tubing back to Unit B
           ▼
UNIT B (Reservoir — cycle repeats)
```

### Alternative: Submerged Mode in Unit A

Instead of water blocks, you can run Unit A in **submersion mode**
(mineral oil fill) — identical to Version A, but with the cryo
reservoir in a separate dedicated Unit B instead of sharing the
main freezer's cold zone.

**Benefit:** Unit A's compressor keeps the oil/chamber cold. Unit B's
compressor chills the circulating coolant to sub-zero. **Double
compressor power** = lower temperatures.

---

## Unit-by-Unit Design

### Unit A: Main Freezer (Frigidaire EFRF1013)

| Parameter | Value |
|---|---|
| **Model** | Frigidaire EFRF1013, 10 cu ft, Black |
| **External** | 44"W × 25.4"D × 33.3"H |
| **Internal (est.)** | ~38"W × 19"D × 25"H |
| **Role** | Motherboard cold chamber |
| **Compressor role** | Chill the chamber air to 5-15°C |
| **Contents** | Motherboard (EEB), CPU, GPU, RAM, NVMe, mounting frame |
| **Cooling mode** | Water blocks (Version B style) OR submerged (Version A style) |
| **Price** | **$413.10** (Home Depot Midtown Manhattan) |

**Modifications to Unit A:**
- Remove wire basket
- Drill side wall pass-through (3" hole, upper right, for cables + tubing to rack)
- Drill second pass-through (lower right or rear, for coolant tubing to/from Unit B)
- Install motherboard mounting frame (2020 extrusion + EEB tray)
- If water block mode: install sealed cold chamber with desiccant
- If submersion mode: fill with mineral oil after mounting components

### Unit B: Cryo Freezer (Mini Chest Freezer)

| Parameter | Value |
|---|---|
| **Type** | Mini chest freezer, 3.5-5 cu ft |
| **External (typical)** | ~22"W × 19"D × 33"H |
| **Internal (typical)** | ~17"W × 14"D × 22"H |
| **Role** | Dedicated coolant reservoir chiller |
| **Compressor role** | Chill the reservoir to -10 to 0°C |
| **Contents** | Stainless steel reservoir (5-10L), D5 pump, temp probes |
| **Price** | **$30-80 used** (FB Marketplace) or $120-180 new |

**Recommended models:**

| Model | Size | Price (new) | Price (used) |
|---|---|---|---|
| Frigidaire EFRF5003 | 5.0 cu ft | ~$180 | $50-80 |
| Midea MRC04M3AWW | 3.5 cu ft | ~$120 | $40-60 |
| Insignia NS-CZ35WH | 3.5 cu ft | ~$130 | $40-60 |
| Any mini chest freezer | 3-5 cu ft | $100-200 | $30-80 |

**Modifications to Unit B:**
- Remove wire basket
- Place stainless steel reservoir (5-10L pot) inside
- Install D5 pump (mounted on side or on reservoir lid)
- Drill two holes in side wall for coolant tubing in/out
- Seal penetrations with silicone + foam
- The freezer's cold air at -15 to -18°C chills the reservoir walls
- Reservoir coolant reaches 0-5°C with continuous operation

**Thermal analysis for Unit B:**
- Mini freezer at -18°C with a 5L reservoir
- Coolant returning at ~25-35°C after absorbing 350-650W
- Freezer compressor (~1/6-1/4 HP) can remove ~100-200W
- The external radiator (Unit C) removes another 200-350W
- **Combined: 300-550W removal capacity** — sufficient for the system

### Unit C: External Server Rack Cage (12U)

| Parameter | Value |
|---|---|
| **Type** | 12U open-frame server rack |
| **Size** | ~19"W × 20"D × 24"H |
| **Role** | Heat exchange, power, I/O, control |
| **Contents** | PSU, 360mm radiator, fans, I/O panel, ESP32, cable management |
| **Mounting** | Bolted to right side of Unit A (Frigidaire) |
| **Price** | ~$70-120 |

**Rack layout (12U):**

| U Position | Contents |
|---|---|
| **12U (top)** | I/O Panel — USB, HDMI, DP, Ethernet bulkheads |
| **11-10U** | 360mm Radiator (horizontal) + 3× Arctic P12 fans |
| **9U** | Quick-Connect Tubing Manifold (to Unit A + Unit B) |
| **8-7U** | ESP32 Controller + 2× OLED + LED controller + STC-1000 |
| **6-4U** | ATX PSU (1200W) + power distribution + surge protector |
| **3-2U** | Cable management + spare NVMe caddy |
| **1U** | Blank panel / ventilation |

**Tubing manifold at 9U:**
The rack serves as the **central tubing hub** connecting all three units:

```
From Unit B (cold supply) ──▶ Manifold ──▶ To Unit A (cold in)
From Unit A (warm return) ──▶ Manifold ──▶ Through Radiator ──▶ To Unit B (warm return)
```

Quick-disconnect fittings at every connection point allow any unit to
be disconnected for maintenance.

---

## Inter-Unit Tubing

### Insulated Tubing Runs

| Run | From | To | Length | Contents |
|---|---|---|---|---|
| **Cold Supply** | Unit B (pump out) | Unit A (cold in) | ~4-6 ft | Chilled coolant (0-5°C) |
| **Warm Return** | Unit A (warm out) | Unit C (radiator in) | ~2-3 ft | Warm coolant (25-35°C) |
| **Pre-Cooled Return** | Unit C (radiator out) | Unit B (reservoir in) | ~4-6 ft | Pre-cooled coolant (15-25°C) |

**All tubing must be insulated** with closed-cell foam pipe insulation
(especially the cold supply line). Without insulation, the cold tubing
will condensate and drip.

**Tubing spec:** EPDM (EK ZMT) or silicone, 10/16mm (3/8" ID),
with foam pipe insulation over the full length.

---

## Dual-Compressor Advantage

Version C has **two compressors** (one in each freezer) working in
concert:

| Compressor | Role | Power | Cooling |
|---|---|---|---|
| **Unit A (Frigidaire)** | Chill the motherboard chamber air | ~1/4-1/3 HP | ~200-300W |
| **Unit B (Mini freezer)** | Chill the coolant reservoir | ~1/6-1/4 HP | ~100-200W |
| **Combined** | | | **~300-500W** |
| **+ Radiator (Unit C)** | Air-cool returning coolant | 3× fans | **+200-350W** |
| **Total cooling capacity** | | | **~500-850W** |

**Total PC heat: ~350-650W** (CPU 350W + GPU 0-300W depending on load)

The system has **excess cooling capacity** even under full CPU + GPU
load. This means the compressors won't run 100% duty cycle — they'll
cycle on/off, extending their lifespan.

---

## Advanced Configuration: Dual-Cryo (Two Mini Freezers)

For extreme cooling, add a **second mini freezer** (Unit B2) with its
own reservoir, connected in parallel:

```
Unit B1 (Cryo #1) ──┐
                     ├──▶ Unit A (Main PC) ──▶ Unit C (Radiator) ──┐
Unit B2 (Cryo #2) ──┘                                              │
                     ◀──────────────────────────────────────────────┘
```

- **Two cryo reservoirs** = double thermal mass + double chilling power
- **Redundancy** = if one fails, the other keeps the system running
- **YouTube gold** = "I wired THREE freezers together for my AI PC"

---

## Parts List — Version C Modular

### Unit A: Main Freezer + Motherboard

| # | Item | Qty | Est. Price | Source |
|---|---|---|---|---|
| 1 | Frigidaire EFRF1013 10 cu ft Black | 1 | **$413.10** | Home Depot |
| 2 | 2020 Aluminum Extrusion Kit (frame) | 1 | ~$30 | Amazon |
| 3 | EEB Motherboard Tray + Hardware | 1 | ~$40 | Mountain Mods |
| 4 | PCIe 5.0 Riser Cable 300mm | 1 | ~$40 | Amazon |
| 5 | Rubber Grommets (3" ID) for pass-throughs | 2 | ~$10 | Amazon |
| 6 | Silicone Sealant + Spray Foam | 1 | ~$15 | Home Depot |
| | **Unit A Subtotal** | | **~$550** | |

### Unit A — Water Block Option (add to above)

| # | Item | Qty | Est. Price |
|---|---|---|---|
| 7 | Heatkiller IV PRO TR (CPU) | 1 | ~$150 |
| 8 | Bykski RTX 5080 Block (GPU) | 1 | ~$100 |
| 9 | EK Momentum² Quad RAM × 2 (or Alphacool × 2) | 2 | ~$440 (EK) / $140 (AC) |
| 10 | Alphacool M.2 NVMe Block | 1 | ~$50 |
| 11 | Heatkiller VRM Block | 1 | ~$60 |
| 12 | Barrow Chipset Block | 1 | ~$25 |
| 13 | Fittings (22× compression, 8× 90°, 2× Y-split) | — | ~$165 |
| 14 | Tubing ZMT 3m × 3 | 3 | ~$54 |
| 15 | Pipe Insulation Foam | 6 | ~$18 |
| 16 | Neoprene + Conformal Coating + Desiccant | — | ~$60 |
| | **Water Block Option Subtotal** | | **~$1,120** (EK) / **~$820** (AC) |

### Unit A — Submersion Option (alternative to above)

| # | Item | Qty | Est. Price |
|---|---|---|---|
| 7 | White Mineral Oil USP (9 gallons) | 9 | ~$180 |
| 8 | Cable Extensions (24-pin, EPS, PCIe) | 1 set | ~$25 |
| | **Submersion Option Subtotal** | | **~$205** |

### Unit B: Cryo Freezer + Reservoir

| # | Item | Qty | Est. Price | Source |
|---|---|---|---|---|
| 16 | Mini Chest Freezer 3.5-5 cu ft (used) | 1 | **$50** | FB Marketplace |
| 17 | Stainless Steel Stock Pot 5-10L | 1 | ~$20 | Amazon |
| 18 | Barrow D5 Pump + Top | 1 | ~$75 | Amazon |
| 19 | G1/4" Bulkhead Fittings (pair) | 1 | ~$10 | Amazon |
| 20 | Propylene Glycol (1 gal) + Distilled Water + Biocide | — | ~$35 | Amazon |
| 21 | Silicone Sealant + Foam | 1 | ~$10 | Home Depot |
| | **Unit B Subtotal** | | **~$200** | |

### Unit C: External Server Rack

| # | Item | Qty | Est. Price | Source |
|---|---|---|---|---|
| 22 | NavePoint 12U Open Frame Rack | 1 | ~$90 | Amazon |
| 23 | Alphacool NexXxoS 360mm Radiator | 1 | ~$65 | Amazon |
| 24 | Arctic P12 PWM PST (5-pack) | 1 | ~$30 | Amazon |
| 25 | Quick-Disconnect Fittings (3 pairs) | 3 | ~$45 | Amazon |
| 26 | ATX PSU Rack Shelf | 1 | ~$15 | Amazon |
| 27 | USB/HDMI/DP/Ethernet Panel Mount | 1 set | ~$25 | Amazon |
| 28 | ESP32 + Sensors + OLEDs + LEDs + Relay | 1 kit | ~$50 | Amazon |
| 29 | STC-1000 Thermostat × 2 (one per freezer) | 2 | ~$24 | Amazon |
| 30 | L-Brackets + Bolts + Vibration Isolators | 1 set | ~$20 | Home Depot |
| 31 | Illuminated Power Button | 1 | ~$8 | Amazon |
| | **Unit C Subtotal** | | **~$390** | |

### Totals

| Configuration | Cooling Cost | With PC Components |
|---|---|---|
| **Version C + Submersion** | ~$550 + $205 + $200 + $390 = **~$1,345** | **~$6,395** |
| **Version C + Water Blocks (Alphacool RAM)** | ~$550 + $820 + $200 + $390 = **~$1,960** | **~$7,010** |
| **Version C + Water Blocks (EK RAM)** | ~$550 + $1,120 + $200 + $390 = **~$2,260** | **~$7,310** |

---

## All Three Versions Compared

| Feature | V-A Submersion | V-B Full Block | V-C Modular |
|---|---|---|---|
| **Freezer units** | 1 (Frigidaire) | 1 (Frigidaire) | 2 (Frigidaire + mini) |
| **External rack** | 8U | 12U | 12U |
| **Cooling method** | Mineral oil bath | Water blocks on all 7 components | Your choice (submersion OR blocks) |
| **Components cooled** | All (submerged) | All (dedicated blocks) | All (either method) |
| **Compressor power** | 1× (1/4-1/3 HP) | 1× (1/4-1/3 HP) | 2× (combined ~1/2 HP) |
| **Radiator** | None needed | In rack | In rack |
| **Coolant temp** | Oil at 0-10°C | Glycol at 0-5°C | Glycol at -5 to 5°C |
| **CPU full load** | 25-40°C | 25-40°C | 20-35°C |
| **Maintenance** | Messy (oil) | Clean (coolant) | Clean (coolant) or messy (oil) |
| **Difficulty** | Medium | Hard | Hardest |
| **Cost (cooling)** | ~$920 | ~$2,215 | ~$1,345-2,260 |
| **YouTube factor** | Huge (oil submersion) | High (precision cooling) | Massive (multi-freezer data center) |
| **Scalability** | Limited | Limited | Excellent (add more units) |
| **Redundancy** | None | Radiator failsafe | Dual compressor + radiator |
| **Best for** | Wow factor, simplicity | Daily driver, cleanest | Maximum performance, content series |

---

## YouTube Episode Arc for Version C

| Ep | Title | Content |
|---|---|---|
| 1 | "I'm Building an AI Data Center from Freezers" | Concept reveal, buy freezers, unbox |
| 2 | "Tearing Down TWO Freezers for Science" | Teardown Unit A + Unit B, measurements |
| 3 | "The Cryo Reservoir: -10°C Coolant" | Build Unit B, reservoir, pump, test temps |
| 4 | "The Server Rack Cage" | Build + mount Unit C, radiator, PSU, I/O |
| 5 | "Wiring Three Units Together" | Insulated tubing, manifold, leak test |
| 6 | "Installing a Threadripper PRO" | Mount motherboard, all water blocks (or submersion) |
| 7 | "The ESP32 Brain" | Build monitoring system, OLED, dew point |
| 8 | "First Boot: Multi-Freezer AI Workstation" | Power on, stress test, results |
| 9 | "Running 70B LLM Models at Sub-Zero" | AI benchmarks at extreme temps |
| 10 | "3 Months Later: Did It Survive?" | Long-term reliability follow-up |

---

*Coolputer Version C — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
