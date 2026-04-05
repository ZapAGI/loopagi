# DIY Sub-Ambient Cooling System — Implementation Guide

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**Target:** Threadripper PRO 9965WX (350W) + RTX 5080 (300W)

---

## Build Overview

This guide converts a **upcycled window AC unit** into a water chiller
that cools a reservoir to sub-ambient temperatures. A pump circulates
chilled coolant through a CPU water block, optional GPU block, and a
pre-entry radiator before returning to the reservoir.

**Total heat load:** ~650W (CPU 350W + GPU 300W)  
**Chiller capacity:** ~1500-2300W (5000-8000 BTU AC)  
**Target coolant temp:** 5-10°C daily, 0 to -10°C aggressive  
**Estimated build time:** 2-3 weekends  

---

## Phase 1: Acquire & Strip the AC Unit

### Step 1.1 — Source a Window AC

Look for a **5000-8000 BTU window AC unit**. Sources:
- Facebook Marketplace / Craigslist ($20-60 used)
- Walmart / Home Depot clearance ($80-120 new)
- Curbside / garage sales (free-$20)

**Requirements:**
- Working compressor (plug it in, should hum and vibrate)
- R-134a or R-410A refrigerant (labeled on unit)
- At least 5000 BTU cooling capacity

### Step 1.2 — Strip the Housing

1. **Unplug** the AC unit. Let it sit 24 hours.
2. Remove all screws holding the outer housing/shell.
3. Remove the front panel, filter, and grille.
4. Carefully expose the internal components:
   - **Compressor** (heavy black cylinder, bottom)
   - **Condenser coil** (rear, with fan — the HOT side)
   - **Evaporator coil** (front, the COLD side)
   - **Fan motor(s)**
   - **Capillary tube** (thin copper tube connecting condenser to evaporator)
5. **Do NOT cut any refrigerant lines yet.**
6. Label each component and take photos for reference.

### Step 1.3 — Separate the Components

You will keep:
- **Compressor** (the heart of the chiller)
- **Condenser coil + condenser fan** (heat rejection)
- **Capillary tube** (metering device)

You will **replace** the evaporator with your own **copper coil
submerged in the reservoir**.

**IMPORTANT:** The refrigerant lines must be properly handled. If you
cut into a charged system, refrigerant will escape. Options:
- **Best:** Have an HVAC tech recover the refrigerant before cutting ($50-100)
- **Budget:** If using R-290 (propane) to recharge, you can vent the
  small amount of original refrigerant outdoors (check local regulations)
- You will recharge the system after assembly

---

## Phase 2: Build the Copper Coil Evaporator

### Step 2.1 — Coil the Copper Tubing

**Materials:**
- 25 feet of 1/4" OD soft copper refrigeration tubing
- A cylindrical form (coffee can, 6" PVC pipe) to wrap around

**Process:**
1. Slowly and carefully wrap the copper tubing around the form
2. Create a coil ~6-8" diameter, ~8-10" tall
3. Leave 12-18" straight on each end for connections
4. Keep the coils tight but don't kink the tubing
5. Space coils ~1/4" apart for coolant flow between them

**Tip:** Fill the tubing with sand before bending to prevent kinking.
Flush the sand out afterward.

### Step 2.2 — Add Fittings

Braze (silver solder) the coil ends to match the compressor's
suction (low) and discharge (high) line diameters. Typically:
- Low side (suction): 3/8" to 1/4" reducer
- High side (from capillary): 1/4" direct connection

**Tools needed:** MAPP gas torch, silver brazing rod, flux.

---

## Phase 3: Build the Reservoir

### Step 3.1 — Select a Container

| Option | Pros | Cons |
|---|---|---|
| **5-gallon insulated cooler** | Pre-insulated, lid, cheap | Plastic, may not seal perfectly |
| **Stainless steel pot (20L)** | Durable, easy to drill | Needs external insulation |
| **Custom acrylic tank** | Looks amazing, precise | Expensive, needs fabrication |
| **Modified plastic tub + foam** | Cheapest, functional | Not pretty |

**Recommended:** A **stainless steel stock pot (20L)** with a custom
lid. Easy to drill for fittings, durable, and looks professional
when wrapped in neoprene.

### Step 3.2 — Install the Coil

1. Place the copper coil evaporator inside the reservoir
2. Route the copper tube ends through holes in the lid/wall
3. Seal penetrations with silicone sealant or compression fittings
4. The coil should be fully submerged when the reservoir is filled

### Step 3.3 — Install Coolant Fittings

Drill two holes in the reservoir wall (above the waterline or with
bulkhead fittings below):
- **OUTLET** (bottom): To pump → CPU block (coldest coolant)
- **INLET** (top): Return from radiator → reservoir (warmer coolant)

Use **G1/4" bulkhead fittings** (standard PC water cooling thread)
with O-ring seals.

### Step 3.4 — Insulate Everything

Wrap the entire reservoir in **6-12mm closed-cell neoprene foam**:
- Walls: Full wrap with adhesive neoprene sheet
- Lid: Neoprene sheet cut to size, sealed edges
- All tubing penetrations: Sealed with silicone + neoprene gaskets
- Bottom: Neoprene pad + rubber feet for vibration isolation

---

## Phase 4: Assemble the Refrigeration Loop

### Step 4.1 — Mount Components

Mount on a sturdy base (plywood, aluminum plate, or inside
a milk crate):

```
┌─────────────────────────────────┐
│          MOUNTING BASE          │
│                                 │
│  ┌────────────┐  ┌───────────┐ │
│  │ COMPRESSOR │  │ CONDENSER │ │
│  │            │──│ (+ FAN)   │ │
│  └──────┬─────┘  └───────────┘ │
│         │                       │
│    CAPILLARY TUBE               │
│         │                       │
│  ┌──────▼──────────────────┐   │
│  │    RESERVOIR            │   │
│  │  (copper coil inside)   │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

### Step 4.2 — Connect Refrigerant Lines

**Order of connections (from compressor output, following flow):**

1. **Compressor HIGH side** → Condenser inlet
2. **Condenser outlet** → Capillary tube inlet
3. **Capillary tube outlet** → Evaporator coil inlet (in reservoir)
4. **Evaporator coil outlet** → Compressor LOW side (suction)

**All joints brazed** with silver solder + flux + MAPP gas torch.

Add **Schrader access valves** at:
- Compressor suction line (for charging/monitoring low side pressure)
- Compressor discharge line (for monitoring high side pressure)

### Step 4.3 — Leak Test

1. **Nitrogen pressure test:** Pressurize the sealed system to 150 PSI
   with dry nitrogen. Wait 24 hours. Any pressure drop = leak.
2. **Soap bubble test:** Apply soapy water to all joints and look for
   bubbles.
3. Fix any leaks by re-brazing.

### Step 4.4 — Evacuate & Charge

1. **Vacuum pump:** Pull a deep vacuum (-29.9" Hg) for 30-60 minutes
   to remove moisture and air.
2. **Charge with refrigerant:**
   - R-134a: Safe, widely available, ~$8-15/can at auto parts store
   - R-290 (propane): Excellent performance, flammable, available online
3. **Charge amount:** Start with manufacturer's spec for your compressor
   size. Typically 8-16 oz for a small system. Add slowly while
   monitoring suction pressure (target 10-25 PSI for sub-ambient).

---

## Phase 5: Build the Water Cooling Loop

### Step 5.1 — Component Order (Flow Path)

```
RESERVOIR (cold) → PUMP → CPU BLOCK → GPU BLOCK → RADIATOR → RESERVOIR
```

### Step 5.2 — Install CPU Water Block

**Watercool Heatkiller IV PRO for Threadripper** (sTR5 compatible):
1. Apply thermal paste (thin layer, spread method for large IHS)
2. Mount block with sTR5 mounting hardware
3. Connect G1/4" fittings to inlet/outlet

### Step 5.3 — Install GPU Water Block (Optional)

If adding the RTX 5080 to the loop:
1. Remove stock cooler from GPU
2. Install full-cover water block
3. Connect in series after CPU block

### Step 5.4 — Install Pre-Entry Radiator

A **360mm or 420mm copper radiator** with fans, placed between
the GPU output and the reservoir return:
- Removes 30-50% of heat load before coolant returns to reservoir
- Reduces chiller workload significantly
- Acts as failsafe cooling if chiller is off/fails
- Mount fans in push configuration for best performance

### Step 5.5 — Tubing & Fittings

| Component | Spec |
|---|---|
| **Tubing** | 12/16mm (1/2" ID) soft tubing or EPDM |
| **Fittings** | G1/4" compression fittings (Barrow, Bitspower, EK) |
| **Insulation** | Closed-cell foam pipe insulation on ALL cold-side tubing |
| **Drain valve** | Ball valve at lowest point for maintenance |

**INSULATE ALL COLD TUBING.** Every inch of exposed cold tubing
will condensate. Use pipe insulation rated for sub-zero temps.

---

## Phase 6: Condensation Protection

This is the **most critical phase** of the entire build.

### Step 6.1 — CPU Block Insulation

1. Cut neoprene foam gasket to match block footprint
2. Apply around the entire block perimeter, sealing against motherboard
3. Cover the block top with neoprene (leave fittings exposed)
4. Seal all edges with silicone sealant or Kapton tape

### Step 6.2 — Motherboard Protection

1. Apply **conformal coating** (liquid electrical tape / MG Chemicals
   419D) to the motherboard area around the CPU socket
2. Cover a 2-3" radius around the socket — both front and back
3. Let cure 24 hours before assembly
4. Apply neoprene sheet to the backside of the motherboard behind CPU

### Step 6.3 — Tubing Insulation

1. Wrap ALL tubing from reservoir to CPU block in closed-cell foam
2. Wrap return tubing from CPU to radiator (still cold)
3. Seal all joints and seams with adhesive or tape
4. No exposed cold surfaces anywhere in the system

### Step 6.4 — Ambient Monitoring (Recommended)

For a daily-driver system, add a **DHT22 humidity/temperature sensor**
connected to an Arduino or ESP32:
- Monitor ambient temperature and humidity
- Calculate dew point in real-time
- If coolant temp approaches dew point → reduce chiller power or
  activate a bypass valve to warm the coolant
- Display on small OLED screen or send alerts to phone

---

## Phase 7: Fill, Test, and Commission

### Step 7.1 — Prepare Coolant

Mix in a clean container:
- **60% distilled water**
- **40% propylene glycol** (food-grade antifreeze)
- **Biocide:** Mayhems biocide drops or small silver coil
- **Corrosion inhibitor:** If mixing metals (add Mayhems XT-1 or similar)

This mix freezes at approximately **-21°C** — plenty of margin.

### Step 7.2 — Fill & Leak Test (No Power)

1. Fill reservoir with coolant mix
2. Run pump only (no chiller) and check for leaks at every fitting
3. Run for 24 hours, check for drips
4. Top up as air bleeds out

### Step 7.3 — Test Chiller (No PC)

1. Start the chiller compressor
2. Monitor reservoir temperature (digital thermometer or thermocouple)
3. Should begin dropping within 10-15 minutes
4. Target: 5-10°C for initial testing
5. Check condenser airflow — condenser should be warm, not hot
6. Monitor suction pressure if you have gauges

### Step 7.4 — First PC Boot

1. Start pump + chiller, wait for reservoir to reach target temp
2. Boot PC, enter BIOS
3. Monitor CPU temperature — should be dramatically lower than air cooling
4. Run stress test (Cinebench, Prime95) for 30 minutes
5. Monitor for ANY condensation — check block, tubing, fittings
6. If condensation appears, SHUT DOWN and add more insulation

---

## Maintenance Schedule

| Task | Frequency |
|---|---|
| Check coolant level | Weekly |
| Inspect tubing insulation for damage | Monthly |
| Check for condensation/moisture | Monthly |
| Test coolant pH and condition | Every 6 months |
| Flush and replace coolant | Annually |
| Clean condenser fins (dust) | Every 3 months |
| Check compressor oil level | Annually |
| Inspect brazing joints | Annually |

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Coolant not getting cold | Low refrigerant charge | Add refrigerant |
| Compressor running hot | Condenser blocked / fan dead | Clean fins, replace fan |
| Condensation on block | Insufficient insulation | Add neoprene layers |
| Coolant freezing in tubing | Too cold, flow stopped | Raise thermostat, add glycol |
| Pump cavitation (bubbles) | Air in loop / coolant too cold | Bleed air, raise temp slightly |
| Compressor won't start | Bad start relay / capacitor | Replace relay/cap ($5-15) |
| High suction pressure | Overcharged / restriction | Remove refrigerant / check lines |

---

## Performance Expectations

| Configuration | Idle CPU Temp | Full Load CPU Temp | Notes |
|---|---|---|---|
| Stock air cooler (Noctua) | 45-55°C | 85-95°C | Baseline |
| 360mm AIO | 35-45°C | 70-85°C | Standard watercooling |
| **This chiller (10°C coolant)** | **15-25°C** | **40-55°C** | **Sub-ambient daily** |
| **This chiller (0°C coolant)** | **5-15°C** | **30-45°C** | **Aggressive, insulation critical** |
| **This chiller (-10°C coolant)** | **0-10°C** | **20-35°C** | **Extreme, full condensation protection** |

At 40-55°C full load, the 9965WX will have massive thermal headroom
for sustained all-core boost at 5.4 GHz, something impossible with
standard cooling at 350W TDP.

---

*DIY Sub-Ambient Cooling Implementation — Copyright 2026 Alexandros Karales / ZapAGI.*
