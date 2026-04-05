# DIY Sub-Ambient Cooling System — Research

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**Target:** Threadripper PRO 9965WX (350W TDP) + RTX 5080 (300W)

---

## Concept Overview

A **phase-change chiller** integrated with a custom water cooling loop.
The system upcycles a window AC unit or chest freezer compressor to chill
a reservoir of coolant to sub-ambient temperatures (0°C to -20°C), which
then flows through a CPU water block and optional GPU block.

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CHILLER UNIT                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │COMPRESSOR│───▶│CONDENSER │───▶│CAPILLARY/METERING│   │
│  │(1/4+ HP) │    │(+ FAN)   │    │TUBE              │   │
│  └────▲─────┘    └──────────┘    └────────┬─────────┘   │
│       │                                    │             │
│       │         ┌──────────────────────┐   │             │
│       └─────────│ COPPER COIL          │◀──┘             │
│                 │ EVAPORATOR           │                  │
│                 │ (submerged in        │                  │
│                 │  reservoir)          │                  │
│                 └──────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │    RESERVOIR        │
              │  (insulated tank,   │
              │   10-20L coolant,   │
              │   copper coil       │
              │   submerged inside) │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  D5 / DDC PUMP      │
              └──────────┬──────────┘
                         │
         ┌───────────────▼───────────────┐
         │     CPU WATER BLOCK           │
         │  (Heatkiller IV PRO sTR5)     │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │     GPU WATER BLOCK           │
         │  (optional, RTX 5080)         │
         └───────────────┬───────────────┘
                         │
         ┌───────────────▼───────────────┐
         │   HEAT DISSIPATER / RADIATOR  │
         │  (360mm/420mm + fans, acts    │
         │   as pre-cooler before        │
         │   returning to reservoir)     │
         └───────────────┬───────────────┘
                         │
                         └──────▶ Back to RESERVOIR
```

---

## How Phase-Change Cooling Works

The refrigeration cycle (identical to a fridge/AC):

1. **Compressor** compresses refrigerant gas → high pressure, warm
2. **Condenser** (with fan) rejects heat → refrigerant becomes liquid
3. **Capillary tube** drops pressure dramatically (few hundred PSI → 10-15 PSI)
4. **Evaporator coil** (submerged in reservoir) — low-pressure liquid boils,
   absorbing heat from the coolant in the reservoir
5. **Refrigerant gas** returns to compressor → cycle repeats

The evaporator coil can reach **-20°C to -40°C** depending on the
refrigerant and compressor power. This chills the reservoir coolant
to near-freezing or below.

---

## Key Design Decisions

### 1. Compressor Source (Upcycled)

| Source | HP Range | Cooling Capacity | Best For |
|---|---|---|---|
| **Window AC 5000-8000 BTU** | 1/6 - 1/3 HP | 1500-2300W | **Best choice — proven in PC builds** |
| **Window AC 10000+ BTU** | 1/3 - 3/4 HP | 2900W+ | Overkill but handles 350W CPU easily |
| Chest Freezer | 1/4 - 1/2 HP | Good | Already optimized for continuous run |
| Dehumidifier | 1/8 - 1/4 HP | Moderate | Compact, but may be undersized |
| Full-size Fridge | 1/8 - 1/6 HP | Low | Marginal for 350W+ heat load |

**Recommendation:** A **5000-8000 BTU window AC** is the sweet spot.
The compressor is designed for continuous operation and has ~1500-2300W
of cooling capacity — far more than the ~650W total heat load
(350W CPU + 300W GPU). This gives massive thermal headroom.

**Overclock.net proven build:** User "[ShowMe!]" converted a $87 Walmart
5000 BTU window AC to a water chiller by submerging the cold-side coils
in a bucket reservoir. Achieved sub-zero coolant temperatures.

### 2. Evaporator Design (Copper Coil in Reservoir)

The evaporator is a **coil of 1/4" OD copper tubing** (12-20 feet)
submerged in the coolant reservoir. The refrigerant flows through this
coil and absorbs heat from the surrounding coolant.

| Parameter | Recommendation |
|---|---|
| **Tubing** | 1/4" OD soft copper refrigeration tubing |
| **Length** | 15-25 feet (more = lower temps, higher capacity) |
| **Coil diameter** | Sized to fit inside reservoir (~6-8" diameter) |
| **Connection** | Brazed to compressor high/low lines |

**From Overclockers.com guide:**
> "The evaporator should be about 12' of 1/4" copper tubing; this should
> give it enough to get all of the Freon to boil off and give you space
> to hold a decent amount of extra Freon for heat load purposes."

For your 350W CPU, err on the longer side (20-25 feet) for maximum
heat absorption capacity.

### 3. Reservoir Design

| Parameter | Recommendation |
|---|---|
| **Material** | Stainless steel pot / insulated cooler / custom acrylic tank |
| **Volume** | 10-20 liters (thermal mass buffer) |
| **Insulation** | Neoprene foam wrap (6-12mm thick) or spray foam |
| **Coolant** | Distilled water + 30-40% propylene glycol (antifreeze) |
| **Target temp** | 0°C to -10°C (below 0°C requires antifreeze mix) |

A larger reservoir acts as a thermal buffer — when the CPU spikes to
350W, the reservoir's thermal mass absorbs the heat while the chiller
catches up. This prevents temperature oscillations.

### 4. Coolant Chemistry

**CRITICAL:** Sub-ambient cooling means the coolant can freeze. You MUST
use antifreeze.

| Mix | Freeze Point | Specific Heat | Notes |
|---|---|---|---|
| Pure distilled water | 0°C | 4.18 J/g·K | Freezes — DO NOT use sub-ambient |
| 70% water / 30% propylene glycol | -13°C | ~3.5 J/g·K | **Good balance** |
| 60% water / 40% propylene glycol | -21°C | ~3.3 J/g·K | **Best for deep sub-ambient** |
| 50% water / 50% propylene glycol | -34°C | ~3.1 J/g·K | Overkill, reduced heat capacity |

**Use propylene glycol (PG), NOT ethylene glycol.** PG is non-toxic.
Add a biocide (silver coil or Mayhems biocide) to prevent algae growth.

**Corrosion:** The loop will have copper (coil, water block), nickel
(block plating), and possibly aluminum (radiator). **Never mix copper
and aluminum in the same loop** — galvanic corrosion will destroy the
aluminum. Use an all-copper/nickel loop or add corrosion inhibitor.

### 5. Condensation — The #1 Enemy

**Sub-ambient cooling WILL cause condensation** on any surface below
the dew point. Condensation on the motherboard = dead motherboard.

| Protection | Method |
|---|---|
| **CPU block insulation** | Neoprene foam gasket around entire block + mounting area |
| **Tubing insulation** | Closed-cell foam pipe insulation on ALL cold tubing |
| **Reservoir insulation** | Full neoprene wrap + sealed lid |
| **Motherboard protection** | Conformal coating (liquid electrical tape) around socket |
| **Backplate insulation** | Neoprene sheet behind motherboard at CPU area |
| **Humidity monitoring** | DHT22 sensor + Arduino/ESP32 for dew point control |
| **Temperature control** | Thermostat to prevent coolant from going too cold |

**The Overclockers.co.uk "Too Tall" build** (Feb 2026) implemented full
dew point control with a custom PCB + humidity/temperature sensors that
automatically adjusts chiller output to stay above dew point. This is
the gold standard approach.

### 6. Pre-Entry Radiator (Heat Dissipater)

A **360mm or 420mm radiator with fans** placed between the GPU output
and the reservoir serves two purposes:

1. **Pre-cools** the returning coolant before it hits the reservoir,
   reducing the load on the chiller
2. **Acts as a safety net** — if the chiller fails, the radiator
   provides enough cooling to prevent thermal shutdown

This is your "heat dissipater with fans before re-entry" — it removes
a significant portion of the heat load before the coolant returns to
the chilled reservoir.

---

## Temperature Targets

| Scenario | Coolant Temp | CPU Temp (est.) | Notes |
|---|---|---|---|
| **Standard water cooling** | 30-40°C | 70-90°C | Baseline comparison |
| **Chiller — mild** | 10-15°C | 35-50°C | Easy, safe, minimal condensation |
| **Chiller — moderate** | 0-5°C | 20-35°C | Good performance, needs insulation |
| **Chiller — aggressive** | -5 to -10°C | 10-25°C | Excellent, full condensation protection needed |
| **Chiller — extreme** | -15 to -20°C | 0-15°C | Diminishing returns, high risk |

**Recommendation:** Target **5-10°C coolant** for daily use. This gives
massive thermal headroom for the 9965WX while keeping condensation
manageable. You can go colder for benchmarking sessions.

---

## Safety Considerations

1. **Refrigerant handling:** In the US, EPA certification is required to
   work with refrigerants. R-134a and R-290 (propane) are commonly available
   without license for small quantities, but check local regulations.
2. **R-290 (propane) is flammable.** Use in well-ventilated areas only.
3. **Electrical safety:** The compressor runs on mains voltage (120V/240V).
   Proper grounding and GFCI protection required.
4. **Condensation:** The single biggest risk. Water + electronics = death.
   Insulate everything. Monitor dew point.
5. **Coolant leaks:** The pump system is pressurized. Use quality fittings
   and leak-test for 24 hours before powering on the PC.
6. **Compressor overheating:** Ensure the condenser has adequate airflow.
   A failed condenser fan = burned compressor.

---

## Reference Builds & Community Resources

| Resource | URL | Key Takeaway |
|---|---|---|
| **Overclockers.com — Phase Change Build Guide** | [Link](https://www.overclockers.com/how-to-build-a-refrigerator-cpu-cooler/) | Complete build-from-scratch guide with materials list |
| **Overclock.net — Window AC to Water Chiller** | [Link](https://www.overclock.net/threads/window-ac-air-conditioner-to-water-chiller-conversion-log.1511297/) | Proven AC-to-chiller conversion with results |
| **Overclock.net — Daily Chiller Build** | [Link](https://www.overclock.net/threads/daily-chiller-build.1749056/) | Daily-driver sub-zero build with condensation solutions |
| **Overclockers.co.uk — Sub-Ambient with Dew Point Control** | [Link](https://forums.overclockers.co.uk/threads/i-built-a-diy-sub-ambient-water-chiller-with-dew-point-control.19011177/) | Feb 2026 build with custom PCB dew point control |
| **Tom's Hardware — Chiller Forum Thread** | [Link](https://forums.tomshardware.com/threads/custom-water-cooling-with-a-chiller.3004294/) | Community discussion on AC chiller integration |
| **Level1Techs — TR sTR5 Waterblocks** | [Link](https://forum.level1techs.com/t/what-cpu-waterblock-should-i-get-for-my-planned-threadripper-7000-build/206499) | Comprehensive sTR5 water block comparison |
| **r/watercooling — TR PRO sTR5 blocks** | [Link](https://www.reddit.com/r/watercooling/comments/1olu22g/threadripper_pro_str5_waterblock/) | Community consensus: Heatkiller IV or EK Magnitude |

---

## Key Findings Summary

1. **5000-8000 BTU window AC** is the proven, budget-friendly compressor source
2. **Heatkiller IV PRO for Threadripper** is the most available sTR5 water block
3. **Copper coil evaporator** (20-25' of 1/4" OD) submerged in insulated reservoir
4. **30-40% propylene glycol** antifreeze mix for sub-ambient operation
5. **Condensation is the #1 risk** — neoprene insulation + conformal coating mandatory
6. **Pre-entry radiator** (360mm+) reduces chiller load and provides failsafe
7. **Target 5-10°C coolant** for daily operation, colder for benchmarking
8. **Total heat load ~650W** (CPU 350W + GPU 300W) — well within a 5000 BTU AC's capacity

---

*DIY Sub-Ambient Cooling Research — Copyright 2026 Alexandros Karales / ZapAGI.*
