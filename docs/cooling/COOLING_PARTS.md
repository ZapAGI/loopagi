# DIY Sub-Ambient Cooling System — Parts List & Sourcing

**Author:** Alexandros Karales  
**Date:** 2026-03-19  
**Target:** Threadripper PRO 9965WX (350W) + RTX 5080 (300W)

---

## Parts Overview

The system has 7 subsystems. Each section lists parts with sourcing links
and estimated prices.

---

## 1. CPU Water Block (sTR5 Socket)

The Threadripper PRO uses the **sTR5 socket** (same physical as SP6/SP5).
Very few water blocks are compatible. The community consensus is clear:

| Block | Material | Price | Source | Status |
|---|---|---|---|---|
| **Watercool Heatkiller IV PRO for Threadripper** (Copper/Nickel) | Cu/Ni | ~$150 | [Watercool Direct](https://shop.watercool.de/HEATKILLER-IV-PRO-for-Threadripper-COPPER-NICKEL_1) / [Newegg](https://www.newegg.com/p/1YF-00CT-00069) / [Performance-PCs](https://www.performance-pcs.com/products/watercool-heatkiller-iv-pro-for-threadripper-copper-nickel-wc-18026) | **RECOMMENDED — In stock** |
| **Watercool Heatkiller IV PRO for Threadripper** (Pure Copper) | Cu | ~$140 | [Watercool Direct](https://shop.watercool.de/HEATKILLER-IV-PRO-for-Threadripper-PURE-COPPER_1) / [Performance-PCs](https://www.performance-pcs.com/products/watercool-heatkiller-iv-pro-for-threadripper-pure-copper-wc-18025) | In stock |
| **EK-Quantum Magnitude sTRX4** (Full Nickel) | Cu/Ni | ~$250 | [EKWB](https://www.ekwb.com/shop/ek-quantum-magnitude-strx4-full-nickel) | End of life — check stock |
| **EK-Pro CPU WB sTR** (Nickel/Acetal) | Cu/Ni | ~$200 | [EKWB](https://www.ekwb.com/shop/ek-pro-cpu-wb-str-nickel-acetal) | Server-grade |
| **Alphacool Eisblock XPX Aurora PRO** | Cu/Brass | ~$120 | [Alphacool](https://shop.alphacool.com/en/shop/cpu-water-cooling/intel/12950-alphacool-eisblock-xpx-aurora-pro-acryl-black-digital-rgb) | In stock |
| **Comino SP3/TR4 Block** | Cu | ~$100 | [Comino](https://www.comino.com/products/cpu-waterblock-for-socket-sp3-tr4-amd-epyc-ryzen-threadripper-ryzen-threadripper-pro) | Industrial grade |

**Best choice:** Heatkiller IV PRO (Copper/Nickel) — made in Germany,
best-reviewed TR block, full sTR5 IHS coverage, excellent flow.

---

## 2. Chiller Unit (Upcycled AC / Freezer)

### Option A: Upcycled Window AC (RECOMMENDED)

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **Window AC Unit 5000-8000 BTU** | R-134a or R-410A, working compressor | Facebook Marketplace / Craigslist / Garage sales | **$0-60 used** |
| **Window AC Unit 5000 BTU** (new, budget) | Generic brand | [Walmart](https://www.walmart.com/search?q=5000+btu+window+ac) / [Home Depot](https://www.homedepot.com/s/5000%20btu%20window%20ac) | ~$120-180 new |

### Option B: Upcycled Chest Freezer

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **Small Chest Freezer** (5-7 cu ft) | 1/4-1/2 HP compressor | Facebook Marketplace / Craigslist | **$0-40 used** |

### Option C: Standalone Compressor (New)

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **Embraco/Danfoss 1/4 HP Compressor** | R-134a, new | [Amazon](https://www.amazon.com/s?k=1%2F4+HP+refrigeration+compressor+R134a) / HVAC suppliers | ~$150-250 |

**Best value:** A used 5000-8000 BTU window AC for $20-60. The compressor
is already matched to a condenser and capillary tube — you just replace
the evaporator with your copper coil.

---

## 3. Copper Coil Evaporator (DIY)

| Item | Spec | Qty | Source | Est. Price |
|---|---|---|---|---|
| **1/4" OD Soft Copper Refrigeration Tubing** (25 ft coil) | Seamless, annealed | 1 | [Amazon](https://www.amazon.com/s?k=1%2F4+soft+copper+tubing+25+feet+refrigeration) / [Home Depot](https://www.homedepot.com/s/1%2F4%20soft%20copper%20tubing) | ~$25-40 |
| **1/4" Copper Tube Couplings** (for splicing) | Solder type | 4 | [Home Depot](https://www.homedepot.com/s/1%2F4%20copper%20coupling) | ~$3 |
| **3/8" to 1/4" Copper Reducer** (for suction line) | Solder type | 2 | [Home Depot](https://www.homedepot.com/s/3%2F8%20to%201%2F4%20copper%20reducer) | ~$3 |
| **Subtotal** | | | | **~$30-45** |

---

## 4. Reservoir & Coolant System

### Reservoir

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **Stainless Steel Stock Pot 20L** (with lid) | 18/10 stainless, ~12" diameter | [Amazon](https://www.amazon.com/s?k=20+liter+stainless+steel+stock+pot) | ~$30-50 |
| **G1/4" Bulkhead Fittings** (for tubing in/out) | Brass or nickel, with O-ring | [Amazon](https://www.amazon.com/s?k=G1%2F4+bulkhead+fitting+water+cooling) | ~$8-12 (pair) |
| **Silicone Sealant** (food-grade, for penetrations) | Clear, waterproof | [Amazon](https://www.amazon.com/s?k=food+grade+silicone+sealant+clear) / Home Depot | ~$6 |
| **Subtotal** | | | **~$45-70** |

### Coolant

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **Propylene Glycol** (food-grade, 1 gallon) | USP grade, non-toxic | [Amazon](https://www.amazon.com/s?k=propylene+glycol+food+grade+1+gallon) | ~$15-20 |
| **Distilled Water** (2 gallons) | Grocery store | Local store | ~$3 |
| **Mayhems Biocide Extreme** | Anti-algae/bacterial | [Amazon](https://www.amazon.com/s?k=mayhems+biocide+extreme) / [Performance-PCs](https://www.performance-pcs.com) | ~$8-12 |
| **Mayhems XT-1 Corrosion Inhibitor** (if mixing metals) | Prevents galvanic corrosion | [Amazon](https://www.amazon.com/s?k=mayhems+XT-1+corrosion+inhibitor) | ~$10-15 |
| **Subtotal** | | | **~$35-50** |

---

## 5. Water Cooling Loop Components

### Pump

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **EK-Quantum Kinetic D5** (pump/res combo) | D5 pump, 1500 L/h, PWM | [EKWB](https://www.ekwb.com/shop/pumps-reservoirs) / [Amazon](https://www.amazon.com/s?k=EK+D5+pump+reservoir) | ~$120-160 |
| **Barrow D5 Pump + Top** (budget) | D5 compatible, PWM | [Amazon](https://www.amazon.com/s?k=Barrow+D5+pump+water+cooling) | ~$60-80 |
| **Laing DDC 3.1** (compact alternative) | DDC pump, 600 L/h | [Amazon](https://www.amazon.com/s?k=DDC+3.1+pump+water+cooling) | ~$50-70 |

**Recommendation:** D5 pump for the flow rate needed in a chiller loop
with long tubing runs. The Barrow D5 is excellent value.

### Radiator (Pre-Entry Heat Dissipater)

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **Hardware Labs Black Ice Nemesis 360 GTS** | 360mm, copper/brass, 30mm thick | [Performance-PCs](https://www.performance-pcs.com) / [Amazon](https://www.amazon.com/s?k=hardware+labs+360+radiator) | ~$80-100 |
| **Alphacool NexXxoS ST30 360mm** | 360mm, copper, 30mm | [Alphacool](https://shop.alphacool.com) / [Amazon](https://www.amazon.com/s?k=alphacool+nexxxos+360+radiator) | ~$60-80 |
| **EK-Quantum Surface S360** | 360mm, copper | [EKWB](https://www.ekwb.com/shop/radiators) | ~$70-90 |

**IMPORTANT:** Use a **copper/brass radiator**, NOT aluminum. The CPU
block is copper/nickel — aluminum + copper in the same loop = galvanic
corrosion death.

### Fans (for Radiator + Condenser)

| Item | Spec | Qty | Source | Est. Price |
|---|---|---|---|---|
| **Noctua NF-A12x25 PWM** | 120mm, 2000 RPM, 60 CFM | 3 | [Amazon](https://www.amazon.com/s?k=noctua+NF-A12x25+PWM) | ~$30 ea / $90 total |
| **Arctic P12 PWM PST** (budget) | 120mm, 1800 RPM, value pack of 5 | 1 pack | [Amazon](https://www.amazon.com/s?k=arctic+P12+PWM+PST+value+pack+5) | ~$30 for 5 |

### Tubing & Fittings

| Item | Spec | Qty | Source | Est. Price |
|---|---|---|---|---|
| **EK-Tube ZMT 15.9/9.5mm** (soft tubing) | EPDM, black, 3m | 1 | [EKWB](https://www.ekwb.com/shop/ek-tube-zmt-15-9-9-5mm-matte-black-3m) / [Amazon](https://www.amazon.com/s?k=EK+ZMT+tubing) | ~$15-20 |
| **G1/4" Compression Fittings** (for 10/16mm tubing) | Barrow or Bitspower | 12 | [Amazon](https://www.amazon.com/s?k=Barrow+G1%2F4+compression+fitting+10+16mm) | ~$4-5 ea / $50-60 |
| **G1/4" 90° Rotary Fittings** (for tight bends) | Barrow or Bitspower | 4 | [Amazon](https://www.amazon.com/s?k=Barrow+G1%2F4+90+degree+rotary+fitting) | ~$6 ea / $24 |
| **G1/4" Ball Valve** (drain valve) | Barrow or Bitspower | 1 | [Amazon](https://www.amazon.com/s?k=G1%2F4+ball+valve+water+cooling) | ~$8-12 |
| **G1/4" Fill Port** (top of reservoir or T-fitting) | With plug | 1 | [Amazon](https://www.amazon.com/s?k=G1%2F4+fill+port+water+cooling) | ~$5-8 |
| **Subtotal (tubing + fittings)** | | | | **~$100-125** |

---

## 6. Insulation & Condensation Protection

| Item | Spec | Qty | Source | Est. Price |
|---|---|---|---|---|
| **Closed-Cell Neoprene Foam Sheet** (6mm, self-adhesive) | 12" × 48" sheets | 2 | [Amazon](https://www.amazon.com/s?k=neoprene+foam+sheet+6mm+self+adhesive) | ~$12-15 ea / $25-30 |
| **Pipe Insulation Foam** (1/2" ID, 3/8" wall) | 6-foot lengths | 4 | [Home Depot](https://www.homedepot.com/s/pipe%20insulation%20foam%201%2F2) / [Amazon](https://www.amazon.com/s?k=pipe+insulation+foam+1%2F2+inch) | ~$3-4 ea / $12-16 |
| **Conformal Coating** (MG Chemicals 419D or liquid electrical tape) | Spray can, 340ml | 1 | [Amazon](https://www.amazon.com/s?k=MG+Chemicals+419D+conformal+coating) | ~$15-20 |
| **Kapton Tape** (high-temp, for sealing neoprene edges) | 1" wide, 36 yards | 1 | [Amazon](https://www.amazon.com/s?k=kapton+tape+1+inch) | ~$8-10 |
| **Silicone Self-Fusing Tape** (waterproof seal) | 1" wide | 1 | [Amazon](https://www.amazon.com/s?k=silicone+self+fusing+tape) | ~$6-8 |
| **Subtotal** | | | | **~$65-85** |

---

## 7. Brazing & Refrigeration Tools

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **MAPP Gas Torch** (or propane, for brazing) | Bernzomatic TS8000 | [Home Depot](https://www.homedepot.com/s/bernzomatic+ts8000) / [Amazon](https://www.amazon.com/s?k=bernzomatic+TS8000+MAPP+torch) | ~$40-50 |
| **MAPP Gas Canister** | 16 oz | Home Depot | ~$12-15 |
| **Silver Brazing Rod** (15% silver, with flux core) | 1/16" dia, 6 sticks | [Amazon](https://www.amazon.com/s?k=silver+brazing+rod+15%25+1%2F16) / Home Depot | ~$15-25 |
| **Brazing Flux Paste** | Harris Stay-Silv or similar | [Amazon](https://www.amazon.com/s?k=brazing+flux+paste+harris) | ~$8-12 |
| **Schrader Access Valves** (1/4" solder-on) | For charging/monitoring | 2 | [Amazon](https://www.amazon.com/s?k=schrader+access+valve+1%2F4+solder) | ~$5-8 ea / $10-16 |
| **Copper Tube Cutter** (1/8" to 1-1/8") | Mini tube cutter | [Home Depot](https://www.homedepot.com/s/copper+tube+cutter) / [Amazon](https://www.amazon.com/s?k=mini+copper+tube+cutter) | ~$8-12 |
| **Copper Tube Bender** (1/4" spring type) | For coiling evaporator | [Amazon](https://www.amazon.com/s?k=copper+tube+bender+1%2F4+spring) | ~$6-10 |
| **Refrigerant R-134a** (12 oz can with gauge hose) | Automotive type | Auto parts store / [Amazon](https://www.amazon.com/s?k=R134a+refrigerant+can+gauge) | ~$15-25 |
| **Vacuum Pump** (optional — HVAC 2-stage) | 3 CFM minimum | [Amazon](https://www.amazon.com/s?k=HVAC+vacuum+pump+2+stage+3+CFM) / [Harbor Freight](https://www.harborfreight.com) | ~$80-120 (or rent) |
| **Refrigeration Gauge Set** (optional — for monitoring) | R-134a compatible | [Amazon](https://www.amazon.com/s?k=R134a+refrigeration+gauge+set) / Auto parts | ~$30-60 |
| **Subtotal** | | | | **~$100-250** (varies by tools owned) |

---

## 8. Monitoring & Control (Optional but Recommended)

| Item | Spec | Source | Est. Price |
|---|---|---|---|
| **DHT22 Temperature/Humidity Sensor** | Digital, ±0.5°C, ±2% RH | [Amazon](https://www.amazon.com/s?k=DHT22+temperature+humidity+sensor) | ~$5-8 |
| **DS18B20 Waterproof Temp Probe** (for coolant) | -55 to +125°C, stainless | [Amazon](https://www.amazon.com/s?k=DS18B20+waterproof+temperature+probe) | ~$5-8 (pack of 3) |
| **Arduino Nano** or **ESP32** | Microcontroller for monitoring | [Amazon](https://www.amazon.com/s?k=ESP32+dev+board) | ~$8-15 |
| **0.96" OLED Display** (I2C, 128×64) | For temp/humidity readout | [Amazon](https://www.amazon.com/s?k=0.96+OLED+display+I2C) | ~$5-8 |
| **Thermostat Controller** (STC-1000 or W1209) | 12V/110V, with probe | [Amazon](https://www.amazon.com/s?k=STC-1000+thermostat+controller) | ~$10-15 |
| **Subtotal** | | | | **~$35-55** |

The thermostat controller is **critical** — it turns the compressor
on/off to maintain target coolant temperature and prevents overcooling.

---

## Total Estimated Cost

| Category | Budget | Mid-Range | Premium |
|---|---|---|---|
| CPU Water Block | $120 (Alphacool) | **$150 (Heatkiller Cu/Ni)** | $250 (EK Magnitude) |
| Chiller Unit | **$0-60 (upcycled AC)** | $120 (new AC) | $250 (new compressor) |
| Copper Coil Evaporator | **$30** | $35 | $45 |
| Reservoir + Coolant | **$45** | $60 | $80 |
| Pump | $60 (DDC) | **$75 (Barrow D5)** | $150 (EK D5 combo) |
| Radiator | $60 (Alphacool) | **$80 (HWLabs)** | $100 (HWLabs) |
| Fans (3×120mm) | **$30 (Arctic P12)** | $60 | $90 (Noctua) |
| Tubing + Fittings | **$80** | $100 | $125 |
| Insulation | **$55** | $70 | $85 |
| Tools + Refrigerant | **$80** | $150 | $250 |
| Monitoring | $0 (skip) | **$35** | $55 |
| **TOTAL** | **~$560** | **~$935** | **~$1,480** |

### vs Commercial Alternatives

| Solution | Price | Temps Achievable |
|---|---|---|
| **This DIY chiller** | **$560-935** | **-10°C to +10°C coolant** |
| Standard 360mm AIO | $120-150 | 30-40°C coolant |
| Custom water loop (no chiller) | $400-700 | 25-35°C coolant |
| Commercial PC chiller (Koolance) | $500-800 | 10-20°C coolant |
| Commercial lab chiller (1/3 HP) | $800-2,000 | -20°C to +20°C coolant |

The DIY approach matches or beats a $2,000 lab chiller at a fraction
of the cost, with the added satisfaction of building it yourself.

---

## Quick-Buy Shopping List (Minimum Viable Chiller)

Order these to get started immediately:

| # | Item | Where | Price |
|---|---|---|---|
| 1 | Watercool Heatkiller IV PRO TR (Cu/Ni) | Newegg/Watercool | ~$150 |
| 2 | Used 5000+ BTU Window AC | Craigslist/FB Marketplace | ~$30 |
| 3 | 1/4" Soft Copper Tubing 25ft | Home Depot | ~$30 |
| 4 | 20L Stainless Steel Stock Pot | Amazon | ~$35 |
| 5 | Barrow D5 Pump + Top | Amazon | ~$75 |
| 6 | Alphacool NexXxoS 360mm Radiator | Amazon | ~$65 |
| 7 | Arctic P12 Fans (5-pack) | Amazon | ~$30 |
| 8 | EK-Tube ZMT 3m + Barrow Fittings (12) | Amazon | ~$75 |
| 9 | Neoprene Foam + Pipe Insulation | Amazon/Home Depot | ~$45 |
| 10 | Propylene Glycol 1gal + Distilled Water | Amazon/Local | ~$20 |
| 11 | MAPP Torch + Silver Brazing Rod + Flux | Home Depot | ~$65 |
| 12 | R-134a Can + Gauge Hose | Auto parts store | ~$20 |
| 13 | STC-1000 Thermostat Controller | Amazon | ~$12 |
| | **Quick-Buy Total** | | **~$650** |

---

## Sourcing Summary by Store

| Store | Items | Estimated Spend |
|---|---|---|
| **Amazon** | Pump, radiator, fans, fittings, tubing, insulation, sensors, coolant, glycol | ~$400 |
| **Home Depot** | Copper tubing, torch, brazing supplies, pipe insulation, sealant | ~$100 |
| **Newegg / Performance-PCs** | CPU water block, specialty fittings | ~$150 |
| **Craigslist / FB Marketplace** | Window AC unit (upcycled) | ~$30 |
| **Auto Parts Store** | R-134a refrigerant + charging hose | ~$20 |
| **Total** | | **~$700** |

---

## GPU Water Block (Optional Add-On)

If you want to add the RTX 5080 to the chiller loop later:

| Block | Price | Source |
|---|---|---|
| **EK-Quantum Vector² RTX 5080** | ~$150-200 | [EKWB](https://www.ekwb.com/shop/) |
| **Alphacool Eiswolf RTX 5080** | ~$120-160 | [Alphacool](https://shop.alphacool.com) |
| **Bykski RTX 5080 Full Cover** | ~$80-120 | [Amazon](https://www.amazon.com/s?k=Bykski+RTX+5080+water+block) |

Adding the GPU brings total heat load to ~650W — still well within
a 5000 BTU AC's capacity (1465W).

---

*DIY Sub-Ambient Cooling Parts List — Copyright 2026 Alexandros Karales / ZapAGI.*
