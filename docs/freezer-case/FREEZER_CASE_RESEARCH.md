# Project: Coolputer — Chest Freezer AI Workstation Case

## Research & Prior Art Analysis

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Project Codename:** Coolputer  

---

## Why a Freezer? The Thesis

A chest freezer already contains a **complete phase-change refrigeration
system** — compressor, condenser, evaporator coils, capillary tube, and
insulation. Instead of buying these components separately (our previous
$650+ chiller build), we upcycle the entire freezer as both the **case
AND the cooling system** in one integrated unit.

**The problem:** Everyone who has tried "PC in a freezer" before has
failed for predictable engineering reasons. We solve all of them.

---

## Prior Art: What Others Have Tried (and Why They Failed)

### 1. "Just Put a PC in a Freezer" Attempts

**HardForum, Overclock.net, Reddit (2008-2024)**

Dozens of builders have tried literally placing PC components inside a
running freezer. Results are consistently poor:

| Problem | Why It Happens |
|---|---|
| **Compressor burns out** | Domestic freezer compressors are 1/10-1/6 HP, designed for ~50W heat loads. A PC dumps 350-650W of heat. The compressor runs 100% duty cycle and overheats. |
| **Condensation destroys motherboard** | Opening the lid introduces humid air. Cold surfaces below dew point → water droplets on PCBs → short circuits → dead hardware. |
| **No airflow** | Freezers are sealed insulated boxes. PC components need airflow. Heat pockets form around GPU/VRM. |
| **PSU fights the freezer** | PSU dumps 50-100W of waste heat INTO the cold zone, making the compressor work even harder. |
| **HDDs/SSDs fail** | Magnetic HDDs fail below ~5°C (lubricant thickens). NVMe controllers don't like condensation. |
| **Frost buildup** | Moisture in sealed air freezes on coils → reduced cooling → compressor overworks. |
| **Can't access components** | Everything crammed in a box with no organization. Maintenance is a nightmare. |

**Verdict:** Simply placing a PC in a freezer is an engineering failure.

### 2. Thermaltake Xpressar RCS100 (2008)

The only **commercial** refrigerated PC case ever made.

| Feature | Detail |
|---|---|
| **Design** | Full ATX case with built-in micro compressor |
| **Cooling** | Phase-change directly on CPU (not water loop) |
| **Compressor** | Tiny, 50W, designed for CPU only |
| **Price** | $699 |
| **Result** | Discontinued. Too expensive, compressor too weak, only cooled CPU. GPU/VRM still needed air cooling. Condensation issues. |

**Lesson:** A tiny integrated compressor can't handle modern heat loads.
Need at least 1/6 HP for a 350W CPU.

### 3. Matt Marshall's Icebox PC (2024, PCGamesN Feature)

Professional refrigeration engineer. Best prior art.

| Feature | Detail |
|---|---|
| **Design** | External lab circulator chiller → tubes → PC case |
| **Coolant** | Runs at 8°C (just above condensation point) |
| **Key quote** | "For my next build, I'm going to use a slightly bigger case and fit the refrigeration equipment in the bottom of it in a **thermally isolated compartment**, making a one-box refrigerated PC." |
| **Result** | Excellent temps, clean build, but TWO separate units. |

**Lesson:** The refrigeration engineer himself says the next step is
a **thermally isolated compartment** inside the case. That's exactly
what we're building — but we go further with MULTI-ZONE isolation.

### 4. Overclock.net "Daily Chiller Build" (2020-2024)

| Feature | Detail |
|---|---|
| **Design** | Separate chiller + radiator inside a freezer for cold air |
| **Key insight** | Put a radiator INSIDE the freezer so cold air helps cool the water, then pipe it to the PC outside |
| **Result** | Works well but is two separate units |

**Lesson:** Using the freezer's cold zone to assist a water cooling
loop is smart. We do this but with the PC INSIDE the freezer.

### 5. Overclockers.co.uk "Too Tall" Build (Feb 2026)

| Feature | Detail |
|---|---|
| **Design** | Custom-built compressor chiller with dew point control |
| **Innovation** | Custom PCB with humidity sensors + automatic chiller power modulation |
| **Result** | Gold standard for condensation prevention |

**Lesson:** Automated dew point control is the key to safe sub-ambient.
We integrate this.

---

## What Makes Coolputer Different: The Innovation

**Nobody has built a multi-zone thermally isolated workstation inside
a chest freezer with separate compartments for each thermal requirement.**

### The 5-Zone Thermal Architecture

This is the core innovation. Instead of one cold box with everything
inside, we divide the freezer into **5 thermally isolated zones**, each
optimized for its contents:

| Zone | Contents | Target Temp | Sealed? | Airflow |
|---|---|---|---|---|
| **Zone 1: Cryo Core** | Coolant reservoir + evaporator coil | -5°C to 5°C | Yes, sealed | None (liquid only) |
| **Zone 2: Cold Chamber** | Motherboard + CPU block + RAM + GPU | 10-20°C | Yes, sealed | Internal recirculation fans only |
| **Zone 3: Heat Exchange** | 360mm radiator + exhaust fans | 25-40°C | Vented to outside | Active exhaust |
| **Zone 4: Power Bay** | PSU + NVMe drives + fan hub | Ambient (~25°C) | Vented to outside | Active intake/exhaust |
| **Zone 5: Control Panel** | Power button, displays, I/O ports, ESP32 | Ambient | Open front | Passive |

### Why This Works (Engineering Analysis)

1. **Compressor never overloaded:** The freezer's existing compressor
   only cools Zone 1 (the reservoir). It never has to fight PC heat
   directly. The reservoir is a thermal buffer. Total coolant heat
   load managed by combination of chiller + Zone 3 radiator.

2. **No condensation on electronics:** Zone 2 (motherboard chamber) is
   sealed and maintained at 10-20°C by the water cooling loop. It's
   cold but ABOVE the dew point. The sealed chamber means no humid air
   enters. Conformal coating provides additional protection.

3. **PSU heat isolated:** Zone 4 has its own ventilation to the outside.
   PSU waste heat (50-100W) never enters the cold zones. This is the
   single biggest improvement over "PC in a freezer" attempts.

4. **Storage at safe temps:** NVMe drives are in Zone 4 (ambient temp),
   not in the cold zone. No condensation, no cold-temp failures.

5. **Thermal barriers:** Foam-core acrylic or XPS foam bulkheads between
   zones prevent thermal crosstalk. Each zone is its own microclimate.

6. **Existing insulation:** The chest freezer's walls are already
   insulated with polyurethane foam — we get free thermal isolation.

7. **Cold air sinks:** In a chest freezer, cold air naturally stays at
   the bottom. Zone 1 (coldest) is at the bottom. Opening the lid
   doesn't dump cold air out (unlike an upright fridge).

---

## Freezer Selection Criteria

### Ideal: 10-14 Cu Ft Chest Freezer

| Spec | Requirement | Why |
|---|---|---|
| **Type** | Chest (top-opening) | Cold air stays down when opened |
| **Size** | 10-14 cu ft | Enough internal volume for 5 zones |
| **Internal dims** | ~38"W × 20"D × 24"H minimum | EEB board is 12"×13", need room for zones |
| **Compressor** | 1/4 HP+ | Handles reservoir chilling at ~200-300W sustained |
| **Refrigerant** | R-134a or R-600a | Common, serviceable |
| **Defrost** | Manual (no auto-defrost) | Simpler, no heat cycling |
| **Source** | Used from FB Marketplace/Craigslist | $50-150 |

### Size Reference: 10 Cu Ft Chest Freezer (Typical)

```
External: ~44"W × 27"D × 34"H
Internal: ~38"W × 20"D × 26"H
Wall thickness: ~3" (polyurethane foam insulation)
Compressor: 1/4-1/3 HP (usually at rear bottom)
```

**This gives us ~38" × 20" × 26" of internal space** — more than enough
for a full EEB workstation with 5 thermal zones.

---

## YouTube Content Potential

### Episode Arc for Multiversity Channel

| Ep | Title | Content |
|---|---|---|
| 1 | "I'm Building a PC Inside a Freezer (But PROPERLY)" | Concept reveal, prior art failures, design philosophy |
| 2 | "Tearing Down a Chest Freezer for Science" | Freezer teardown, component identification, measurements |
| 3 | "The 5-Zone Thermal Architecture" | Designing compartments, cutting foam bulkheads, building thermal barriers |
| 4 | "Converting the Evaporator to a Water Chiller" | Copper coil build, reservoir, brazing, refrigerant work |
| 5 | "Installing a Threadripper PRO in a Freezer" | Motherboard mounting, water block, cable routing |
| 6 | "The Dew Point Controller" | ESP32 build, humidity sensors, OLED displays |
| 7 | "First Boot: Sub-Zero AI Workstation" | Power on, stress test, temperature results |
| 8 | "Running AI Models at -5°C" | LLM benchmarks, Ollama, fine-tuning at sub-ambient |

### Why This Will Go Viral

- **Nobody has done multi-zone properly** — every freezer PC video is "lol I put a PC in a freezer and it died"
- **Threadripper PRO + RTX 5080** in a freezer = extreme hardware in extreme cooling
- **AI workstation angle** = trending topic
- **Engineering rigor** = differentiates from "I duct-taped a GPU to a frozen pizza" content
- **Upcycling/sustainability** angle = turning e-waste into an AI supercomputer

---

## Key Reference Sources

| Source | URL | Key Insight |
|---|---|---|
| PCGamesN — Icebox PC | [Link](https://www.pcgamesn.com/pc-build/fridge-icebox) | Pro refrigeration engineer's approach, thermally isolated compartment plan |
| Overclockers.com — Phase Change Guide | [Link](https://www.overclockers.com/how-to-build-a-refrigerator-cpu-cooler/) | Complete DIY phase-change build process |
| Overclock.net — AC to Chiller | [Link](https://www.overclock.net/threads/window-ac-air-conditioner-to-water-chiller-conversion-log.1511297/) | Window AC conversion proven |
| Overclock.net — Daily Chiller | [Link](https://www.overclock.net/threads/daily-chiller-build.1749056/) | Radiator-in-freezer assist concept |
| Overclockers.co.uk — Dew Point Chiller | [Link](https://forums.overclockers.co.uk/threads/i-built-a-diy-sub-ambient-water-chiller-with-dew-point-control.19011177/) | Automated condensation prevention |
| HardForum — PC in Freezer | [Link](https://hardforum.com/threads/computer-in-a-freezer-seriously.842419/) | What goes wrong and why |
| Tom's Hardware — Thermaltake Xpressar | [Link](https://www.tomshardware.com/news/Thermaltake-Xpressar-Case,6399.html) | Only commercial attempt, lessons learned |
| Level1Techs — sTR5 Waterblocks | [Link](https://forum.level1techs.com/t/what-cpu-waterblock-should-i-get-for-my-planned-threadripper-7000-build/206499) | Water block selection for Threadripper |
| Maytag — Freezer Dimensions | [Link](https://www.maytag.com/blog/kitchen/freezer-sizes-and-dimensions-guide.html) | Freezer sizing reference |

---

*Coolputer Research — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
