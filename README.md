# Optical-noise TRNG (PICAXE-08M2)

**Status: design only. Nothing has been built, measured or tested. The firmware has been compiled but never run on hardware, and the entropy of the output has not been assessed. Do not use it for anything that depends on real randomness.**

A hardware true-random-number generator that works from shot noise. An LED shines into the photodarlington of an FOD852 optocoupler. The small random current fluctuations are amplified about 1,000 to 5,000 times, turned into a 1/0 stream by a comparator, and read by a PICAXE-08M2 on pin C.3.

That randomness is a hypothesis until raw captures have been tested. A stream that looks random is not proof.

## Signal chain

```
9 V -> 2 x WS78L05:  +5V_OPT (LED and detector load only)   +5V (everything else)

+5V_OPT -> R1 -> FOD852 LED
+5V_OPT -> R2 -> FOD852 collector = DETECTOR (TP1)
   -> C1 100 nF -> MCP6022 A, x48 (TP3) -> C4 100 nF -> MCP6022 B, x22.9 / x48 / x101 (TP4)
   -> LM393 vs 2.5 V VREF, with hysteresis (TP5) -> PICAXE-08M2 C.3 (pin 4)
```

Two regulators keep the up-to-60 mA detector load and the PICAXE's switching from disturbing each other. The two 5 V rails are never joined. A 10k/10k divider makes the 2.5 V reference around which both op-amp stages and the comparator work.

## Plug-in resistor sockets

Four values can be changed without soldering. Each is one pair of single-pin female sockets, and you plug a resistor of the wanted value between them. An empty socket is always a safe state. (* = default)

| Ref | Position | Plug | Result | Empty socket |
|---|---|---|---|---|
| R1 | +5V_OPT to LED anode | 7.5k / **3.9k*** / 2.0k | 0.5 / 1.0 / 1.9 mA | LED off |
| R2 | +5V_OPT to detector collector | **68*** / 220 / 680 ohm (68 ohm: use 1/2 W) | collector load | no signal |
| R20 | across stage-B feedback, parallel with fixed R10 100k | **28.0k*** / 88.7k / none | stage B x22.9 / x48 / x101 | x101 |
| R13 | comparator output to + input | 1M / 330k / **100k*** | about 5 / 15 / 47 mV hysteresis | no hysteresis |

Total gain is 48 times stage B: about 1,100, 2,300 or 4,850.

The usable band is about 16 Hz (coupling capacitors) to roughly 100-200 kHz, depending on the gain.

The PICAXE download jack is a PJ-307 3.5 mm stereo jack. JP1 links the serial-in line. JP2 is a PROG/OUT changeover on C.0, in the style of the AXE021 board. J3 is an 8-pin breakout, where J3 pin n is PICAXE pin n.

*An earlier implementation of the same design used four jumper banks with fixed resistors instead of sockets, and four stripboards instead of three. The circuit is the same, and the sockets are the implementation that is documented here.*

## Repository layout

| Folder | Contents |
|---|---|
| `schematic/` | `optical_trng_v2.circuit` (the electrical truth, 24 nets), KiCad schematic, PDF, PNG, ERC report, exported netlist, and the Python that generates the schematic (`optical_trng_sch_v2.py`, `kisch.py`) |
| `fab/` | 3-board ElectroCookie stripboard layout (2 half boards of 30 columns and 1 mini board): pictures, `BUILD_GUIDE.txt` (hole-by-hole parts, wires and Dupont pins), wire-cutting templates (PDF, print at 100 %) and cut lists (CSV), `layout_check.txt`, and the generators |
| `firmware/` | `raw_capture_rev1.bas`: raw capture only, 8 samples of C.3 per byte, sent with `sertxd` at 38400 baud |
| `docs/NOTES.md` | open items and unverified assumptions |

## Verified so far

- The KiCad netlist matches the `.circuit` file: 24 of 24 nets.
- KiCad ERC: 0 errors. There are 46 warnings, all of the "symbol differs from library copy" kind.
- The stripboard layout was rebuilt into nets by `fab/fab_layout.py` and compared with the circuit: 24 of 24 nets match, no extra connections, and every hole is used once.
- The firmware passes the PICAXE compiler's syntax check (`picaxe08m2 -s`). It has not been downloaded to a chip.

## Regenerating files

```
cd fab && python3 fab_layout.py                  # layout, pictures, BUILD_GUIDE, layout_check (exit 1 on a netlist mismatch)
cd fab && python3 wire_templates.py B1           # also B2, B3; needs matplotlib
cd schematic && python3 optical_trng_sch_v2.py   # writes the .kicad_sch files; ERC, netlist and PDF then come from kicad-cli
picaxe08m2 -s firmware/raw_capture_rev1.bas      # syntax check only
```

## Bring-up (when it is built)

1. Power up from 9 V with the default plugs. Check both regulator outputs read about 5 V, then check TP2 reads about 2.5 V.
2. Measure TP1 with a meter. About 2-3 V is good. Near 1 V it is saturated, so lower the LED current (R1) or the load (R2). Near 4-5 V there is very little current, so raise the LED current. The FOD852's current-transfer ratio varies widely from part to part.
3. With an AC-coupled scope, look at TP3 and TP4. You should see noise centred on 2.5 V and not clipping.
4. Choose R20 so the TP4 noise is several times the hysteresis without clipping.
5. Choose R13 as the smallest hysteresis that gives a clean TP5 output without chatter.
6. Capture raw bytes from the PICAXE and analyse them offline before trusting anything.

## Cautions

- A rough estimate suggests about 40 uV rms of noise at TP1. It uses an assumed photodarlington gain and bandwidth and could be off by a large factor. Trust the scope, not the estimate.
- Op-amp and comparator offsets can bias the 1/0 balance. Correlation, drift and interference (mains hum, PICAXE switching) must be checked on raw data. Firmware conditioning such as von Neumann only removes simple bias, and only if the bits are independent.
- Plugged resistors add contact resistance and noise in the high-impedance gain and hysteresis nodes. This has not been measured.
- A 9 V battery sags as it discharges, and the more heavily loaded regulator (+5V_OPT) drops out first.

No license has been chosen yet. Until one is added, all rights are reserved.
