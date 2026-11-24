# Open items and unverified assumptions

Nothing here has been built or measured.

## Parts and pinouts
- No datasheets for the FOD852, MCP6022 or LM393 were available when the schematic was drawn. Their pinouts are unverified. The schematic uses a PC817 symbol for the FOD852, and the equivalence is unverified.
- The FOD852 may saturate at the 68 ohm collector load. VREF is unbuffered. The MCP6022 output swing and input range at 5 V are unchecked.
- No physical socket part has been chosen. The intent is single-pin machined or female header pins that grip a 0.6 mm lead, with the four sockets 0.3 in apart across the stripboard centre channel (rows F and E). Resistor leads can be bent up to lift a 1/2 W body (R2, 68 ohm) above the gap.
- Jack pin map (PJ-307: pin 1 sleeve, pins 2+3 ring, pins 4+5 tip) is inferred from the drawing and must be meter-checked. The two outer locating posts have no holes and must be clipped. The AXE021 H1 centre pin = leg 7 is inferred from the manual's wording.

## Stripboard
- Board 2 needs the T+ rail cut between columns 17 and 18 (columns 1-17 are VREF, columns 18-30 are +5V).
- Board thickness (1.6 mm assumed) and hole diameter (about 1.0 mm assumed) are unmeasured. The wire-template constants LEG 4.0 mm, BEND 1.0 mm and insulation OD 1.6 mm are assumptions (22 AWG solid wire).
- Wire colours: black GND, red +5V, yellow +5V_OPT, green VREF, white VIN_9V, blue signals.

## Firmware
- `raw_capture_rev1.bas` is raw capture only: no extraction, no conditioning, no entropy claim. Sample spacing is not uniform, because `sertxd` blocks between bytes, so the gap between bit 0 of one byte and bit 7 of the next is longer than the gap inside a byte.
- It has not been downloaded to a chip. It needs an AXE027 cable, with JP1 and JP2 (PROG) closed.

## Analysis (not started)
- Offline analysis of a raw capture: bias, autocorrelation, health tests. No entropy claims until then.
