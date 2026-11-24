' optical_trng_08m2 firmware rev1 - RAW capture only (no extraction, no conditioning, no entropy claim)
' Target: PICAXE-08M2. Comparator output (LM393, TP5) on C.3 (pin 4, input only).
' Output: continuous raw bytes via sertxd (C.0 / pin 7, download socket; JP2 shunt on PROG, pins 1-2).
' Each byte = 8 consecutive samples of C.3, first sample = bit 7 (MSB).
' setfreq m32 -> sertxd baud is 38400, 8N1 (manual 2: 4800 at 4 MHz x8).
' Sample spacing is NOT uniform: sertxd blocks between bytes, so the gap between bit 0 of one
' byte and bit 7 of the next is longer than the gap between bits inside a byte. Analyse accordingly.
#picaxe 08m2
#no_data
setfreq m32
pause 100
main:
  b0 = 0
  for b1 = 1 to 8
    b0 = b0 + b0
    if pinC.3 = 1 then
      b0 = b0 + 1
    endif
  next b1
  sertxd(b0)
  goto main
