# Coolputer Advanced — Research: Immersion, Full-Block, & Modular Designs

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Base Unit:** Frigidaire 10 cu ft Chest Freezer (Black) — EFRF1013  

---

## Selected Freezer: Frigidaire EFRF1013

| Spec | Value |
|---|---|
| **Model** | Frigidaire EFRF1013 (Black Granite Design) |
| **Capacity** | 10 cu ft |
| **External Dimensions** | 44"W × 25.4"D × 33.3"H |
| **Internal Dimensions (est.)** | ~38"W × 19"D × 25"H |
| **Defrost** | Manual (simple, no auto-heat cycles) |
| **Temperature Range** | 0°F to 10°F (-18°C to -12°C) |
| **Controls** | External temperature adjustment |
| **Drain** | Easy external defrost drain |
| **Compressor** | ~1/4-1/3 HP (typical for 10 cu ft) |
| **Refrigerant** | R-600a (isobutane) — common in modern units |
| **Color** | Black granite finish |
| **Garage Ready** | Yes (operates in 0-110°F ambient) |
| **Price** | **$413.10** |
| **Pickup** | Home Depot — Midtown Manhattan (Relo 6177) |
| **Features** | Power-on indicator, removable wire basket, aluminum interior liner |

**Why this unit is ideal:**
- Black finish = professional, YouTube-ready aesthetic
- Manual defrost = no heating elements cycling on/off
- External controls = accessible even when modded
- Easy drain = useful for coolant management
- Aluminum interior liner = durable, won't rust
- Garage ready = designed for wide ambient temp ranges
- 10 cu ft = perfect size for EEB workstation + zones

---

## Research Area 1: Immersion/Submerged Cooling

### What Is Immersion Cooling?

The entire motherboard + GPU + RAM is **submerged in a dielectric
(non-conductive) fluid** inside a tank. The fluid absorbs heat directly
from all components simultaneously — no water blocks, no thermal paste
interfaces, no fans needed.

### Fluid Options Compared

| Fluid | Type | Dielectric? | Thermal Conductivity | Specific Heat | Viscosity | Boiling Point | Cost/Gallon | Notes |
|---|---|---|---|---|---|---|---|---|
| **Mineral Oil** (white, USP) | Single-phase | Yes | 0.13 W/m·K | 1.67 J/g·K | 15-30 cSt | >300°C | **$15-25** | Cheapest, proven, messy |
| **STEOIL MO-01** | Single-phase | Yes | 0.13 W/m·K | 1.67 J/g·K | ~15 cSt | >300°C | ~$30 | Formulated for PC immersion |
| **Novec 7100** (3M) | Two-phase | Yes | 0.069 W/m·K | 1.18 J/g·K | 0.58 cSt | **61°C** | **$400-600** | Discontinued Jan 2025 by 3M |
| **TMC-7100** | Two-phase | Yes | ~0.069 W/m·K | ~1.18 J/g·K | ~0.58 cSt | ~61°C | ~$350-500 | **Drop-in Novec 7100 replacement** |
| **TMC-649** | Two-phase | Yes | Similar | Similar | Similar | ~49°C | ~$400+ | Novec 649 replacement |
| **Shell Diala S4** | Single-phase | Yes | ~0.13 W/m·K | ~1.8 J/g·K | ~8 cSt | >300°C | ~$40-60 | Transformer oil, excellent |
| **Engineered Fluid (BitCool)** | Single-phase | Yes | 0.14 W/m·K | 2.0 J/g·K | ~5 cSt | >300°C | ~$50-80 | Best single-phase performance |

### Single-Phase vs Two-Phase Immersion

| Feature | Single-Phase (Mineral Oil) | Two-Phase (TMC-7100/Novec) |
|---|---|---|
| **How it works** | Fluid stays liquid, absorbs heat, circulated to heat exchanger | Fluid boils at component surface, vapor rises, condenses on cold plate, drips back |
| **Cooling power** | Good — relies on convection + circulation | Excellent — latent heat of vaporization is massive |
| **Temperature control** | Needs pump + heat exchanger | Self-regulating — boils at fixed temp |
| **Complexity** | Medium — pump, heat exchanger | Lower — condenser coil above fluid |
| **Cost** | **Very low** ($50-100 for full fill) | **Very high** ($2,000-5,000 for full fill) |
| **Mess factor** | HIGH — oil gets everywhere, hard to clean | Low — evaporates clean |
| **Long-term reliability** | Proven 2-4+ years (Puget Systems) | Proven in data centers |
| **Fan survival in fluid** | Fans work fine in oil (Puget confirmed 4+ years) | Fans not needed |
| **Maintenance** | Oil change every 12-24 months | Fluid top-off (evaporation loss) |
| **Component removal** | Messy — oil drips everywhere | Clean — evaporates in minutes |

### Immersion + Freezer: The Innovation

**Nobody has combined immersion cooling with a chest freezer's
refrigeration system.** Here's why it's brilliant:

1. Freezer chills the dielectric fluid to sub-ambient temps (0-10°C)
2. Fluid directly contacts ALL components — uniform cooling
3. No water blocks needed — fluid IS the cooling medium
4. No condensation risk — components are SUBMERGED (no air interface)
5. The freezer's compressor handles heat removal from the fluid
6. Massive thermal mass (10+ gallons of fluid = huge buffer)

**Key insight:** Condensation is impossible when components are
submerged — the fluid displaces all air. This eliminates the #1
risk of sub-ambient cooling.

### Immersion Cooling Problems & Solutions

| Problem | Cause | Solution |
|---|---|---|
| **Oil is messy** | Mineral oil clings to everything | Use nitrile gloves, have paper towels ready. Or use engineered fluid. |
| **Fans spin but don't cool** | No air to move in liquid | Remove all fans, rely on natural convection + pump circulation |
| **GPU sag** | Components heavy + buoyancy | Mount vertically on brackets, or use horizontal tray |
| **Rubber seals degrade** | Mineral oil attacks some rubbers | Use nitrile/EPDM O-rings. Most PC components are fine (Puget: 4+ years no degradation) |
| **Hard to upgrade** | Must drain fluid to swap parts | Use quick-drain valve. Or accept the mess. |
| **Thermal expansion** | Oil expands when hot | Leave 2-3" headroom in tank. Don't overfill. |
| **Oil oxidation** | Heat + air = degradation over time | Keep fluid below 50°C (freezer handles this). Seal tank. |
| **PCIe slots** | Oil may interfere with high-speed signals | Not observed in practice. Dielectric fluid doesn't conduct. |

### Long-Term Reliability (Puget Systems Data)

Puget Systems ran a mineral oil PC for **4+ years** as a public demo:
- Fans: Still spinning, no bearing degradation
- Rubber seals: No visible deterioration  
- PCBs: No corrosion, no signal issues
- Oil: Required change every 12-18 months (darkening/particles)
- Thermal performance: Consistent throughout

**Verdict:** Mineral oil immersion is proven reliable for multi-year
daily operation.

---

## Research Area 2: Full Liquid Block Cooling (Every Component)

### Available Water Blocks for Every Component

| Component | Block | Manufacturer | Est. Price | Source |
|---|---|---|---|---|
| **CPU (sTR5)** | Heatkiller IV PRO for Threadripper (Cu/Ni) | Watercool | ~$150 | [Watercool](https://shop.watercool.de) / [Newegg](https://www.newegg.com) |
| **GPU (RTX 5080)** | Bykski / EK / Alphacool full-cover block | Various | ~$80-200 | [Amazon](https://www.amazon.com) |
| **RAM (DDR5 RDIMM)** | EK-Quantum Momentum² Quad RAM Set D-RGB | EKWB | ~$200-250 | [EKWB](https://www.ekwb.com/shop/ek-quantum-momentum2-quad-ram-module-set-d-rgb) |
| **RAM (DDR5)** | Alphacool Core DDR5 Water Block | Alphacool | ~$60-80 | [Alphacool](https://shop.alphacool.com) |
| **NVMe M.2** | Alphacool Core M.2 NVMe PCIe 5.0 Liquid Cooler | Alphacool | ~$40-70 | [Alphacool](https://shop.alphacool.com/en/shop/m.2ssdhdd-cooler/) |
| **VRM** | Heatkiller IV VRM-Block (DIY/universal) | Watercool | ~$50-80 | [Watercool](https://shop.watercool.de) |
| **Chipset** | Universal chipset block (40mm × 40mm) | Alphacool / Barrow | ~$20-30 | [Amazon](https://www.amazon.com) |

### WRX90E-SAGE SE: 8 DIMM Slots = 2 Quad RAM Blocks

The ASUS WRX90E-SAGE SE has **8 DDR5 RDIMM slots** (4 per side of CPU).
To water-cool all 8 DIMMs:
- 2× EK-Quantum Momentum² Quad RAM Sets = ~$400-500
- OR 2× Alphacool Core DDR5 kits = ~$120-160

**Note on RDIMM cooling:** DDR5 RDIMMs run significantly hotter than
standard DDR5 due to onboard PMIC + VRM. Level1Techs forum users
report 80-95°C on RDIMMs without active cooling. Water cooling is
**highly recommended** for the WRX90E-SAGE SE.

### Full-Block Loop Complexity

With every component on the loop, flow path becomes critical:

```
Reservoir → Pump → CPU Block → RAM Block L → RAM Block R →
GPU Block → NVMe Block → VRM Block → Chipset Block →
Radiator → Reservoir
```

**Series vs Parallel:**
- **Series** (daisy-chain): Simplest, but each component gets
  progressively warmer coolant. CPU first = coldest.
- **Parallel** (Y-splits): More complex plumbing, but all components
  get equal-temp coolant. Better for sub-ambient.

**Recommendation for sub-ambient:** Use **parallel splits** for CPU
and GPU (highest heat), with RAM/NVMe/VRM/chipset in a separate
series branch.

```
                    ┌──▶ CPU Block ──────────────┐
Reservoir → Pump ──┤                              ├──▶ Radiator → Reservoir
                    └──▶ GPU Block ──────────────┘
                              │
                    ┌─────────┴──────────┐
                    │ RAM L → RAM R →    │
                    │ NVMe → VRM →       │
                    │ Chipset            │
                    └────────────────────┘
```

---

## Research Area 3: Modular Multi-Freezer System

### Concept: Separate Freezers for Separate Roles

Instead of one large freezer doing everything, use **multiple smaller
units** (mini freezers, wine coolers, dorm fridges), each dedicated
to a specific thermal role, linked by insulated tubing.

| Unit | Role | Size | Temp Target | Contents |
|---|---|---|---|---|
| **Unit A: Main Case** | Motherboard chamber | 10 cu ft chest (Frigidaire) | 10-20°C (passive cold) | Motherboard, CPU, GPU, RAM |
| **Unit B: Cryo Reservoir** | Chiller for coolant | 3-5 cu ft mini freezer | -15 to 0°C | Reservoir + copper coil |
| **Unit C: Heat Exchange** | Warm-side radiator bay | Open server rack cage | Ambient | Radiator, fans, PSU |
| **Unit D: Storage & Control** | NVMe, ESP32, I/O | Small enclosure on rack | Ambient | Drives, controller, I/O panel |

### Why Modular?

1. **Each unit optimized for its thermal zone** — no barrier engineering
   needed inside a single box
2. **Smaller freezers are cheaper** — a 3.5 cu ft mini freezer is $80-150
3. **Easier to maintain** — disconnect any unit without disturbing others
4. **Scalable** — add more chiller units for more cooling capacity
5. **YouTube gold** — "I wired 4 freezers together to make a supercomputer"
6. **Redundancy** — if one chiller fails, the other keeps running

### Multi-Freezer Linking

All units connected by **insulated tubing** (EPDM + foam insulation):

```
┌───────────┐     insulated      ┌───────────┐     insulated     ┌───────────┐
│  UNIT B   │◀── coolant tube ──▶│  UNIT A   │◀── coolant tube ─▶│  UNIT C   │
│  Cryo     │    (cold supply)   │  Main PC  │   (warm return)   │  Radiator │
│  Reservoir│                    │  Chamber  │                   │  + PSU    │
│  (-10°C)  │                    │  (15°C)   │                   │  (ambient)│
└───────────┘                    └───────────┘                   └───────────┘
    3.5 cu ft                     10 cu ft                        Server rack
    mini freezer                  Frigidaire                      open frame
```

### Small Freezer Options for Unit B (Cryo Reservoir)

| Model | Size | Price (new) | Price (used) | Notes |
|---|---|---|---|---|
| **Midea MRC04M3AWW** | 3.5 cu ft | ~$120 | $40-60 | Compact, good compressor |
| **Insignia NS-CZ35WH** | 3.5 cu ft | ~$130 | $40-60 | Best Buy house brand |
| **Frigidaire EFRF5003** | 5.0 cu ft | ~$180 | $50-80 | Same brand, matches main |
| **Any mini chest freezer** | 3-5 cu ft | $100-200 | $30-80 | FB Marketplace deals |

**The cryo reservoir doesn't need to be large.** A 3.5 cu ft freezer
can hold a 5-10L reservoir easily. The freezer's cold air chills the
reservoir walls. The smaller the freezer, the faster it reaches target
temp for a given reservoir size.

---

## Research Area 4: External Server Rack Cage

### Concept

Mount an **open-frame server rack** (8U-12U) on the side of the main
Frigidaire freezer. This holds:
- PSU (with its own ventilation)
- Radiator + exhaust fans
- NVMe drive caddies
- ESP32 controller + displays
- Cable management
- Quick-connect tubing manifold

### Why External Rack?

1. **No cutting the freezer for PSU/radiator** — keeps main freezer
   intact for max insulation
2. **Standard 19" rack format** — use off-the-shelf rack shelves,
   blanking panels, cable management
3. **Professional aesthetic** — looks like a real server/workstation
4. **Easy access** — swap PSU, drives, controller without opening freezer
5. **Heat isolation** — all warm components outside the cold zones

### Rack Options

| Rack | Size | Style | Price | Source |
|---|---|---|---|---|
| **StarTech RK819SIDEM** | 8U | Wall-mount, side-mount, open | ~$80 | [Amazon](https://www.amazon.com/s?k=startech+8U+open+frame+rack) |
| **NavePoint 9U Open Frame** | 9U | Desktop/wall, open | ~$60-80 | [Amazon](https://www.amazon.com/s?k=navepoint+9U+open+frame+rack) |
| **Tecmojo 12U Open Frame** | 12U | Desktop, open, compact | ~$80-120 | [Amazon](https://www.amazon.com/s?k=tecmojo+12U+open+frame+rack) |
| **DIY 2020 Extrusion Rack** | Custom | Any size, fully custom | ~$40-80 | [Amazon](https://www.amazon.com/s?k=2020+aluminum+extrusion+kit) |
| **RackSolutions Open Frame 2-Post** | 8-12U | Desktop, 2-post, minimal | ~$50-100 | [RackSolutions](https://www.racksolutions.com/server-racks) |

**Recommendation:** The **NavePoint 9U or StarTech 8U open frame** is
perfect — small enough to mount on the freezer's side, big enough for
PSU + radiator + drives.

### Rack Mounting to Freezer

```
SIDE VIEW:

     ┌──────────────────────┐
     │   FRIGIDAIRE 10 CU   │
     │   FT CHEST FREEZER   │
     │                      │  ┌──────────────┐
     │   (Main PC Chamber)  │  │  8U SERVER   │
     │                      │──│  RACK CAGE   │
     │                      │  │              │
     │                      │  │  - PSU       │
     │                      │  │  - Radiator  │
     │                      │  │  - Fans      │
     │                      │  │  - NVMe      │
     │                      │  │  - ESP32     │
     └──────────────────────┘  │  - I/O Panel │
        44"W × 25.4"D         └──────────────┘
                                  ~19"W × 20"D
```

**Attachment method:**
- L-brackets bolted to the freezer's exterior steel shell
- Rubber vibration isolators between rack and freezer
- Insulated tubing pass-through from freezer side wall to rack
- All power cables routed through the rack

---

## Research Area 5: Advanced Cooling Methods Comparison

### Method Ranking for YouTube Content

| # | Method | Difficulty | Cost | Performance | YouTube Factor | Best For |
|---|---|---|---|---|---|---|
| 1 | **Submerged Mineral Oil + Freezer** | Medium | Low | Excellent | 🔥🔥🔥🔥🔥 | Version A |
| 2 | **Full Water Block + Freezer Chiller** | Hard | Medium | Excellent | 🔥🔥🔥🔥 | Version B |
| 3 | **Modular Multi-Freezer + Rack** | Hard | Medium | Excellent | 🔥🔥🔥🔥🔥 | Version C |
| 4 | **Two-Phase Engineered Fluid** | Expert | Very High | Best | 🔥🔥🔥🔥🔥 | Future upgrade |
| 5 | **Peltier/TEC Assist** | Medium | Medium | Good | 🔥🔥🔥 | Add-on to any version |
| 6 | **Liquid Nitrogen (LN2)** | Expert | High (ongoing) | Extreme | 🔥🔥🔥🔥🔥 | Benchmarking only |
| 7 | **Dry Ice Assist** | Easy | Medium (ongoing) | Good | 🔥🔥🔥 | Temporary boost |

### Method 5: Peltier/TEC Assist (Add-On for Any Version)

Thermoelectric coolers (Peltier modules) can be sandwiched between the
coolant flow and the components for additional spot cooling:

| Spec | Value |
|---|---|
| **Module** | TEC1-12706 (12V, 6A, 72W max) |
| **Delta-T** | Up to 68°C across the module |
| **Use case** | Stack on top of CPU block for extra cold |
| **Power** | Each module draws 72W from PSU |
| **Cost** | ~$3-5 per module |

**WARNING:** TECs generate waste heat on the hot side that must be
removed. In a freezer, this heat goes into the cold zone — the
freezer's compressor must handle it. Use sparingly.

### Method 6: Two-Phase Engineered Fluid (Future Upgrade)

3M discontinued Novec in Jan 2025, but **TMC Industries** now produces
drop-in replacements:

| Fluid | Replaces | Boiling Point | Cost/Liter |
|---|---|---|---|
| **TMC-7100** | Novec 7100 | 61°C | ~$100 |
| **TMC-649** | Novec 649 | 49°C | ~$110 |
| **TMC-7500** | Novec 7500 | 128°C | ~$120 |

To fill a 10 cu ft freezer to submerge a motherboard, you'd need
~30-40 liters = **$3,000-4,000** in fluid alone. This is a future
upgrade path, not a starting point.

**Two-phase in a freezer:** The fluid would boil at component surfaces,
vapor rises, hits the freezer's cold walls/ceiling, condenses, drips
back down. Self-regulating, zero pumps needed. Absolutely stunning
visually — bubbles rising from the CPU under freezer-cold fluid.

---

## Research Area 6: Heat Exchanger Designs

### Types of Heat Exchangers for the External Rack

| Type | Description | Pros | Cons | Best For |
|---|---|---|---|---|
| **Radiator + Fans** | Standard PC radiator (360mm/420mm) | Simple, proven, cheap | Large, noisy at high RPM | Version B rack |
| **Copper Coil in Air** | Coiled copper tubing with fins + fan | DIY, cheap, custom size | Less efficient than rad | Budget builds |
| **Plate Heat Exchanger** | Brazed plate (like HVAC) | Extremely efficient, compact | Expensive ($80-200) | Pro builds |
| **Car Heater Core** | Repurposed automotive heater | Very efficient, cheap ($20-40) | Needs adaptation fittings | Budget Version B |
| **Mo-Ra3 420** | External "monster radiator" (420×420mm) | Insane cooling capacity | Large, expensive ($150+) | Overkill option |
| **Immersion Air Bubbler** | Air pumped through fluid | Adds convection + O2 | Can oxidize oil faster | Version A only |

### Plate Heat Exchanger (Recommended for Pro Build)

A **brazed plate heat exchanger** (BPHE) is what industrial chillers use.
Two fluid circuits pass through alternating plates — extremely efficient
heat transfer in a tiny package.

For our use: Loop coolant on one side, ambient air (via fan) or a
second cooling loop on the other side.

| Model | Plates | Capacity | Size | Price |
|---|---|---|---|---|
| **Duda Energy 30-plate BPHE** | 30 | ~50 kW | 7.5" × 3" × 3" | ~$50-80 |
| **Kelvion GBS 200H-30** | 30 | ~30 kW | Similar | ~$100-150 |

A 30-plate BPHE can handle 50 kW — our 650W PC is literally 1.3%
of its capacity. Total overkill. A 10-plate unit would suffice.

---

## Summary: Three Versions to Build

| Version | Name | Cooling Method | Freezer Config | External | Difficulty | Cost (cooling only) |
|---|---|---|---|---|---|---|
| **A** | **Coolputer Submersion** | Mineral oil immersion in freezer | Single Frigidaire 10 cu ft | Server rack cage (PSU, I/O) | Medium | ~$600-800 |
| **B** | **Coolputer Liquid** | Full water blocks on every component | Single Frigidaire 10 cu ft | Server rack cage (PSU, radiator, I/O) | Hard | ~$1,200-1,600 |
| **C** | **Coolputer Modular** | Multi-freezer linked system | Frigidaire 10 cu ft + mini freezer | Server rack cage (PSU, radiator, I/O) | Hardest | ~$1,400-2,000 |

All three versions use the **Frigidaire EFRF1013 Black 10 cu ft**
as the primary unit with an **external server rack cage** mounted
on the side.

---

*Coolputer Advanced Research — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
