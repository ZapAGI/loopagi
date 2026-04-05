# Coolputer Version A: Submersion Build

## Mineral Oil Immersion + Chest Freezer + Server Rack Cage

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**YouTube Channel:** Multiversity  
**Base Unit:** Frigidaire EFRF1013 10 cu ft Black ($413.10)  

---

## Concept

The motherboard, CPU, GPU, and RAM are **fully submerged in mineral oil**
inside the Frigidaire chest freezer. The freezer's compressor chills the
oil to sub-ambient temperatures (0-10°C). An external server rack cage
mounted on the side houses the PSU, I/O panel, and control system.

**No water blocks. No thermal paste interfaces. No fans.** The dielectric
fluid is the cooling medium for every component simultaneously.

---

## Why Submersion + Freezer Is Groundbreaking

1. **No condensation possible** — components are submerged, no air contact
2. **Uniform cooling** — every component cooled equally by the fluid
3. **No water blocks needed** — $300+ in blocks eliminated
4. **Dead silent** — no fans spinning in oil (remove them all)
5. **Freezer chills the oil** — sub-ambient temps with zero modification
   to the refrigerant system
6. **Visually stunning** — components visible through oil, RGB lighting
   refracts through the fluid

---

## System Architecture

```
┌──────────────────────────────────────────────────────┐
│              FRIGIDAIRE EFRF1013 (BLACK)              │
│              44"W × 25.4"D × 33.3"H                  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │                                                │  │
│  │          MINERAL OIL BATH (~30-35L)            │  │
│  │                                                │  │
│  │   ┌─────────────────────────────────────┐      │  │
│  │   │  MOTHERBOARD (vertical, submerged)  │      │  │
│  │   │  - ASUS WRX90E-SAGE SE (EEB)       │      │  │
│  │   │  - TR PRO 9965WX (no block needed)  │      │  │
│  │   │  - 8× DDR5 RDIMM (submerged)       │      │  │
│  │   │  - RTX 5080 (submerged, no fans)    │      │  │
│  │   │  - NVMe in M.2 slot (submerged)     │      │  │
│  │   └─────────────────────────────────────┘      │  │
│  │                                                │  │
│  │   Oil circulation pump (optional, low-flow)    │  │
│  │   Temperature probe (DS18B20, submerged)       │  │
│  │   RGB LED strip (waterproof, bottom)           │  │
│  │                                                │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  FREEZER WALLS: Polyurethane insulation + aluminum   │
│  COMPRESSOR: Chills the oil through wall conduction   │
│  EVAPORATOR COILS: Embedded in walls/floor            │
└──────────────────────────┬───────────────────────────┘
                           │
            Power cables + I/O cables pass through
            sealed grommet in side wall
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│           EXTERNAL SERVER RACK CAGE (8U)              │
│           Mounted on right side of freezer            │
│                                                      │
│  ┌─── 1U ───┐  I/O Panel (USB, HDMI, DP, Ethernet)  │
│  ┌─── 2U ───┐  ESP32 Controller + OLED Displays      │
│  ┌─── 2U ───┐  PSU (1200W, ATX, fan-exhausted)       │
│  ┌─── 1U ───┐  Fan Hub + Power Distribution           │
│  ┌─── 2U ───┐  Cable Management / Spare               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Build Phases

### Phase 1: Prepare the Freezer

1. **Unbox** the Frigidaire EFRF1013
2. **Remove** the wire storage basket (not needed)
3. **Test** the freezer — plug in, confirm it reaches -18°C in 4-6 hours
4. **Map the evaporator coils:**
   - Use a thermal camera (FLIR ONE) or run the freezer and feel the
     walls for cold spots
   - Coils are typically in the **bottom and lower walls**
   - Mark coil locations with tape — DO NOT drill/cut near them
5. **Plan the side wall pass-through hole:**
   - Choose a spot on the RIGHT side wall, UPPER half (away from coils)
   - This is where power cables and I/O cables exit to the server rack
   - Size: ~3" diameter hole

### Phase 2: Build the Motherboard Mounting Frame

The motherboard must be mounted **vertically** inside the freezer to
maximize oil contact on both sides and allow natural convection flow
(hot oil rises, cold oil sinks).

**Mounting frame materials:**
- 2020 aluminum extrusion (4× 20" verticals, 4× 14" horizontals)
- EEB motherboard tray or direct standoff mounting to extrusion
- Stainless steel hardware (won't corrode in oil)

```
VERTICAL MOUNT FRAME (inside freezer):

        ┌─────────────── 14" ───────────────┐
        │                                    │
   20"  │   ┌────────────────────────┐       │
        │   │                        │       │
        │   │    MOTHERBOARD         │       │
        │   │    (EEB 12" × 13")     │       │
        │   │                        │       │
        │   │    CPU (bare die/IHS)  │       │
        │   │    GPU (vertical,      │       │
        │   │         riser cable)   │       │
        │   │    8× RAM sticks       │       │
        │   │                        │       │
        │   └────────────────────────┘       │
        │                                    │
        └────────────────────────────────────┘
        (frame sits on freezer floor, legs raise
         board 2-3" above bottom for oil flow)
```

**GPU mounting:**
- Remove the stock cooler and fans entirely (plastic shroud, fans, all of it)
- Keep only the PCB + heatsink fins (if any)
- Mount vertically using a PCIe riser cable from the motherboard
- Or mount directly in PCIe slot if orientation allows

### Phase 3: Prepare Components for Submersion

**Before submerging, do these for each component:**

| Component | Preparation |
|---|---|
| **Motherboard** | Remove all plastic shrouds/covers. Leave heatsinks on VRMs (helps oil contact). Remove I/O shield (allows oil flow). |
| **CPU** | Install in socket normally. Apply thin thermal paste on IHS (oil is poor thermal conductor — paste on IHS helps). |
| **GPU** | Remove entire stock cooler (fans, shroud, backplate if plastic). Leave bare PCB. Thermal pads on memory/VRM optional. |
| **RAM** | Remove any clip-on heatsinks/RGB covers. Bare PCB is fine. |
| **NVMe** | Install in M.2 slot. Remove any heatsink — oil will cool it. |
| **24-pin / EPS cables** | Route out through side wall pass-through. Seal with silicone. |

### Phase 4: Fill with Mineral Oil

**Oil selection:**
- **White mineral oil, USP grade, light viscosity** (~15 cSt)
- Food-safe, odorless, non-toxic
- Available in bulk from Amazon or pharmacy suppliers

**Fill quantity:**
- Internal dims ~38"W × 19"D × 25"H
- Motherboard frame sits in lower ~18" of depth
- Fill to ~2-3" above the top of the tallest component
- Estimated **30-35 liters (8-9 US gallons)** of oil needed
- Leave 3-4" headroom for thermal expansion

**Fill process:**
1. Place the mounting frame with all components inside the freezer
2. Route all cables through the side wall pass-through
3. Slowly pour mineral oil along the side wall (not directly on components)
4. Fill until all components are submerged by 2-3"
5. Let it sit for 30 minutes — air bubbles will rise out
6. Top up as needed

### Phase 5: Install External Server Rack Cage

**Mount the 8U open-frame rack to the right side of the freezer:**

1. Position the rack vertically, flush with the freezer's right side
2. Use 4× L-brackets + bolts through the freezer's exterior steel shell
3. Add rubber vibration isolators between bracket and freezer
4. Install components in the rack:
   - **1U:** I/O panel (HDMI, DP, USB-A, USB-C, Ethernet pass-throughs)
   - **2U:** ESP32 + OLED displays + LED controller
   - **2U:** ATX PSU (fan facing outward for exhaust)
   - **1U:** Fan hub + power distribution (SATA/Molex splitters)
   - **2U:** Cable management + spare space

### Phase 6: Cable Routing & Sealing

All cables pass through a **single sealed grommet** in the side wall:

| Cable | Purpose | Routing |
|---|---|---|
| 24-pin ATX | Main power | Freezer → Rack (PSU) |
| 8-pin EPS (×2) | CPU power | Freezer → Rack (PSU) |
| 8-pin PCIe (×2) | GPU power | Freezer → Rack (PSU) |
| HDMI / DisplayPort | Video out | Freezer → Rack (I/O panel) → Monitor |
| USB 3.0 header | Front USB | Freezer → Rack (I/O panel) |
| Ethernet | Network | Freezer → Rack (I/O panel) |
| SATA power | NVMe (if needed) | Freezer → Rack (PSU) |
| DS18B20 probe wire | Temp sensor | Freezer → Rack (ESP32) |

**Sealing the pass-through:**
1. Drill 3" hole in side wall (above coil line)
2. Insert rubber grommet
3. Route all cables through
4. Pack remaining gaps with closed-cell foam
5. Seal exterior with silicone sealant
6. The oil level inside should be BELOW this hole

### Phase 7: Monitoring & Control

**ESP32 system (mounted in rack):**
- DS18B20 probe #1: Oil temperature (submerged)
- DS18B20 probe #2: Freezer air temp (above oil)
- DS18B20 probe #3: Rack ambient temp
- OLED display #1: Oil temp + CPU temp (read from motherboard sensor)
- OLED display #2: System status
- WS2812B LED strip: Submerged in oil at bottom (RGB glow through oil)
- Relay: Controls freezer compressor on/off for temp regulation

**Thermostat logic:**
```
TARGET_OIL_TEMP = 5°C  // Adjustable

if oil_temp < TARGET_OIL_TEMP - 2:
    freezer_compressor = OFF   // Oil cold enough
elif oil_temp > TARGET_OIL_TEMP + 2:
    freezer_compressor = ON    // Need more cooling
```

### Phase 8: Commission & Test

1. **Dry test** — Power on PSU in rack, verify all connections
2. **Cold test** — Run freezer for 4-6 hours, let oil chill to ~5°C
3. **First boot** — Power on PC, enter BIOS
4. **Monitor** — Watch oil temp, CPU temp, GPU temp
5. **Stress test** — Cinebench R24, 30 minutes, monitor all temps
6. **24-hour soak** — Run overnight, check for any issues

---

## Expected Performance

| Metric | Standard Air | Standard AIO | Coolputer Submersion |
|---|---|---|---|
| **Idle CPU** | 45-55°C | 35-45°C | **5-15°C** |
| **Full Load CPU** | 85-95°C | 70-85°C | **25-40°C** |
| **Idle GPU** | 35-45°C | 30-40°C | **5-15°C** |
| **Full Load GPU** | 75-85°C | 60-75°C | **25-40°C** |
| **RAM** | 50-80°C | 50-80°C | **5-15°C** |
| **NVMe** | 50-70°C | 50-70°C | **5-15°C** |
| **VRM** | 60-90°C | 60-90°C | **10-20°C** |
| **Noise** | 35-45 dBA | 30-40 dBA | **Near silent** (compressor hum only) |

---

## Parts List — Version A Submersion

| # | Item | Qty | Est. Price | Source |
|---|---|---|---|---|
| 1 | Frigidaire EFRF1013 10 cu ft Black Chest Freezer | 1 | **$413.10** | Home Depot Midtown Manhattan |
| 2 | White Mineral Oil USP (1 gallon × 9) | 9 gal | ~$20/gal = **$180** | [Amazon](https://www.amazon.com/s?k=white+mineral+oil+USP+1+gallon) |
| 3 | 2020 Aluminum Extrusion Kit (frame) | 1 | ~$30 | [Amazon](https://www.amazon.com/s?k=2020+aluminum+extrusion+kit) |
| 4 | EEB Motherboard Standoffs + Hardware (stainless) | 1 kit | ~$15 | Amazon |
| 5 | PCIe 5.0 Riser Cable 300mm | 1 | ~$40 | Amazon |
| 6 | NavePoint 9U Open Frame Rack | 1 | ~$70 | [Amazon](https://www.amazon.com/s?k=navepoint+9U+open+frame+rack) |
| 7 | L-Brackets + Bolts (rack mount to freezer) | 4 sets | ~$15 | Home Depot |
| 8 | Rubber Vibration Isolators | 4 | ~$8 | Amazon |
| 9 | Rubber Grommet (3" ID, bulkhead) | 1 | ~$5 | Amazon |
| 10 | Silicone Sealant + Closed-Cell Foam | 1 | ~$12 | Home Depot |
| 11 | USB/HDMI/DP/Ethernet Panel Mount Set | 1 | ~$25 | Amazon |
| 12 | ATX PSU Mounting Shelf (1U/2U rack) | 1 | ~$15 | Amazon |
| 13 | ESP32 Dev Board | 1 | ~$10 | Amazon |
| 14 | DS18B20 Waterproof Probes (5-pack) | 1 | ~$10 | Amazon |
| 15 | 0.96" OLED Displays (2-pack) | 1 | ~$10 | Amazon |
| 16 | WS2812B Waterproof LED Strip (1m, IP67) | 1 | ~$10 | Amazon |
| 17 | 5V Relay Module | 1 | ~$5 | Amazon |
| 18 | STC-1000 Thermostat (backup) | 1 | ~$12 | Amazon |
| 19 | Illuminated Power Button (22mm) | 1 | ~$8 | Amazon |
| 20 | Cable Extensions (24-pin, EPS, PCIe) | 1 set | ~$25 | Amazon |
| | **TOTAL (Version A cooling system)** | | **~$920** | |

### Grand Total with PC Components

| Component | Price |
|---|---|
| Coolputer Version A (above) | ~$920 |
| TR PRO 9965WX (24C/48T) | $2,699.99 |
| ASUS Pro WS WRX90E-SAGE SE | ~$1,099 |
| 256GB DDR5 ECC RDIMM (8×32GB) | ~$1,000 |
| 1200W PSU (80+ Platinum) | ~$250 |
| RTX 5080 (reuse) | — |
| 2TB NVMe (reuse) | — |
| **Grand Total** | **~$5,970** |

---

## Maintenance Schedule

| Task | Frequency |
|---|---|
| Check oil level (top up if evaporated/absorbed) | Monthly |
| Check oil clarity (replace if dark/particles) | Every 6 months |
| Full oil change | Every 12-18 months |
| Clean/replace oil filter (if installed) | Every 6 months |
| Check cable seal at pass-through | Monthly |
| Defrost freezer (manual) | Every 6-12 months |
| Replace desiccant (if used above oil) | Monthly |

---

## YouTube Episode Ideas for Version A

| Episode | Title | Hook |
|---|---|---|
| 1 | "I Submerged a $6,000 AI Computer in Oil Inside a Freezer" | The reveal, pouring oil over the Threadripper |
| 2 | "Will Mineral Oil Destroy My PC? (4-Year Puget Data)" | Research + reliability deep-dive |
| 3 | "Sub-Zero AI: Running LLMs at -5°C" | Benchmark results, thermal imaging |
| 4 | "The Server Rack Cage Mod" | Building and mounting the external rack |
| 5 | "6 Months Later: Did the Freezer PC Survive?" | Long-term follow-up |

---

*Coolputer Version A — Copyright 2026 Alexandros Karales / Multiversity / ZapAGI.*
