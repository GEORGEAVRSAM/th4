# TH-4 v1.2 — 4-bit μικροελεγκτής

Αυτό το αρχείο το διαβάζει αυτόματα το Claude στην αρχή κάθε συζήτησης.
Περιέχει ό,τι χρειάζεται για να συνεχίσουμε χωρίς να ξαναεξηγούμε.
**Όταν αλλάζει κάτι σημαντικό στο project, ενημέρωσε και αυτό το αρχείο.**

## Ο χρήστης και πώς δουλεύουμε

- Ηλεκτρονικός με εμπειρία σε AVR (C και assembly), Proteus, Eagle, LTspice.
  Μαθαίνει σχεδίαση chip από το μηδέν.
- **Πάντα στα ελληνικά.** Εξηγήσεις **βήμα-βήμα, ένα βήμα τη φορά**, με παραδείγματα
  από τον AVR και τα ηλεκτρονικά (74HC157, CD4511, PORTB, DDR κ.λπ.).
- Μετά από κάθε βήμα περίμενε screenshot πριν δώσεις το επόμενο.
- Του αρέσει να γράφει ο ίδιος κομμάτια κώδικα με υποδείξεις. Μην δίνεις αμέσως τη λύση
  σε άσκηση: δώσε υπόδειξη.
- Είναι προσεκτικός με την ασφάλεια. Ό,τι γίνεται στον λογαριασμό GitHub (GEORGEAVRSAM)
  το κάνει ο ίδιος, με το χέρι, αφού του εξηγήσεις.
- Πριν από αλλαγή στον σχεδιασμό ή σε όνομα, ρώτα πρώτα.

## Ονόματα και εκδόσεις

| Τι | Όνομα |
|---|---|
| Οικογένεια | **TH-4** (4 bit) |
| Έκδοση σχεδίασης | **v1.0, v1.1, v1.2 …**· τώρα **v1.2** |
| Μεγάλη αλλαγή | **v2.0** |
| Πρώτο κατασκευασμένο chip | **TH-4A** (μετά TH-4B …) |
| Μελλοντικός 8-bit | **TH-8** |

Τα ονόματα των αρχείων και των modules **δεν** αλλάζουν με την έκδοση.
Η έκδοση γράφεται μέσα στα αρχεία, στο datasheet και εδώ.

## Περιβάλλον του χρήστη (Windows)

- Τερματικό: **MSYS2 UCRT64** (όχι Git Bash). Φάκελος εργασίας: `C:\TH4` → `cd /c/TH4`
- OSS CAD Suite στο `C:\oss-cad-suite-windows-x64-20261107\oss-cad-suite`, μπαίνει
  στο PATH από το `~/.bashrc`. Στο `~/.bashrc` υπάρχουν και δικές του συναρτήσεις AVR
  (`lockhex`, `lockall`): μην τις πειράξεις.
- Εργαλεία: iverilog/vvp 14, gtkwave, yosys 0.70, python3, notepad.
- Παλιότερα projects: `C:\chip` (μετρητής 0–9, 7-segment), `C:\chip2` (00–99, multiplexing).

## Το repository (github.com/GEORGEAVRSAM/th4, Public)

    CLAUDE.md                 αυτό το αρχείο
    info.yaml  src/  test/  docs/   αρχεία του Tiny Tapeout (από ttsky-verilog-template)
    work/                     ο φάκελος εργασίας του TH-4 (τα αρχεία παρακάτω)

Στον υπολογιστή του χρήστη, τα αρχεία του `work/` είναι στο `C:\TH4`.

## Αρχεία (στο work/)

| Αρχείο | Τι είναι |
|---|---|
| `tt_um_th4.v` | **ο TH-4 σε Verilog — η κύρια πηγή** |
| `th4asm.py` | assembler: `python3 th4asm.py X.asm > prog.hex` |
| `run.v` | τρέχει το `prog.hex`: `vvp run +cycles=500 +in=5` |
| `tb.v`, `selftest.asm`, `selftest.hex` | αυτοέλεγχος όλων των εντολών και του timer |
| `th4_disasm.vh` | βοηθητικό για το ίχνος εκτέλεσης (`include` στο tb.v και run.v) |
| `prog.asm`, `timer.asm`, `fos.asm` | παραδείγματα (το `fos.asm` το έγραψε ο χρήστης) |
| `TH4_datasheet_GR.pdf`, `TH4_datasheet_EN.pdf` | το datasheet, έκδοση 1.2 |
| `TH4_ektelesi.pdf`, `TH4_metritis.pdf` | ίχνη εκτέλεσης με εξηγήσεις |
| `tools/docs/` | τα scripts που φτιάχνουν τα PDF (οι διαδρομές μέσα τους θέλουν προσαρμογή) |
| `../src/project.v` | ο TH-4 για το Tiny Tapeout (αντίγραφο, δες παρακάτω) |

Το `src/project.v` είναι **αντίγραφο** του `work/tt_um_th4.v` με άλλο όνομα module.
Μετά από κάθε αλλαγή στο `work/tt_um_th4.v`, από τη ρίζα του repository:

    sed 's/^module tt_um_th4 (/module tt_um_georgeavrsam_th4 (/' work/tt_um_th4.v > src/project.v

Το test του Tiny Tapeout: `cd test && make` (θέλει `pip install -r requirements.txt`).

## Εντολές (μέσα στο work/)

    iverilog -g2012 -o sim tb.v tt_um_th4.v      # αυτοέλεγχος
    vvp sim                                      # → ALL TESTS PASSED, 2054 παλμοί
    iverilog -g2012 -o run run.v tt_um_th4.v     # προσομοίωση προγράμματος
    python3 th4asm.py timer.asm > prog.hex
    vvp run +cycles=300 | grep "OUT  "
    yosys -p "read_verilog tt_um_th4.v; synth -top tt_um_th4; stat" | tail -22

## TH-4 v1.2 — προδιαγραφή

- Αρχιτεκτονική Harvard. Δεδομένα 4 bit, εντολή 8 bit: `[7:4]` opcode, `[3:0]` n.
- Καταχωρητές: **A**, **B** (4 bit), **Z** (flag), **PC** (8 bit).
- **RAM** 16 × 4 bit μέσα στο chip. Δεν μηδενίζεται στο reset.
- **Μνήμη προγράμματος** εξωτερική, 256 bytes: PC → `uo_out[7:0]`, εντολή ← `ui_in[7:0]`.
- **Θύρες:** είσοδος `port_in` = `uio[3:0]`, έξοδος `port_out` = `uio[7:4]` (latched).
  `uio_oe = 8'b1111_0000`.
- **Timer** 25 bit. Τρέχει **μόνο** μέσα στο `WAIT`, ξεκινά από 0 (οικονομία ρεύματος).
- Μονάδα ελέγχου: καταστάσεις `S_FETCH`, `S_ADDR`, `S_WAIT`.
- Reset `rst_n`: ενεργό στο 0, σύγχρονο. PC=A=B=Z=0, έξοδος 0000, timer 0.

| Hex | Εντολή | Λειτουργία | Κύκλοι | Z |
|---|---|---|---|---|
| `0n` | LOAD n | A ← n | 1 | ✔ |
| `1n` | ADD n | A ← A + n | 1 | ✔ |
| `2n` | SUB n | A ← A − n | 1 | ✔ |
| `3n` | AND n | A ← A AND n | 1 | ✔ |
| `40` | IN | A ← port_in | 1 | ✔ |
| `50` | OUT | port_out ← A | 1 | |
| `60 aa` | JUMP aa | PC ← aa | 2 | |
| `70 aa` | JZ aa | αν Z=1: PC ← aa | 2 | |
| `8n` | STORE n | RAM[n] ← A | 1 | |
| `9n` | LOADM n | A ← RAM[n] | 1 | ✔ |
| `An` | LDB n | B ← n | 1 | |
| `B0` | DECB | B ← B − 1 | 1 | ✔ (από τον B) |
| `C0 aa` | JNZ aa | αν Z=0: PC ← aa | 2 | |
| `Dn` | ADDM n | A ← A + RAM[n] | 1 | ✔ |
| `En` | SUBM n | A ← A − RAM[n] | 1 | ✔ |
| `F0` | TAB | B ← A | 1 | |
| `Fn` | WAIT n (n=1..15) | περίμενε | 2^(n+9)+2 | |

Assembler: ετικέτες `loop:`, ονόματα θέσεων RAM `temp = 0` ή `.equ temp = 0`, `ORG 0x40`.
Μια ετικέτα (`temp:`) **δεν** είναι θέση RAM: η μνήμη προγράμματος δεν γράφεται από το πρόγραμμα.

## Μέγεθος (Yosys 0.33 + sky130_fd_sc_hd, πριν την τοποθέτηση)

- 561 κελιά, ~5.530 µm² (~30% ενός tile των ~18.000 µm²) → αναμένεται 1 tile.
- Flip-flops: RAM 64, timer 25, PC 8, A 4, B 4, port_out 4, jop 4, state 3 (one-hot), Z 1 = **117**.

## Αποφάσεις

- Πρώτα 4-bit· ο 8-bit θα είναι το TH-8.
- Εξωτερική μνήμη προγράμματος (σαν Intel 4004): EEPROM (28C16/28C64) ή AVR που κάνει τη ROM.
- Ονόματα `port_out` / `port_in` (όχι leds / buttons).
- **ΟΧΙ** στο wafer.space Run 3 (προθεσμία GDS 16/12/2026, πολύ ρίσκο).
  Επόμενο run, στην τιμή early bird. Τέταρτο slot: 1,94 × 2,53 mm, 48 I/O, 2.000–3.000 $
  για 1.000 chips, +1.500 $ chip-on-board. Ο χρήστης θέλει τελικά chip με πόδια (QFN/TQFP ή module).
- Δρόμος: προσομοίωση ✅ → layout στο Tiny Tapeout → FPGA → κατασκευή.

## Κανόνες για αλλαγές στο chip

1. Μετά από κάθε αλλαγή στο `tt_um_th4.v`: τρέξε τον αυτοέλεγχο (`vvp sim`).
2. Για νέα λειτουργία: πρόσθεσε έλεγχο στο `selftest.asm` / `tb.v`, και έλεγξε ότι
   ο αυτοέλεγχος **αποτυγχάνει** αν χαλάσεις επίτηδες τη νέα λειτουργία.
3. Ενημέρωσε `src/project.v`, `test/test.py` και `test/tb.v` (αναμενόμενες τιμές, πρόγραμμα),
   το datasheet, και αυτό το αρχείο. Ανέβασε την έκδοση (v1.3 …).

## Επόμενα βήματα

1. **Tiny Tapeout:** το repository υπάρχει ήδη με τα αρχεία. top_module `tt_um_georgeavrsam_th4`.
   Ενεργοποίηση Pages (Settings → Pages → Source: GitHub Actions), έλεγχος ότι τρέχουν
   οι Actions (test, gds, docs). Δούμε το 3D layout και πόσα tiles πιάνει στην πράξη.
2. Προγράμματα με `IN` (κουμπιά), π.χ. κλειδαριά με κωδικό.
3. FPGA (π.χ. Tang Nano 9K) με αληθινά LED και AVR ως μνήμη.
4. Ιδέες για v2.0: SPI flash, περισσότερη RAM, carry flag, `jop` 2 bit αντί 4,
   αργό ρολόι για τον timer και sleep, clock gating.
