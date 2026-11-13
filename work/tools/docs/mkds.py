import sys, html
lang = sys.argv[1]
def L(el, en): return el if lang == "el" else en
e = html.escape
M = lambda s: f"<span class='m'>{s}</span>"

# ---------------- instruction set data ----------------
# (hex, mnemonic, operation_el, operation_en, bytes, cycles, Z, desc_el, desc_en)
INS = [
 ("0n","LOAD n","A ← n","A ← n",1,"1","✔","Φορτώνει τον σταθερό αριθμό n στον A.","Loads the constant n into A."),
 ("1n","ADD n","A ← A + n","A ← A + n",1,"1","✔","Προσθέτει το n στον A. Το αποτέλεσμα κρατάει 4 bits (15 + 1 = 0).","Adds n to A. The result is kept to 4 bits (15 + 1 = 0)."),
 ("2n","SUB n","A ← A − n","A ← A − n",1,"1","✔","Αφαιρεί το n από τον A. Το αποτέλεσμα κρατάει 4 bits (0 − 1 = 15).","Subtracts n from A. The result is kept to 4 bits (0 − 1 = 15)."),
 ("3n","AND n","A ← A AND n","A ← A AND n",1,"1","✔","Λογικό AND, bit προς bit. Χρήσιμο για «μάσκα».","Bitwise AND. Useful as a mask."),
 ("40","IN","A ← IN[3:0]","A ← IN[3:0]",1,"1","✔","Διαβάζει τη θύρα εισόδου στον A.","Reads the input port into A."),
 ("50","OUT","OUT[3:0] ← A","OUT[3:0] ← A",1,"1","—","Γράφει τον A στον καταχωρητή της θύρας εξόδου. Η τιμή μένει μέχρι το επόμενο OUT.","Writes A to the output port register. The value is held until the next OUT."),
 ("60 aa","JUMP aa","PC ← aa","PC ← aa",2,"2","—","Άλμα χωρίς συνθήκη στη διεύθυνση aa.","Unconditional jump to address aa."),
 ("70 aa","JZ aa","αν Z = 1: PC ← aa","if Z = 1: PC ← aa",2,"2","—","Άλμα αν το τελευταίο αποτέλεσμα ήταν 0.","Jumps if the last result was 0."),
 ("8n","STORE n","RAM[n] ← A","RAM[n] ← A",1,"1","—","Γράφει τον A στη θέση n της RAM.","Writes A to RAM location n."),
 ("9n","LOADM n","A ← RAM[n]","A ← RAM[n]",1,"1","✔","Φορτώνει τη θέση n της RAM στον A.","Loads RAM location n into A."),
 ("An","LDB n","B ← n","B ← n",1,"1","—","Φορτώνει το n στον B.","Loads n into B."),
 ("B0","DECB","B ← B − 1","B ← B − 1",1,"1","✔","Μειώνει τον B κατά 1. Το Z γίνεται 1 όταν ο B φτάσει στο 0.","Decrements B. Z is set when B reaches 0."),
 ("C0 aa","JNZ aa","αν Z = 0: PC ← aa","if Z = 0: PC ← aa",2,"2","—","Άλμα αν το τελευταίο αποτέλεσμα δεν ήταν 0. Με το DECB φτιάχνει βρόχους.","Jumps if the last result was not 0. Used with DECB for loops."),
 ("Dn","ADDM n","A ← A + RAM[n]","A ← A + RAM[n]",1,"1","✔","Προσθέτει τη θέση n της RAM στον A.","Adds RAM location n to A."),
 ("En","SUBM n","A ← A − RAM[n]","A ← A − RAM[n]",1,"1","✔","Αφαιρεί τη θέση n της RAM από τον A. Αν είναι ίσα, Z = 1.","Subtracts RAM location n from A. Z = 1 if they are equal."),
 ("F0","TAB","B ← A","B ← A",1,"1","—","Αντιγράφει τον A στον B.","Copies A to B."),
 ("Fn","WAIT n","περίμενε 2<sup>n+9</sup> παλμούς","wait 2<sup>n+9</sup> cycles",1,"2<sup>n+9</sup> + 2","—","n = 1…15. Μηδενίζει τον timer και σταματάει το πρόγραμμα μέχρι να μετρήσει 2<sup>n+9</sup> παλμούς.","n = 1…15. Clears the timer and halts the program until it has counted 2<sup>n+9</sup> cycles."),
]

def pin_rows():
    rows = []
    for i in range(8):
        rows.append((f"uo_out[{i}]", f"ADDR{i}", L("Έξοδος","Output"), L(f"Διεύθυνση μνήμης προγράμματος, bit {i} (PC{i})", f"Program memory address, bit {i} (PC{i})")))
    for i in range(8):
        rows.append((f"ui_in[{i}]", f"INSTR{i}", L("Είσοδος","Input"), L(f"Byte εντολής από τη μνήμη προγράμματος, bit {i}", f"Instruction byte from program memory, bit {i}")))
    for i in range(4):
        rows.append((f"uio[{i}]", f"IN{i}", L("Είσοδος","Input"), L(f"Θύρα εισόδου, bit {i}", f"Input port, bit {i}")))
    for i in range(4):
        rows.append((f"uio[{i+4}]", f"OUT{i}", L("Έξοδος","Output"), L(f"Θύρα εξόδου, bit {i}", f"Output port, bit {i}")))
    rows.append(("clk","CLK",L("Είσοδος","Input"),L("Ρολόι. Όλα αλλάζουν στη θετική ακμή.","Clock. All state changes on the rising edge.")))
    rows.append(("rst_n","RST_N",L("Είσοδος","Input"),L("Reset, ενεργό στο 0, σύγχρονο με το ρολόι","Reset, active low, synchronous to the clock")))
    rows.append(("ena","—",L("Είσοδος","Input"),L("Δεν χρησιμοποιείται","Not used")))
    return rows

block_svg = """
<svg viewBox="0 0 720 330" class="fig" role="img">
 <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2f5d7c"/></marker></defs>
 <rect x="150" y="10" width="560" height="310" rx="6" fill="#f3f6f8" stroke="#2f5d7c" stroke-width="1.5"/>
 <text x="430" y="30" class="t2">TH-4</text>
 <g class="bx">
  <rect x="170" y="45" width="110" height="44"/><text x="225" y="72">PC (8)</text>
  <rect x="320" y="45" width="170" height="44"/><text x="405" y="64">%DEC%</text><text x="405" y="80" class="sm">%SM%</text>
  <rect x="320" y="125" width="170" height="54"/><text x="405" y="150">ALU</text><text x="405" y="166" class="sm">+ − AND</text>
  <rect x="530" y="45" width="80" height="34"/><text x="570" y="67">A (4)</text>
  <rect x="530" y="90" width="80" height="34"/><text x="570" y="112">B (4)</text>
  <rect x="530" y="135" width="80" height="34"/><text x="570" y="157">Z</text>
  <rect x="320" y="215" width="170" height="50"/><text x="405" y="236">RAM</text><text x="405" y="252" class="sm">16 × 4 bit</text>
  <rect x="170" y="215" width="110" height="50"/><text x="225" y="236">TIMER</text><text x="225" y="252" class="sm">25 bit</text>
  <rect x="530" y="215" width="90" height="50"/><text x="575" y="236">PORT</text><text x="575" y="252" class="sm">OUT (4)</text>
  <rect x="530" y="275" width="90" height="34"/><text x="575" y="297">PORT IN</text>
 </g>
 <g class="ln">
  <line x1="170" y1="67" x2="20" y2="67" marker-end="url(#ar)"/>
  <path d="M20,105 H350 V91" fill="none" marker-end="url(#ar)"/>
  <line x1="318" y1="67" x2="282" y2="67" marker-end="url(#ar)"/>
  <line x1="405" y1="89" x2="405" y2="123" marker-end="url(#ar)"/>
  <path d="M490,145 H510 M510,62 V152" fill="none"/>
  <line x1="510" y1="62" x2="528" y2="62" marker-end="url(#ar)"/>
  <line x1="510" y1="107" x2="528" y2="107" marker-end="url(#ar)"/>
  <line x1="510" y1="152" x2="528" y2="152" marker-end="url(#ar)"/>
  <line x1="405" y1="181" x2="405" y2="213" marker-end="url(#ar)" marker-start="url(#ar)"/>
  <path d="M610,62 H640 V213" fill="none" marker-end="url(#ar)"/>
  <line x1="620" y1="240" x2="700" y2="240" marker-end="url(#ar)"/>
  <line x1="700" y1="292" x2="622" y2="292" marker-end="url(#ar)"/>
  <path d="M530,292 H470 V181" fill="none" marker-end="url(#ar)"/>
  <path d="M280,240 H300 V80 H318" fill="none" marker-end="url(#ar)" stroke-dasharray="4 3"/>
 </g>
 <text x="12" y="58" class="sm l">uo_out[7:0]</text><text x="12" y="120" class="sm l">ui_in[7:0]</text>
 <text x="12" y="134" class="sm l">%PMEM%</text>
 <text x="655" y="232" class="sm l">uio[7:4]</text><text x="640" y="306" class="sm l">uio[3:0]</text>
</svg>""".replace("%DEC%", L("Αποκωδικοποίηση","Decoder")).replace("%SM%", L("+ μονάδα ελέγχου","+ control unit")).replace("%PMEM%", L("προς/από μνήμη προγρ.","to/from program memory"))

timing_svg = """
<svg viewBox="0 0 700 170" class="fig" role="img">
 <g class="wv">
 <text x="5" y="35" class="sm l">clk</text>
 <path d="M80,45 h40 v-25 h40 v25 h40 v-25 h40 v25 h40 v-25 h40 v25 h40 v-25 h40 v25 h40 v-25 h40 v25 h40"/>
 <text x="5" y="85" class="sm l">uo_out (PC)</text>
 <path d="M80,72 h45 l5,8 l-5,8 h-45 M80,88 h45"/><path d="M130,80 l5,-8 h150 l5,8 l-5,8 h-150 z"/><path d="M290,80 l5,-8 h150 l5,8 l-5,8 h-150 z"/><path d="M450,80 l5,-8 h150 l5,8 l-5,8 h-150 z"/>
 <text x="210" y="84" class="sm">n</text><text x="370" y="84" class="sm">n+1</text><text x="530" y="84" class="sm">n+2</text>
 <text x="5" y="125" class="sm l">ui_in (%INS%)</text>
 <path d="M150,120 l5,-8 h120 l5,8 l-5,8 h-120 z"/><path d="M310,120 l5,-8 h120 l5,8 l-5,8 h-120 z"/><path d="M470,120 l5,-8 h120 l5,8 l-5,8 h-120 z"/>
 <path d="M130,120 h20 M285,120 h25 M445,120 h25" stroke-dasharray="3 3"/>
 <text x="215" y="124" class="sm">%MEMN%</text><text x="375" y="124" class="sm">%MEMN1%</text><text x="535" y="124" class="sm">…</text>
 <line x1="280" y1="10" x2="280" y2="150" class="mk"/><line x1="440" y1="10" x2="440" y2="150" class="mk"/>
 <text x="280" y="165" class="sm">%LATCH%</text><text x="440" y="165" class="sm">%LATCH%</text>
 <path d="M155,140 h120" class="dim" marker-end="url(#ar2)" marker-start="url(#ar2)"/>
 <text x="215" y="152" class="sm">t<tspan font-size="8" dy="2">acc</tspan></text>
 </g>
 <defs><marker id="ar2" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#a33a00"/></marker></defs>
</svg>""".replace("%INS%", L("εντολή","instr.")).replace("%MEMN%", L("byte[n]","byte[n]")).replace("%MEMN1%","byte[n+1]").replace("%LATCH%", L("εκτέλεση","execute"))

CSS = """
@page{size:A4;margin:16mm 14mm 16mm 14mm}
body{font-family:"DejaVu Sans",sans-serif;font-size:9.4pt;color:#1a2730;line-height:1.42;margin:0}
.m{font-family:"DejaVu Sans Mono",monospace;font-size:8.9pt}
h1{font-size:24pt;margin:0;letter-spacing:-.01em}
h2{font-size:13pt;margin:18pt 0 6pt;padding-bottom:3pt;border-bottom:2pt solid #2f5d7c;break-after:avoid}
h2 .n{color:#2f5d7c;margin-right:6pt}
h3{font-size:10.5pt;margin:10pt 0 4pt;break-after:avoid;color:#2f5d7c}
p{margin:4pt 0}
table{border-collapse:collapse;width:100%;margin:4pt 0 6pt}
th{background:#2f5d7c;color:#fff;text-align:left;padding:3pt 5pt;font-size:8.5pt;font-weight:bold}
td{padding:2.6pt 5pt;border-bottom:.5pt solid #c6d0d6;vertical-align:top}
tr{break-inside:avoid}thead{display:table-header-group}
.cover{border-bottom:3pt solid #2f5d7c;padding-bottom:8pt;margin-bottom:10pt}
.cover .pn{font-size:10pt;color:#5a6a74;letter-spacing:.08em;text-transform:uppercase}
.cover .sub{font-size:12pt;color:#2f5d7c;margin-top:2pt}
.prelim{display:inline-block;border:1pt solid #a33a00;color:#a33a00;padding:1pt 6pt;font-size:8pt;font-weight:bold;letter-spacing:.06em;margin-top:6pt}
.two{display:flex;gap:16pt}.two>div{flex:1;min-width:0}
.feat ul{margin:2pt 0;padding-left:14pt}.feat li{margin:1.5pt 0}
.feat h3{margin-top:6pt}
.box{border:1pt solid #c6d0d6;border-left:4pt solid #2f5d7c;background:#f3f6f8;padding:6pt 9pt;margin:6pt 0}
.warn{border-left-color:#a33a00}
.fig{width:100%;display:block;margin:6pt 0}
.fig .bx rect{fill:#fff;stroke:#2f5d7c;stroke-width:1.3}
.fig text{font-family:"DejaVu Sans",sans-serif;font-size:11px;text-anchor:middle;fill:#1a2730}
.fig .sm{font-size:9.5px}.fig .l{text-anchor:start}.fig .t2{font-weight:bold;font-size:13px;fill:#2f5d7c}
.fig .ln line,.fig .ln path{stroke:#2f5d7c;stroke-width:1.3;fill:none}
.fig .wv path{fill:none;stroke:#1a2730;stroke-width:1.3}.fig .mk{stroke:#a33a00;stroke-dasharray:3 3}
.fig .dim{stroke:#a33a00 !important}
.figwrap{break-inside:avoid}
.cap{font-size:8.3pt;color:#5a6a74;text-align:center;margin-top:-2pt}
pre{font-family:"DejaVu Sans Mono",monospace;font-size:8.6pt;background:#f3f6f8;border:1pt solid #c6d0d6;padding:6pt 8pt;margin:4pt 0;white-space:pre-wrap;break-inside:avoid}
.enc td{text-align:center;font-family:"DejaVu Sans Mono",monospace}
.pb{break-before:page}
.small{font-size:8.3pt;color:#5a6a74}
.hdr{position:running(h)}
"""

o = []
add = o.append
add(f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><title>TH-4 {L('Φύλλο δεδομένων','Datasheet')}</title><style>{CSS}</style></head><body>")

# ---------------- cover ----------------
add("<div class='cover'><div class='pn'>"+L("Φύλλο δεδομένων","Datasheet")+" · "+L("Έκδοση 1.2","Revision 1.2")+" · "+L("Νοέμβριος 2026","November 2026")+"</div>")
add("<h1>TH-4</h1><div class='sub'>"+L("Μικροελεγκτής 4 bit με εξωτερική μνήμη προγράμματος, RAM 16 × 4 bit και timer","4-bit microcontroller with external program memory, 16 × 4-bit RAM and timer")+"</div>")
add("<div class='prelim'>"+L("ΠΡΟΚΑΤΑΡΚΤΙΚΟ · ΜΟΝΟ ΠΡΟΣΟΜΟΙΩΣΗ","PRELIMINARY · SIMULATION ONLY")+"</div></div>")

add("<div class='two feat'><div>")
add("<h3>"+L("Πυρήνας","Core")+"</h3><ul>"
 + "<li>"+L("Αρχιτεκτονική Harvard, 4 bit δεδομένα, 8 bit εντολές","Harvard architecture, 4-bit data, 8-bit instructions")+"</li>"
 + "<li>"+L("17 εντολές: αριθμητικές, λογικές, μνήμης, άλματα, αναμονή","17 instructions: arithmetic, logic, memory, branch, wait")+"</li>"
 + "<li>"+L("Οι περισσότερες εντολές εκτελούνται σε 1 κύκλο, τα άλματα σε 2","Most instructions execute in 1 cycle, jumps in 2")+"</li>"
 + "<li>"+L("Καταχωρητές: A (accumulator), B (μετρητής βρόχων), flag Z","Registers: A (accumulator), B (loop counter), Z flag")+"</li>"
 + "<li>"+L("Μετρητής προγράμματος 8 bit","8-bit program counter")+"</li></ul>")
add("<h3>"+L("Μνήμη","Memory")+"</h3><ul>"
 + "<li>"+L("Έως 256 bytes μνήμη προγράμματος, εξωτερική, παράλληλη","Up to 256 bytes external parallel program memory")+"</li>"
 + "<li>"+L("RAM 16 θέσεων × 4 bit μέσα στο chip","16 × 4-bit on-chip RAM")+"</li></ul>")
add("</div><div>")
add("<h3>"+L("Περιφερειακά","Peripherals")+"</h3><ul>"
 + "<li>"+L("Θύρα εισόδου 4 bit","4-bit input port")+"</li>"
 + "<li>"+L("Θύρα εξόδου 4 bit με καταχωρητή (latched)","4-bit latched output port")+"</li>"
 + "<li>"+L("Timer 25 bit για καθυστερήσεις από 1.024 έως 16.777.216 κύκλους","25-bit timer for delays from 1,024 to 16,777,216 cycles")+"</li>"
 + "<li>"+L("Ο timer τρέχει μόνο μέσα στην εντολή WAIT, για χαμηλότερη κατανάλωση","Timer runs only during WAIT, for lower power")+"</li></ul>")
add("<h3>"+L("Υλοποίηση","Implementation")+"</h3><ul>"
 + "<li>"+L("Γραμμένος σε Verilog, για το Tiny Tapeout (24 σήματα I/O)","Written in Verilog for Tiny Tapeout (24 I/O signals)")+"</li>"
 + "<li>"+L("117 flip-flops, 561 κελιά, περίπου 5.530 µm² σε SKY130 (εκτίμηση πριν την τοποθέτηση)","117 flip-flops, 561 cells, about 5,530 µm² in SKY130 (pre-placement estimate)")+"</li>"
 + "<li>"+L("Αναμένεται να χωρά σε 1 tile (~18.000 µm²)","Expected to fit in 1 tile (~18,000 µm²)")+"</li></ul>")
add("<h3>"+L("Εργαλεία","Tools")+"</h3><ul>"
 + "<li>"+L("Assembler (Python), προσομοίωση με Icarus Verilog, αυτοέλεγχος όλων των εντολών","Assembler (Python), Icarus Verilog simulation, self-test of every instruction")+"</li></ul>")
add("</div></div>")

add("<div class='box warn'><b>"+L("Κατάσταση:","Status:")+"</b> "+L(
 "Ο TH-4 έχει ελεγχθεί μόνο σε προσομοίωση. Δεν έχει κατασκευαστεί και δεν έχει περάσει από τοποθέτηση και καλωδίωση (place and route). Μέγιστη συχνότητα ρολογιού, ηλεκτρικά χαρακτηριστικά και κατανάλωση δεν έχουν μετρηθεί. Οι αντίστοιχες ενότητες θα συμπληρωθούν.",
 "TH-4 has been verified in simulation only. It has not been fabricated and has not been through place and route. Maximum clock frequency, electrical characteristics and power consumption have not been measured. These sections will be completed later.")+"</div>")

# ---------------- 1 block diagram ----------------
add("<h2><span class='n'>1</span>"+L("Διάγραμμα μπλοκ","Block diagram")+"</h2>")
add("<p>"+L(
 "Σε κάθε κύκλο ρολογιού ο TH-4 βγάζει τον μετρητή προγράμματος (PC) στα πόδια ADDR, διαβάζει το byte της εντολής από τα πόδια INSTR, το αποκωδικοποιεί και το εκτελεί. Η ALU υπολογίζει τη νέα τιμή του A. Η RAM, ο B, ο timer και οι θύρες είναι μέσα στο chip.",
 "On every clock cycle TH-4 drives the program counter (PC) on the ADDR pins, reads the instruction byte from the INSTR pins, decodes it and executes it. The ALU computes the new value of A. RAM, B, the timer and the ports are on chip.")+"</p>")
add("<div class='figwrap'>"+block_svg)
add("<p class='cap'>"+L("Σχήμα 1-1. Εσωτερική δομή του TH-4. Η μνήμη προγράμματος είναι έξω από το chip.","Figure 1-1. TH-4 internal structure. Program memory is external.")+"</p></div>")


# ---------------- 2 pins ----------------
add("<h2><span class='n'>2</span>"+L("Περιγραφή ποδιών","Pin description")+"</h2>")
add("<p>"+L("Ο TH-4 χρησιμοποιεί τη διεπαφή του Tiny Tapeout: 8 εισόδους, 8 εξόδους, 8 αμφίδρομα πόδια, ρολόι και reset.",
 "TH-4 uses the Tiny Tapeout interface: 8 inputs, 8 outputs, 8 bidirectional pins, clock and reset.")+"</p>")
add("<table><thead><tr><th>"+L("Πόδι Tiny Tapeout","Tiny Tapeout pin")+"</th><th>"+L("Όνομα","Name")+"</th><th>"+L("Κατεύθυνση","Direction")+"</th><th>"+L("Περιγραφή","Description")+"</th></tr></thead>")
for r in pin_rows():
    add(f"<tr><td class='m'>{r[0]}</td><td class='m'>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>")
add("</table>")
add("<p class='small'>"+L("Τα uio[7:4] ορίζονται πάντα ως έξοδοι και τα uio[3:0] ως είσοδοι (uio_oe = 1111 0000). Η κατεύθυνση δεν αλλάζει από το πρόγραμμα.",
 "uio[7:4] are always outputs and uio[3:0] always inputs (uio_oe = 1111 0000). Direction cannot be changed by software.")+"</p>")

# ---------------- 3 memory ----------------
add("<h2><span class='n'>3</span>"+L("Οργάνωση μνήμης","Memory organization")+"</h2>")
add("<p>"+L("Ο TH-4 έχει αρχιτεκτονική Harvard: η μνήμη προγράμματος και η μνήμη δεδομένων είναι χωριστές, με χωριστούς χώρους διευθύνσεων.",
 "TH-4 uses a Harvard architecture: program memory and data memory are separate, with separate address spaces.")+"</p>")
add("<table><thead><tr><th></th><th>"+L("Μνήμη προγράμματος","Program memory")+"</th><th>RAM</th><th>"+L("Καταχωρητές","Registers")+"</th></tr></thead>")
rows = [
 (L("Θέση","Location"), L("έξω από το chip","off chip"), L("μέσα στο chip","on chip"), L("μέσα στο chip","on chip")),
 (L("Μέγεθος","Size"), "256 × 8 bit", "16 × 4 bit", "A, B: 4 bit · Z: 1 bit · PC: 8 bit"),
 (L("Διευθύνσεις","Addresses"), "0x00 – 0xFF", "0x0 – 0xF", L("χωρίς διεύθυνση","not addressable")),
 (L("Περιεχόμενο","Contents"), L("εντολές","instructions"), L("μεταβλητές","variables"), L("τρέχουσες τιμές","working values")),
 (L("Ανάγνωση από το πρόγραμμα","Read by program"), L("όχι (μόνο εκτέλεση)","no (fetch only)"), "LOADM, ADDM, SUBM", L("σχεδόν όλες οι εντολές","most instructions")),
 (L("Εγγραφή από το πρόγραμμα","Written by program"), L("όχι","no"), "STORE", L("σχεδόν όλες οι εντολές","most instructions")),
 (L("Μετά από reset","After reset"), L("αμετάβλητη","unchanged"), L("απροσδιόριστη","undefined"), L("όλα 0","all 0")),
]
for r in rows: add("<tr>"+"".join(f"<td>{c}</td>" for c in r)+"</tr>")
add("</table>")
add("<div class='box'>"+L("Η RAM δεν μηδενίζεται στο reset. Το πρόγραμμα πρέπει να γράψει μια θέση με STORE πριν τη διαβάσει.",
 "RAM is not cleared by reset. Software must write a location with STORE before reading it.")+"</div>")
add("<h3>"+L("Ο flag Z","The Z flag")+"</h3><p>"+L(
 "Το Z γίνεται 1 όταν το αποτέλεσμα της τελευταίας εντολής που τον επηρεάζει είναι 0, αλλιώς 0. Τον επηρεάζουν οι LOAD, ADD, SUB, AND, IN, LOADM, ADDM, SUBM (με βάση τον A) και η DECB (με βάση τον B). Οι υπόλοιπες εντολές τον αφήνουν αμετάβλητο. Δεν υπάρχει flag κρατουμένου (carry).",
 "Z is set when the result of the last instruction that affects it is 0, and cleared otherwise. It is affected by LOAD, ADD, SUB, AND, IN, LOADM, ADDM, SUBM (based on A) and by DECB (based on B). All other instructions leave it unchanged. There is no carry flag.")+"</p>")

# ---------------- 4 instruction set ----------------
add("<h2 class='pb'><span class='n'>4</span>"+L("Σύνολο εντολών","Instruction set")+"</h2>")
add("<h3>"+L("Μορφή εντολής","Instruction format")+"</h3>")
add("<table class='enc'><tr><th colspan='8'>"+L("byte 1","byte 1")+"</th><th colspan='8'>"+L("byte 2 (μόνο άλματα)","byte 2 (jumps only)")+"</th></tr>"
    "<tr><td>7</td><td>6</td><td>5</td><td>4</td><td>3</td><td>2</td><td>1</td><td>0</td><td colspan='8'>7 … 0</td></tr>"
    "<tr><td colspan='4'>opcode</td><td colspan='4'>n</td><td colspan='8'>"+L("διεύθυνση aa","address aa")+"</td></tr></table>")
add("<p>"+L("Τα 4 πάνω bits είναι το opcode. Τα 4 κάτω bits είναι ένας αριθμός n (0–15): σταθερά, θέση της RAM ή παράμετρος του WAIT. Τα JUMP, JZ και JNZ έχουν δεύτερο byte με τη διεύθυνση προορισμού. Το opcode F είναι TAB όταν n = 0 και WAIT όταν n = 1–15.",
 "The upper 4 bits are the opcode. The lower 4 bits are a number n (0–15): a constant, a RAM address or the WAIT parameter. JUMP, JZ and JNZ have a second byte holding the target address. Opcode F is TAB when n = 0 and WAIT when n = 1–15.")+"</p>")
add("<h3>"+L("Σύνοψη","Summary")+"</h3>")
add("<table><thead><tr><th>Hex</th><th>"+L("Εντολή","Instruction")+"</th><th>"+L("Λειτουργία","Operation")+"</th><th>Bytes</th><th>"+L("Κύκλοι","Cycles")+"</th><th>Z</th></tr></thead>")
for i in INS:
    add(f"<tr><td class='m'>{i[0]}</td><td class='m'>{i[1]}</td><td>{L(i[2],i[3])}</td><td>{i[4]}</td><td>{i[5]}</td><td>{i[6]}</td></tr>")
add("</table>")
add("<p class='small'>"+L("✔ = η εντολή ενημερώνει το Z. Όλες οι πράξεις γίνονται modulo 16.","✔ = instruction updates Z. All arithmetic is modulo 16.")+"</p>")
add("<h3>"+L("Περιγραφή εντολών","Instruction descriptions")+"</h3>")
add("<table><thead><tr><th style='width:18%'>"+L("Εντολή","Instruction")+"</th><th>"+L("Περιγραφή","Description")+"</th></tr></thead>")
for i in INS:
    add(f"<tr><td class='m'>{i[1]}</td><td>{L(i[7],i[8])}</td></tr>")
add("</table>")

# ---------------- 5 timer ----------------
add("<h2><span class='n'>5</span>"+L("Timer και εντολή WAIT","Timer and the WAIT instruction")+"</h2>")
add("<p>"+L(
 "Ο timer είναι μετρητής 25 bit που μετράει κύκλους ρολογιού. Δεν τρέχει συνεχώς: ξεκινάει από 0 όταν εκτελεστεί ένα WAIT n, και σταματάει μόλις ανέβει το bit n+9, δηλαδή μετά από 2<sup>n+9</sup> κύκλους. Μετά συνεχίζει η επόμενη εντολή. Όσο ο timer δεν μετράει, τα flip-flops του δεν αλλάζουν τιμή.",
 "The timer is a 25-bit counter that counts clock cycles. It does not run continuously: it starts from 0 when WAIT n executes, and stops when bit n+9 goes high, that is after 2<sup>n+9</sup> cycles. Execution then continues with the next instruction. While the timer is not counting, its flip-flops do not toggle.")+"</p>")
add("<p>"+L("Κάθε WAIT n κρατάει ακριβώς 2<sup>n+9</sup> + 2 κύκλους, ανεξάρτητα από ό,τι προηγήθηκε. Κατά τη διάρκειά του οι A, B, Z, η RAM και οι θύρες δεν αλλάζουν.",
 "Every WAIT n takes exactly 2<sup>n+9</sup> + 2 cycles, independent of what came before. During WAIT, A, B, Z, RAM and the ports do not change.")+"</p>")
add("<table><thead><tr><th>"+L("Εντολή","Instruction")+"</th><th>Hex</th><th>"+L("Κύκλοι","Cycles")+"</th><th>"+L("στο 1 MHz","at 1 MHz")+"</th><th>"+L("στο 10 MHz","at 10 MHz")+"</th></tr></thead>")
def fmt_t(sec):
    if sec >= 1: v, u = sec, "s"
    elif sec >= 1e-3: v, u = sec*1e3, "ms"
    else: v, u = sec*1e6, "µs"
    s = f"{v:.3g}"
    return (s.replace(".", ",") if lang == "el" else s) + " " + u
def fmt_n(n):
    s = f"{n:,}"
    return s.replace(",", ".") if lang == "el" else s
for n in range(1, 16):
    c = 2**(n+9) + 2
    add(f"<tr><td class='m'>WAIT {n}</td><td class='m'>F{n:X}</td><td>{fmt_n(c)}</td><td>{fmt_t(c/1e6)}</td><td>{fmt_t(c/1e7)}</td></tr>")
add("</table>")
add("<p>"+L("Για μεγαλύτερες καθυστερήσεις, το WAIT μπαίνει σε βρόχο με τον B:","For longer delays, put WAIT in a loop with B:")+"</p>")
add("<pre>        LDB 10          ; "+L("10 επαναλήψεις","10 iterations")+"\nwait:   WAIT 15         ; "+L("1,68 s στα 10 MHz","1.68 s at 10 MHz")+"\n        DECB\n        JNZ wait        ; "+L("σύνολο περίπου 16,8 s","about 16.8 s in total")+"</pre>")

# ---------------- 6 ports ----------------
add("<h2><span class='n'>6</span>"+L("Θύρες εισόδου και εξόδου","Input and output ports")+"</h2>")
add("<h3>"+L("Θύρα εισόδου (IN[3:0] στα uio[3:0])","Input port (IN[3:0] on uio[3:0])")+"</h3><p>"+L(
 "Η εντολή IN διαβάζει τα 4 πόδια τη στιγμή που εκτελείται και αντιγράφει την τιμή στον A. Δεν υπάρχουν εσωτερικές αντιστάσεις pull-up ούτε φίλτρο αναπηδήσεων: για κουμπιά χρειάζονται εξωτερικές αντιστάσεις, και η αναπήδηση πρέπει να αντιμετωπιστεί στο πρόγραμμα (για παράδειγμα με WAIT και δεύτερη ανάγνωση).",
 "IN samples the 4 pins when it executes and copies the value to A. There are no internal pull-ups and no debouncing: buttons need external resistors, and bounce must be handled in software (for example with WAIT and a second read).")+"</p>")
add("<h3>"+L("Θύρα εξόδου (OUT[3:0] στα uio[7:4])","Output port (OUT[3:0] on uio[7:4])")+"</h3><p>"+L(
 "Η θύρα εξόδου έχει δικό της καταχωρητή 4 bit. Η εντολή OUT γράφει τον A σε αυτόν, και η τιμή μένει σταθερή στα πόδια μέχρι το επόμενο OUT, ενώ ο A μπορεί να αλλάζει. Μετά από reset η θύρα είναι 0000. Το ρεύμα που μπορούν να δώσουν τα πόδια ορίζεται από το chip του Tiny Tapeout· για LED χρησιμοποιήστε αντιστάσεις, και για μεγαλύτερα φορτία τρανζίστορ.",
 "The output port has its own 4-bit register. OUT writes A to it, and the value stays on the pins until the next OUT, even while A changes. After reset the port is 0000. Pin drive strength is set by the Tiny Tapeout chip; use resistors for LEDs and transistors for larger loads.")+"</p>")

# ---------------- 7 reset & clock ----------------
add("<h2><span class='n'>7</span>"+L("Reset και ρολόι","Reset and clock")+"</h2>")
add("<p>"+L(
 "Το reset (rst_n) είναι ενεργό στο 0 και σύγχρονο: λαμβάνεται υπόψη στη θετική ακμή του ρολογιού. Πρέπει να μείνει στο 0 για τουλάχιστον έναν κύκλο. Όσο είναι 0:",
 "Reset (rst_n) is active low and synchronous: it is sampled on the rising clock edge. Hold it low for at least one cycle. While it is low:")+"</p><ul>"
 + "<li>PC = 0x00, A = 0, B = 0, Z = 0</li>"
 + "<li>"+L("θύρα εξόδου = 0000, timer = 0","output port = 0000, timer = 0")+"</li>"
 + "<li>"+L("η RAM δεν αλλάζει","RAM is not changed")+"</li></ul>")
add("<p>"+L("Μόλις το rst_n γίνει 1, η εκτέλεση αρχίζει από τη διεύθυνση 0x00 στην επόμενη θετική ακμή.",
 "When rst_n goes high, execution starts at address 0x00 on the next rising edge.")+"</p>")
add("<p>"+L("Όλοι οι καταχωρητές αλλάζουν στη θετική ακμή του clk. Η μέγιστη συχνότητα δεν έχει ακόμα επαληθευτεί. Στην πράξη το όριο θα το βάλει συνήθως η εξωτερική μνήμη (ενότητα 8).",
 "All registers change on the rising edge of clk. Maximum frequency has not yet been verified. In practice the limit will usually be set by the external memory (section 8).")+"</p>")

# ---------------- 8 external memory ----------------
add("<h2><span class='n'>8</span>"+L("Σύνδεση μνήμης προγράμματος","Connecting program memory")+"</h2>")
add("<p>"+L(
 "Η μνήμη προγράμματος πρέπει να είναι ασύγχρονη (συνδυαστική): μόλις αλλάξει η διεύθυνση, να βγάλει τα δεδομένα χωρίς δικό της ρολόι. Ο TH-4 αλλάζει τη διεύθυνση στη θετική ακμή και διαβάζει την εντολή στην επόμενη θετική ακμή.",
 "Program memory must be asynchronous (combinational): when the address changes, it must output the data without its own clock. TH-4 changes the address on a rising edge and samples the instruction on the next rising edge.")+"</p>")
add("<div class='figwrap'>"+timing_svg)
add("<p class='cap'>"+L("Σχήμα 8-1. Ανάγνωση εντολής. Ο χρόνος πρόσβασης της μνήμης t<sub>acc</sub> πρέπει να είναι μικρότερος από μία περίοδο ρολογιού, μείον τις καθυστερήσεις των ποδιών.",
 "Figure 8-1. Instruction fetch. Memory access time t<sub>acc</sub> must be less than one clock period, minus pin delays.")+"</p></div>")
add("<h3>"+L("Επιλογή 1: παράλληλη EEPROM","Option 1: parallel EEPROM")+"</h3><p>"+L(
 "Μια EEPROM όπως η 28C64 ή η 28C16: οι γραμμές διεύθυνσης A0–A7 στα ADDR0–ADDR7, οι γραμμές δεδομένων D0–D7 στα INSTR0–INSTR7, οι υπόλοιπες γραμμές διεύθυνσης στη γείωση, /CE και /OE στη γείωση, /WE στην τροφοδοσία. Με χρόνο πρόσβασης 150 ns το ρολόι πρέπει να είναι κάτω από περίπου 6 MHz· αφήστε περιθώριο για τις καθυστερήσεις των ποδιών (ενδεικτικά 2–4 MHz). Προσοχή στα επίπεδα τάσης: ελέγξτε ότι η μνήμη είναι συμβατή με την τάση I/O του chip.",
 "An EEPROM such as the 28C64 or 28C16: address lines A0–A7 to ADDR0–ADDR7, data lines D0–D7 to INSTR0–INSTR7, remaining address lines to ground, /CE and /OE to ground, /WE to supply. With 150 ns access time the clock must stay below about 6 MHz; leave margin for pin delays (2–4 MHz as a guide). Check that the memory's logic levels match the chip's I/O voltage.")+"</p>")
add("<h3>"+L("Επιλογή 2: μικροελεγκτής ως μνήμη","Option 2: microcontroller as memory")+"</h3><p>"+L(
 "Ένας AVR ή άλλος μικροελεγκτής διαβάζει τη διεύθυνση από 8 πόδια, βρίσκει το byte σε έναν πίνακα στη flash του και το βγάζει σε 8 άλλα πόδια. Το πρόγραμμα του TH-4 αλλάζει απλώς με ξαναπρογραμματισμό του μικροελεγκτή. Επειδή η απάντηση γίνεται σε software, το ρολόι του TH-4 πρέπει να είναι αρκετά αργό ώστε ο μικροελεγκτής να προλαβαίνει (πρέπει να μετρηθεί για κάθε υλοποίηση).",
 "An AVR or other microcontroller reads the address on 8 pins, looks up the byte in a table in its flash and drives it on 8 other pins. The TH-4 program is changed simply by reprogramming the microcontroller. Because the lookup is done in software, the TH-4 clock must be slow enough for the microcontroller to keep up (to be measured for each implementation).")+"</p>")

# ---------------- 9 tools ----------------
add("<h2><span class='n'>9</span>"+L("Εργαλεία ανάπτυξης","Development tools")+"</h2>")
add("<table><thead><tr><th>"+L("Αρχείο","File")+"</th><th>"+L("Τι κάνει","Purpose")+"</th></tr></thead>"
 + f"<tr><td class='m'>tt_um_th4.v</td><td>{L('ο TH-4 σε Verilog','TH-4 in Verilog')}</td></tr>"
 + f"<tr><td class='m'>th4asm.py</td><td>{L('assembler: .asm → .hex','assembler: .asm → .hex')}</td></tr>"
 + f"<tr><td class='m'>run.v</td><td>{L('προσομοίωση οποιουδήποτε προγράμματος από το prog.hex, με ίχνος εκτέλεσης','simulates any program from prog.hex, with an execution trace')}</td></tr>"
 + f"<tr><td class='m'>tb.v, selftest.asm</td><td>{L('αυτοέλεγχος: δοκιμάζει όλες τις εντολές και τον timer','self-test: exercises every instruction and the timer')}</td></tr>"
 + "</table>")
add("<h3>"+L("Σύνταξη του assembler","Assembler syntax")+"</h3>")
add("<pre>; "+L("σχόλιο","comment")+"\ntemp = 0            ; "+L("όνομα για τη θέση 0 της RAM (ή .equ temp = 0)","name for RAM location 0 (or .equ temp = 0)")+"\nloop:   OUT         ; "+L("ετικέτα: η διεύθυνση της εντολής","label: the instruction's address")+"\n        STORE temp\n        JUMP loop\n        ORG 0x40    ; "+L("οι επόμενες εντολές ξεκινούν από τη διεύθυνση 0x40","following code starts at address 0x40")+"</pre>")
add("<h3>"+L("Ροή εργασίας","Workflow")+"</h3>")
add("<pre>python3 th4asm.py "+L("πρόγραμμα","program")+".asm &gt; prog.hex\niverilog -g2012 -o run run.v tt_um_th4.v\nvvp run +cycles=500 +in=5      ; "+L("+in = τιμή της θύρας εισόδου","+in = input port value")+"</pre>")

# ---------------- 10 examples ----------------
add("<h2><span class='n'>10</span>"+L("Παραδείγματα","Examples")+"</h2>")
add("<p class='small'>"+L("Όλα τα παραδείγματα έχουν ελεγχθεί σε προσομοίωση.","All examples have been verified in simulation.")+"</p>")
ex = [
 (L("Μετρητής με timer","Counter with timer"), L("Μετράει 0–15 στη θύρα εξόδου, ένα νούμερο κάθε 0,42 s στα 10 MHz.","Counts 0–15 on the output port, one step every 0.42 s at 10 MHz."),
  "        LOAD 0\nloop:   OUT\n        WAIT 13\n        ADD 1\n        JUMP loop", "00 50 FD 11 60 01"),
 (L("Τρεχούμενο φως","Running light"), L("Ένα LED ανάβει τη φορά: 0001, 0010, 0100, 1000. Το A + A κάνει ολίσθηση αριστερά, και το ξεχείλισμα (8 + 8 = 0) ξεκινάει τον κύκλο από την αρχή.","One LED at a time: 0001, 0010, 0100, 1000. A + A shifts left, and the overflow (8 + 8 = 0) restarts the cycle."),
  "temp = 0\n        LOAD 1\nloop:   OUT\n        WAIT 13\n        STORE temp\n        ADDM temp       ; A = A + A\n        JNZ loop\n        LOAD 1\n        JUMP loop", "01 50 FD 80 D0 C0 01 01 60 01"),
 (L("Κουμπί","Button"), L("Αν το IN0 είναι 1, η έξοδος δείχνει 1111, αλλιώς 0000.","If IN0 is 1 the output shows 1111, otherwise 0000."),
  "loop:   IN\n        AND 1           ; "+L("κράτα μόνο το bit 0","keep bit 0 only")+"\n        JZ off\n        LOAD 15\n        OUT\n        JUMP loop\noff:    LOAD 0\n        OUT\n        JUMP loop", "40 31 70 08 0F 50 60 00 00 50 60 00"),
]
for t, d, code, hx in ex:
    add(f"<h3>{t}</h3><p>{d}</p><pre>{e(code)}</pre><p class='small'>"+L("Μηχανική γλώσσα: ","Machine code: ")+M(hx)+"</p>")

# ---------------- 11 implementation ----------------
add("<h2><span class='n'>11</span>"+L("Στοιχεία υλοποίησης","Implementation data")+"</h2>")
add("<table><thead><tr><th>"+L("Μέγεθος","Item")+"</th><th>"+L("Τιμή","Value")+"</th></tr></thead>"
 + f"<tr><td>{L('Flip-flops','Flip-flops')}</td><td>117 ({L('64 RAM, 53 καταχωρητές και έλεγχος','64 RAM, 53 registers and control')})</td></tr>"
 + f"<tr><td>{L('Κελιά SKY130 (sky130_fd_sc_hd)','SKY130 cells (sky130_fd_sc_hd)')}</td><td>561</td></tr>"
 + f"<tr><td>{L('Επιφάνεια κελιών','Cell area')}</td><td>{L('περίπου 5.530 µm²','about 5,530 µm²')}</td></tr>"
 + f"<tr><td>{L('Tiles Tiny Tapeout','Tiny Tapeout tiles')}</td><td>{L('1 (αναμένεται, δεν έχει επαληθευτεί)','1 (expected, not yet verified)')}</td></tr>"
 + "</table>")
FF = [
 ("RAM", "64", "16 θέσεις × 4 bit", "16 locations × 4 bit"),
 ("Timer", "25", "μετρητής της εντολής WAIT", "WAIT instruction counter"),
 ("PC", "8", "διεύθυνση της εντολής", "instruction address"),
 ("A", "4", "accumulator", "accumulator"),
 ("B", "4", "μετρητής βρόχων", "loop counter"),
 ("port_out", "4", "καταχωρητής θύρας εξόδου", "output port register"),
 ("jop", "4", "ποιο άλμα περιμένει τη διεύθυνσή του", "pending jump type"),
 ("state", "3", "κατάσταση μονάδας ελέγχου (one-hot: FETCH, ADDR, WAIT)", "control state (one-hot: FETCH, ADDR, WAIT)"),
 ("Z", "1", "flag μηδέν", "zero flag"),
]
add("<h3>"+L("Flip-flops ανά μονάδα","Flip-flops per unit")+"</h3>")
add("<table><thead><tr><th>"+L("Μονάδα","Unit")+"</th><th>Flip-flops</th><th>"+L("Τι κρατάει","Contents")+"</th></tr></thead>")
for n_, c_, el_, en_ in FF:
    add(f"<tr><td class='m'>{n_}</td><td>{c_}</td><td>{L(el_, en_)}</td></tr>")
add("<tr><td><b>"+L("Σύνολο","Total")+"</b></td><td><b>117</b></td><td></td></tr></table>")
add("<p class='small'>"+L("Η RAM είναι το 55% των flip-flops και ο timer το 21%. Ο πυρήνας (PC, A, B, Z, θύρα, έλεγχος) είναι 28. Το state δηλώνεται με 2 bit στον κώδικα, αλλά η σύνθεση το κωδικοποιεί one-hot με 3 flip-flops.",
 "RAM is 55% of the flip-flops and the timer 21%. The core (PC, A, B, Z, port, control) is 28. state is declared as 2 bits in the source, but synthesis encodes it one-hot with 3 flip-flops.")+"</p>")
add("<p class='small'>"+L("Μέτρηση με Yosys 0.33 και τη βιβλιοθήκη sky130_fd_sc_hd (tt, 25 °C, 1,8 V), πριν την τοποθέτηση. Η τελική επιφάνεια θα είναι μεγαλύτερη λόγω καλωδίωσης και ενισχυτών ρολογιού.",
 "Measured with Yosys 0.33 and the sky130_fd_sc_hd library (tt, 25 °C, 1.8 V), before placement. Final area will be larger due to routing and clock buffers.")+"</p>")

# ---------------- 12 revision ----------------
add("<h2><span class='n'>12</span>"+L("Ιστορικό εκδόσεων","Revision history")+"</h2>")
add("<table><thead><tr><th>"+L("Έκδοση","Revision")+"</th><th>"+L("Αλλαγές","Changes")+"</th></tr></thead>"
 + f"<tr><td>1.0</td><td>{L('16 εντολές, καταχωρητές A και B, RAM 16 × 4 bit.','16 instructions, A and B registers, 16 × 4-bit RAM.')}</td></tr>"
 + f"<tr><td>1.1</td><td>{L('Timer και εντολή WAIT n (opcode F, n = 1–15).','Timer and WAIT n instruction (opcode F, n = 1–15).')}</td></tr>"
 + f"<tr><td>1.2</td><td>{L('Ο timer τρέχει μόνο μέσα στο WAIT, για οικονομία ρεύματος. Κάθε WAIT κρατάει πλέον ακριβώς 2<sup>n+9</sup> + 2 κύκλους.','The timer runs only during WAIT, to save power. Every WAIT now takes exactly 2<sup>n+9</sup> + 2 cycles.')}</td></tr>"
 + "</table>")
add("<p class='small' style='margin-top:14pt'>"+L("Σχεδίαση: George Avrsam, 2026.","Design: George Avrsam, 2026.")+"</p>")
add("</body></html>")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(o))
