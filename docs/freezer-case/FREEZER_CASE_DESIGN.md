# Project: Coolputer — Design Document

## Multi-Zone Thermally Isolated AI Workstation in a Chest Freezer

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Project Codename:** Coolputer  
**Hardware:** Threadripper PRO 9965WX + ASUS WRX90E-SAGE SE + RTX 5080

---

## Design Philosophy

> "Don't put a PC in a freezer. Turn a freezer into a PC."

Every previous freezer-PC attempt failed because builders treated the
freezer as a dumb box. Coolputer treats the freezer as a **thermal
management platform** with engineered zones, each optimized for its
contents. The freezer's existing refrigeration system becomes the
backbone of a precision chiller loop.

---

## The 5-Zone Architecture

### Top-Down View (Lid Open, Looking Down Into Freezer)

```
┌──────────────────────────────────────────────────────────┐
│                     CHEST FREEZER LID                     │
│              (hinged at back, opens upward)                │
│         ┌──────────────────────────────────┐              │
│         │   ZONE 5: CONTROL PANEL          │              │
│         │   (mounted inside lid)           │              │
│         │   - Power button                 │              │
│         │   - OLED temp/humidity displays  │              │
│         │   - RGB LED strip                │              │
│         └──────────────────────────────────┘              │
└──────────────────────────────────────────────────────────┘

Looking down into the freezer interior (~38"W × 20"D × 26"H):

┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌─────────────────────┐  ┌───────────────────────────┐  │
│  │                     │  │                           │  │
│  │   ZONE 2            │  │   ZONE 3                  │  │
│  │   COLD CHAMBER      │  │   HEAT EXCHANGE           │  │
│  │                     │  │                           │  │
│  │   Motherboard       │  │   360mm Radiator          │  │
│  │   (vertical mount)  │  │   + 3× 120mm Fans         │  │
│  │   CPU Block         │  │                           │  │
│  │   RAM               │  │   Exhaust vent to         │  │
│  │   GPU               │  │   outside (rear wall)     │  │
│  │                     │  │                           │  │
│  │   ~22"W × 16"D      │  │   ~14"W × 16"D           │  │
│  │                     │  │                           │  │
│  └─────────┬───────────┘  └──────────┬────────────────┘  │
│            │  THERMAL BARRIER (XPS foam + acrylic)  │     │
│  ┌─────────┴───────────┐  ┌──────────┴────────────────┐  │
│  │                     │  │                           │  │
│  │   ZONE 1            │  │   ZONE 4                  │  │
│  │   CRYO CORE         │  │   POWER BAY               │  │
│  │                     │  │                           │  │
│  │   Reservoir (10L)   │  │   PSU (1200W)             │  │
│  │   Copper coil       │  │   NVMe drives             │  │
│  │   evaporator        │  │   Fan hub                 │  │
│  │   D5 Pump           │  │   ESP32 controller        │  │
│  │                     │  │                           │  │
│  │   ~22"W × 8"D       │  │   ~14"W × 8"D            │  │
│  │                     │  │                           │  │
│  └─────────────────────┘  └───────────────────────────┘  │
│                                                          │
│  ════════════════════════════════════════════════════════ │
│  FREEZER FLOOR (evaporator coils embedded in walls/floor)│
│  Compressor + Condenser (external, rear/bottom of unit)  │
└──────────────────────────────────────────────────────────┘
```

### Side Cross-Section View (Front to Back)

```
                    LID (hinged at back)
    ┌──────────────────────────────────────┐
    │  Zone 5: Control Panel (inside lid)  │
    └──┬───────────────────────────────┬───┘
       │                               │
  ┌────┴───────────────────────────────┴────┐
  │ ┌───────────────┐ ┌──────────────────┐  │ ← Top half
  │ │  ZONE 2       │ │  ZONE 3          │  │   (above barrier)
  │ │  Cold Chamber │ │  Heat Exchange   │  │
  │ │  Motherboard  │ │  Radiator+Fans   │  │
  │ │  (vertical)   │ │  ↓ exhaust out   │  │
  │ │  CPU+GPU      │ │  (rear vent)     │  │
  │ ├───────────────┤ ├──────────────────┤  │ ← Horizontal
  │ │ THERMAL       │ │ THERMAL          │  │   thermal barrier
  │ │ BARRIER       │ │ BARRIER          │  │
  │ ├───────────────┤ ├──────────────────┤  │ ← Bottom half
  │ │  ZONE 1       │ │  ZONE 4          │  │   (below barrier)
  │ │  Cryo Core    │ │  Power Bay       │  │
  │ │  Reservoir    │ │  PSU + NVMe      │  │
  │ │  Pump         │ │  ↓ exhaust out   │  │
  │ │               │ │  (side vent)     │  │
  │ └───────────────┘ └──────────────────┘  │
  │ ══════════════════════════════════════  │
  │        Freezer insulated floor          │
  ├─────────────────────────────────────────┤
  │  Compressor │ Condenser │ Condenser Fan │ ← External
  └─────────────────────────────────────────┘   (rear/bottom)
```

---

## Zone-by-Zone Detailed Design

### Zone 1: Cryo Core (Bottom-Left)

**Purpose:** Houses the chilled coolant reservoir with the copper coil
evaporator submerged inside. This is where the freezer's refrigeration
system does its work — chilling the coolant.

| Parameter | Value |
|---|---|
| **Location** | Bottom-left quadrant |
| **Size** | ~22"W × 8"D × 12"H |
| **Temperature** | -5°C to +5°C (coolant) |
| **Sealed?** | Yes — fully insulated and sealed |
| **Contents** | Reservoir (10-15L stainless pot), copper coil evaporator, D5 pump, temp sensor |

**How it works:**
1. The freezer's existing evaporator coils run through the walls/floor
   and chill the air inside Zone 1
2. The copper coil evaporator sits in the reservoir, further chilling
   the coolant directly via refrigerant loop
3. Alternatively, if we don't modify the refrigerant loop: the freezer's
   cold air chills the reservoir through its stainless steel walls
   (simpler, no brazing required)
4. D5 pump pushes chilled coolant up to Zone 2 (CPU block)

**Two approaches:**

| Approach | Difficulty | Performance | Risk |
|---|---|---|---|
| **A: Passive chilling** — Freezer air chills the reservoir walls | Easy | Good (5-10°C coolant) | Low |
| **B: Direct coil** — Custom copper coil in reservoir, tapped into refrigerant loop | Hard | Excellent (-5°C coolant) | Medium |

**Recommendation:** Start with **Approach A** (passive). The freezer's
cold air at -15 to -20°C will chill a 10L stainless steel reservoir to
near 0°C over time. The thermal mass of 10L of glycol mix provides
a huge buffer for the 350W CPU heat load. Upgrade to Approach B later
if needed.

### Zone 2: Cold Chamber (Top-Left)

**Purpose:** The motherboard chamber. Sealed, insulated, contains all
core compute components cooled by the water loop.

| Parameter | Value |
|---|---|
| **Location** | Top-left quadrant (above Zone 1) |
| **Size** | ~22"W × 16"D × 14"H |
| **Temperature** | 10-20°C (managed by water cooling + sealed air) |
| **Sealed?** | Yes — sealed from all other zones |
| **Contents** | Motherboard (EEB, vertical), CPU water block, RAM (8 DIMMs), GPU (RTX 5080), internal recirculation fan |

**Motherboard mounting:**
- **Vertical orientation** on a custom bracket or Mountain Mods EEB tray
- Mounted to the thermal barrier wall between Zone 2 and Zone 3
- EEB board (12" × 13") fits comfortably in 22" × 16" chamber
- GPU hangs vertically (may need GPU support bracket or riser cable)

**Thermal management:**
- Water block on CPU provides primary cooling (coolant from Zone 1)
- Optional water block on GPU (or GPU uses its own fans + sealed air)
- Small 120mm recirculation fan inside the chamber prevents hotspots
- Sealed chamber means no outside humid air enters
- Chamber air stays above dew point because it's warmed by VRM/RAM

**Condensation prevention:**
- Chamber is SEALED — no humidity exchange with outside
- All water cooling tubing entering/exiting is insulated with neoprene
- Conformal coating on motherboard PCB around socket as extra safety
- Internal humidity can be reduced by adding silica gel desiccant packs
  (replace monthly) or a small Peltier dehumidifier

**Cable routing:**
- Power cables from Zone 4 (PSU) enter through sealed grommets
- SATA/NVMe cables to Zone 4 through sealed grommets
- I/O cables (USB, HDMI, DP) exit through rear of freezer to Zone 5 or
  external panel

### Zone 3: Heat Exchange (Top-Right)

**Purpose:** Pre-cools the returning coolant before it goes back to the
reservoir in Zone 1. Also serves as a thermal buffer and failsafe.

| Parameter | Value |
|---|---|
| **Location** | Top-right quadrant (above Zone 4) |
| **Size** | ~14"W × 16"D × 14"H |
| **Temperature** | 25-40°C (warm, actively vented) |
| **Sealed?** | No — vented to outside through rear wall |
| **Contents** | 360mm radiator, 3× 120mm exhaust fans, coolant lines |

**How it works:**
1. Warm coolant exits Zone 2 (CPU/GPU) and enters the radiator
2. Fans push air across the radiator and exhaust through a vent cut
   in the rear freezer wall
3. Pre-cooled coolant returns to reservoir in Zone 1
4. This zone runs warm — that's fine, it's vented to outside

**Rear wall modification:**
- Cut a rectangular vent (~14" × 5") in the rear freezer wall
- Line the cut edges with foam weatherstripping
- Mount 120mm fan grille + dust filter on the outside
- The vent ONLY connects to Zone 3 — other zones remain sealed

**Benefit:** The radiator removes 30-50% of the heat load before
coolant reaches Zone 1. This means the freezer compressor only needs
to handle 50-70% of the CPU/GPU heat output — well within its capacity.

### Zone 4: Power Bay (Bottom-Right)

**Purpose:** Houses the PSU, NVMe drives, and all heat-generating
support components that should NOT be in the cold zones.

| Parameter | Value |
|---|---|
| **Location** | Bottom-right quadrant (below Zone 3) |
| **Size** | ~14"W × 8"D × 12"H |
| **Temperature** | Ambient (~25°C) |
| **Sealed?** | No — vented to outside through side wall |
| **Contents** | 1200W PSU, NVMe M.2 drives (in external caddy), fan hub, ESP32 controller, wiring |

**How it works:**
1. PSU mounted with fan facing the vent (exhausts outside)
2. Small intake vent on opposite side for fresh air
3. NVMe drives in a bracket, at safe ambient temperatures
4. All power cables route through sealed grommets to Zone 2

**Side wall modification:**
- Cut intake vent (~6" × 4") on one side
- Cut exhaust vent (~6" × 4") on opposite side or rear
- Mount dust filters on both
- PSU's own fan provides airflow through this zone

**Critical benefit:** PSU waste heat (50-100W) is exhausted OUTSIDE the
freezer. This is the single most important improvement over all previous
freezer-PC builds. In naive builds, the PSU's heat fights the compressor.
Here, it never enters the thermal envelope.

### Zone 5: Control Panel (Inside Lid)

**Purpose:** User interface, monitoring displays, I/O ports, power
controls. The "face" of the build — what viewers see on YouTube.

| Parameter | Value |
|---|---|
| **Location** | Inside the chest freezer lid |
| **Size** | Full lid inner surface |
| **Temperature** | Ambient (lid is open during use or has cutout) |
| **Contents** | Power button, reset button, OLED displays, RGB LED strips, external I/O panel |

**Components mounted to lid:**
- **Power button + reset** (illuminated, industrial-style)
- **2× 0.96" OLED displays** (I2C) showing:
  - Coolant temp (Zone 1 reservoir)
  - CPU temp
  - Ambient humidity + dew point
  - Zone temperatures
- **RGB LED strip** (addressable WS2812B) — changes color with temp
  (blue = cold, green = nominal, red = hot)
- **External I/O panel** with USB-A, USB-C, HDMI, DisplayPort pass-throughs
- **ESP32 microcontroller** — reads all sensors, drives displays, controls
  compressor on/off via relay

**Lid operation:**
- During normal use, lid stays **closed** (components accessed through
  front/rear I/O panel)
- Open lid for maintenance only (after letting Zone 2 warm to ambient)
- Optional: cut a **window** in the lid with clear acrylic/polycarbonate
  for visible internals + RGB lighting

---

## Thermal Barriers: The Key Engineering

### Barrier Material Options

| Material | R-value/inch | Waterproof? | Workable? | Cost |
|---|---|---|---|---|
| **XPS Foam (Extruded Polystyrene)** | R-5.0 | Yes | Easy to cut | ~$0.50/sq ft |
| **Polyiso Foam Board** | R-6.5 | With foil face | Easy to cut | ~$0.75/sq ft |
| **Closed-Cell Spray Foam** | R-6.9 | Yes | Messy but seals gaps | ~$8/can |
| **Acrylic Sheet + Foam Core** | Varies | Acrylic is | Needs tools | ~$2/sq ft |

**Recommended approach:**
1. **Primary barriers:** 2" XPS foam board cut to fit, sealed with
   spray foam at edges
2. **Visual barriers:** 3mm clear acrylic on the Zone 2 side (so you
   can see the motherboard through the window in the lid)
3. **Penetrations:** Sealed with silicone + neoprene grommets where
   tubing/cables pass between zones

### Barrier Placement

```
              Zone 2          │          Zone 3
           Cold Chamber       │       Heat Exchange
                              │
  ────────────────────────────┼────────────────────────
         VERTICAL BARRIER     │     (2" XPS foam +
        (separates left       │      acrylic face)
         from right)          │
  ────────────────────────────┼────────────────────────
                              │
           Zone 1             │          Zone 4
          Cryo Core           │        Power Bay
                              │
```

**Horizontal barrier** (separates top/bottom): 2" XPS foam board, full
width, with sealed cutouts for:
- Coolant tubing (Zone 1 → Zone 2)
- Coolant tubing (Zone 2 → Zone 3 → Zone 1)
- Power cables (Zone 4 → Zone 2)

**Vertical barrier** (separates left/right): 2" XPS foam board, full
depth, with sealed cutouts for:
- Coolant tubing (Zone 2 → Zone 3)
- Coolant return (Zone 3 → Zone 1)

---

## Coolant Flow Path

```
Zone 1 (Reservoir, -5 to 5°C)
    │
    ▼  [D5 Pump]
    │
    ▼  (insulated tubing through barrier)
    │
Zone 2 (CPU Water Block)
    │
    ▼  (through CPU block, absorbs ~350W)
    │
Zone 2 (GPU Water Block — optional)
    │
    ▼  (through GPU block, absorbs ~300W)
    │
    ▼  (through barrier to Zone 3)
    │
Zone 3 (360mm Radiator + Fans)
    │
    ▼  (radiator removes 30-50% of heat)
    │  (warm air exhausted outside)
    │
    ▼  (through barrier back to Zone 1)
    │
Zone 1 (Reservoir — coolant returns, chilled again)
    │
    └──▶ Repeat
```

---

## Freezer Modification Checklist

### Cuts Required

| Location | Size | Purpose | Zone |
|---|---|---|---|
| Rear wall (upper right) | ~14" × 5" | Radiator exhaust vent | Zone 3 |
| Side wall (lower right) | ~6" × 4" | PSU intake vent | Zone 4 |
| Rear wall (lower right) | ~6" × 4" | PSU exhaust vent | Zone 4 |
| Rear wall (bottom) | ~4" × 2" | I/O cable pass-through | External |
| Lid (center) | ~16" × 10" | Acrylic viewing window | Zone 5 |

**IMPORTANT:** When cutting the freezer walls:
- The walls contain polyurethane foam insulation
- The evaporator coils may be embedded in the walls/floor
- **Map the coil routing FIRST** before cutting
- Use a thermal camera or carefully probe to locate coils
- If coils are only in the floor/lower walls, upper wall cuts are safe
- Seal ALL cut edges with spray foam + weatherstripping

### Internal Fabrication

| Item | Material | Purpose |
|---|---|---|
| Horizontal barrier | 2" XPS foam + spray foam edges | Separates top (Zones 2,3) from bottom (Zones 1,4) |
| Vertical barrier | 2" XPS foam + spray foam edges | Separates left (Zones 1,2) from right (Zones 3,4) |
| Motherboard tray | EEB tray or aluminum L-brackets | Vertical mount for ASUS WRX90E-SAGE SE |
| Radiator mount | Aluminum L-brackets | Holds 360mm rad in Zone 3 |
| PSU bracket | Steel L-brackets | Holds ATX PSU in Zone 4 |
| Viewing window frame | Acrylic + silicone seal | Lid cutout window |

---

## Electrical & Control System

### ESP32 Monitoring System

```
ESP32 Dev Board
    ├── DHT22 (Zone 2 — humidity + temp)
    ├── DS18B20 #1 (Zone 1 — coolant temp)
    ├── DS18B20 #2 (Zone 2 — ambient air temp)
    ├── DS18B20 #3 (Zone 3 — radiator exhaust temp)
    ├── DS18B20 #4 (Zone 4 — PSU bay temp)
    ├── OLED Display #1 (coolant + CPU temp)
    ├── OLED Display #2 (humidity + dew point)
    ├── WS2812B LED Strip (RGB status lighting)
    ├── 5V Relay Module (compressor on/off control)
    └── WiFi → Web dashboard / phone alerts
```

**Dew point control logic (Arduino/MicroPython):**
```
if coolant_temp < (dew_point + 3°C):
    compressor_relay.OFF()   // Stop chilling
    status_led = YELLOW
else:
    compressor_relay.ON()    // Resume chilling
    status_led = BLUE

if coolant_temp > 15°C:
    status_led = RED         // Chiller struggling
    alert("Coolant temp high!")

if zone2_humidity > 70%:
    status_led = RED
    alert("Humidity high in Cold Chamber!")
```

### Power Distribution

```
Wall Outlet (120V/15A)
    ├── Freezer Compressor (via thermostat + relay)
    │   └── Controlled by ESP32 for dew point management
    │
    └── Power Strip (for PC components)
        ├── ATX PSU (1200W) → Motherboard, CPU, GPU, drives
        ├── D5 Pump (via SATA or Molex from PSU)
        ├── ESP32 + Sensors (5V USB from PSU)
        └── LED Strips (5V from PSU or separate supply)
```

**Two separate circuits recommended:**
- Freezer compressor on its own 15A circuit (with GFCI)
- PC + pump on a separate 15A circuit (with surge protector)

---

## Performance Projections

### Thermal Analysis

| Factor | Value |
|---|---|
| **CPU heat load** | 350W (TR PRO 9965WX) |
| **GPU heat load** | 300W (RTX 5080, if on loop) |
| **Total PC heat** | 350-650W |
| **Radiator removal** (Zone 3) | 30-50% → ~105-325W removed |
| **Remaining for chiller** | ~175-325W to Zone 1 |
| **Freezer cooling capacity** | ~200-400W (1/4-1/3 HP, typical 10 cu ft) |
| **Thermal balance?** | **Yes — freezer can handle it** |

### Expected Temperatures

| Scenario | Zone 1 Coolant | CPU Full Load | GPU Full Load |
|---|---|---|---|
| **CPU only on loop** | 0-5°C | 30-45°C | 65-80°C (air cooled) |
| **CPU + GPU on loop** | 5-10°C | 35-50°C | 40-55°C |
| **Aggressive (no radiator assist)** | -5-0°C | 25-40°C | 35-50°C |

Compare: standard 360mm AIO → CPU 70-85°C at full load.
**Coolputer delivers 30-50°C lower CPU temps.**

---

## Innovation Summary: What Makes This a "World's First"

| Innovation | Description |
|---|---|
| **5-Zone Thermal Architecture** | No one has designed multi-zone thermal isolation in a freezer case |
| **PSU Thermal Isolation** | PSU heat exhausted outside — every prior build had PSU fighting compressor |
| **Passive Reservoir Chilling** | Freezer air chills reservoir walls — no refrigerant loop modification needed |
| **Sealed Cold Chamber** | Motherboard in humidity-controlled sealed zone — eliminates condensation |
| **Integrated Dew Point Control** | ESP32 + sensors + relay = automated safety system |
| **EEB Threadripper PRO** | Largest consumer motherboard in a freezer — 128 PCIe 5.0 lanes chilled |
| **YouTube-Ready** | Designed for visual impact — acrylic window, RGB, OLED displays |
| **Upgradeable** | Start with 24-core, drop in 96-core later. Same case, same cooling. |

---

*Coolputer Design — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
