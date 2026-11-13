import sys, html, re
sys.path.insert(0, "/home/user/th4")
from th4asm import OPS

import json
CFG = json.load(open(sys.argv[3], encoding="utf-8"))
SRC = CFG["src"]
BUTTONS = CFG["port_in"]
NSIM = sum(1 for _ in open(sys.argv[1]))
TWO = {n for n, (o, k) in OPS.items() if k == "a"}

# ---------- assemble (κρατάμε και τα σχόλια) ----------
rows, labels, pc = [], {}, 0
for raw in open(SRC, encoding="utf-8"):
    code, _, comment = raw.partition(";")
    text = code.strip()
    if not text:
        continue
    lab = ""
    while ":" in text:
        l, text = text.split(":", 1); lab = l.strip(); labels[lab] = pc; text = text.strip()
    if not text:
        continue
    parts = text.split()
    name = parts[0].upper(); arg = parts[1] if len(parts) > 1 else None
    rows.append(dict(pc=pc, label=lab, name=name, arg=arg, comment=comment.strip()))
    pc += 2 if name in TWO else 1
rom = [0] * 256
addr2row = {}
for r in rows:
    op, kind = OPS[r["name"]]
    if kind == "n":
        r["n"] = int(r["arg"], 0); r["bytes"] = [op << 4 | r["n"]]
    elif kind == "-":
        r["n"] = 0; r["bytes"] = [op << 4]
    else:
        r["target"] = labels[r["arg"]]; r["bytes"] = [op << 4, r["target"]]
    for i, b in enumerate(r["bytes"]):
        rom[r["pc"] + i] = b
    addr2row[r["pc"]] = r

b4 = lambda v: format(v, "04b")

# ---------- simulate ----------
A = B = Z = LED = 0; ram = [None] * 16; pc = 0; trace = []; last_pc = None
for step in range(NSIM):
    r = addr2row[pc]; name = r["name"]; n = r.get("n", 0); here = pc
    oA, oB, oZ, oLED = A, B, Z, LED
    newpc = pc + len(r["bytes"]); note = ""; kind = ""
    def zmsg(v):
        return " Το αποτέλεσμα είναι 0, άρα <b>Z = 1</b>." if v == 0 else (" Δεν είναι 0, άρα Z = 0." if oZ else "")
    if name == "LOAD":
        A = n; Z = int(A == 0); note = f"Βάζει τον αριθμό {n} στον A." + zmsg(A)
    elif name == "ADD":
        A = (oA + n) & 15; Z = int(A == 0)
        note = f"A = {oA} + {n} = {oA+n}" + (f" → δεν χωράει σε 4 bits, μένει <b>{A}</b> (ξεχείλισμα)." if oA + n > 15 else ".") + zmsg(A)
    elif name == "SUB":
        A = (oA - n) & 15; Z = int(A == 0)
        note = f"A = {oA} − {n} = {A}." + zmsg(A)
    elif name == "AND":
        A = oA & n; Z = int(A == 0)
        note = f"A = {b4(oA)} AND {b4(n)} = {b4(A)} ({A}). Μένουν 1 μόνο τα bits που είναι 1 και στα δύο." + zmsg(A)
    elif name == "IN":
        A = BUTTONS; Z = int(A == 0)
        note = f"Διαβάζει τη θύρα εισόδου ({b4(BUTTONS)}) και τη βάζει στον A = {A}." + zmsg(A)
    elif name == "OUT":
        LED = oA; kind = "led"
        note = f"Η θύρα εξόδου παίρνει την τιμή του A: {oA} = <b>{b4(oA)}</b>."
    elif name == "STORE":
        ram[n] = oA; note = f"Αποθηκεύει τον A ({oA}) στη θέση {n} της RAM. Ο A δεν αλλάζει."
    elif name == "LOADM":
        A = ram[n]; Z = int(A == 0); note = f"Φορτώνει στον A τη θέση {n} της RAM, που έχει {ram[n]}." + zmsg(A)
    elif name == "ADDM":
        A = (oA + ram[n]) & 15; Z = int(A == 0)
        note = f"A = {oA} + RAM[{n}] = {oA} + {ram[n]} = {A}." + zmsg(A)
    elif name == "SUBM":
        A = (oA - ram[n]) & 15; Z = int(A == 0)
        note = f"A = {oA} − RAM[{n}] = {oA} − {ram[n]} = {A}." + zmsg(A)
    elif name == "LDB":
        B = n; note = f"Βάζει τον αριθμό {n} στον B (μετρητής του βρόχου). Το Z δεν αλλάζει."
    elif name == "DECB":
        B = (oB - 1) & 15; Z = int(B == 0)
        note = f"B = {oB} − 1 = {B}." + (" Ο B έφτασε στο 0, άρα <b>Z = 1</b>: ο βρόχος τελείωσε." if B == 0 else " Δεν είναι 0, άρα Z = 0: ο βρόχος συνεχίζει.")
    elif name == "WAIT":
        per = f"{2**(n+9):,}".replace(",", ".")
        note = f"Μηδενίζει τον timer και σταματάει το πρόγραμμα για {per} παλμούς ρολογιού, μέχρι να ανέβει το bit {n+9} του timer. Οι A, B, Z δεν αλλάζουν."
        kind = "wait"
    elif name == "TAB":
        B = oA; note = f"Αντιγράφει τον A ({oA}) στον B. Το Z δεν αλλάζει."
    elif name == "JUMP":
        newpc = r["target"]; kind = "jump"
        note = f"Πηδάει πάντα στη διεύθυνση {r['target']:02x}" + (" (στον εαυτό της: το πρόγραμμα «σταματάει» εδώ)." if r["target"] == here else (" (πίσω στην αρχή του βρόχου)." if r["target"] < here else "."))
    elif name == "JZ":
        if oZ: newpc = r["target"]; kind = "jump"; note = f"Z = 1, άρα <b>πηδάει</b> στη διεύθυνση {r['target']:02x}."
        else: note = f"Z = 0, άρα <b>δεν πηδάει</b>. Συνεχίζει στην επόμενη εντολή ({newpc:02x})."
    elif name == "JNZ":
        if not oZ: newpc = r["target"]; kind = "jump"; note = f"Z = 0, άρα <b>πηδάει</b> {'πίσω ' if r['target'] < here else ''}στη διεύθυνση {r['target']:02x}."
        else: note = f"Z = 1, άρα <b>δεν πηδάει</b>. Συνεχίζει στην επόμενη εντολή ({newpc:02x})."
    txt = name + (f" {r['target']:02x}" if name in TWO else (f" {n}" if OPS[name][1] == "n" else ""))
    trace.append(dict(pc=here, txt=txt, A=A, B=B, Z=Z, LED=LED, note=note, kind=kind,
                      chA=A != oA, chB=B != oB, chZ=Z != oZ, chL=LED != oLED))
    if newpc == here and CFG.get("stop_on_self_jump", True): break
    pc = newpc

# ---------- cross-check με την προσομοίωση Verilog ----------
sim = [l.split() for l in open(sys.argv[1])]
ok = len(sim) == len(trace)
for s, t in zip(sim, trace):
    l = " ".join(s)
    m = re.match(r"PC=(\w+) .*A=\s*(\d+)\s+B=\s*(\d+)\s+Z=(\d)\s+OUT=(\d+)", l)
    if not m or (int(m[1], 16), int(m[2]), int(m[3]), int(m[4]), m[5]) != (t["pc"], t["A"], t["B"], t["Z"], b4(t["LED"])):
        ok = False; print("MISMATCH", l, t)
print("cross-check with Verilog simulation:", "OK" if ok else "FAILED", len(sim), len(trace), file=sys.stderr)

# ---------- HTML ----------
e = html.escape
INSTR = [("0n","LOAD n","A ← n","✔"),("1n","ADD n","A ← A + n","✔"),("2n","SUB n","A ← A − n","✔"),("3n","AND n","A ← A AND n","✔"),
 ("40","IN","A ← θύρα εισόδου","✔"),("50","OUT","θύρα εξόδου ← A",""),("60 aa","JUMP aa","PC ← aa (πάντα)",""),("70 aa","JZ aa","αν Z = 1: PC ← aa",""),
 ("8n","STORE n","RAM[n] ← A",""),("9n","LOADM n","A ← RAM[n]","✔"),("An","LDB n","B ← n",""),("B0","DECB","B ← B − 1","✔"),
 ("C0 aa","JNZ aa","αν Z = 0: PC ← aa",""),("Dn","ADDM n","A ← A + RAM[n]","✔"),("En","SUBM n","A ← A − RAM[n]","✔"),("F0","TAB","B ← A",""),("F1–FF","WAIT n","περίμενε τον timer (n = 1…15)","")]
o = []
o.append(("""<!doctype html><html lang="el"><head><meta charset="utf-8"><title>" + CFG["title"] + "</title><style>
@page{size:A4;margin:14mm 12mm}
body{font-family:"DejaVu Sans",sans-serif;font-size:9.5pt;color:#1b2830;line-height:1.4;margin:0}
h1{font-size:19pt;margin:0 0 2pt}h2{font-size:12.5pt;margin:16pt 0 6pt;border-bottom:1.5pt solid #2f6f8f;padding-bottom:2pt;break-after:avoid}
p{margin:4pt 0}.sub{color:#5a6a74;margin-bottom:8pt}
table{border-collapse:collapse;width:100%}th{background:#2f6f8f;color:#fff;text-align:left;padding:3pt 5pt;font-size:8.5pt}
td{padding:2.5pt 5pt;border-bottom:.5pt solid #c9d2d8;vertical-align:top}
.m{font-family:"DejaVu Sans Mono",monospace;font-size:8.8pt;white-space:nowrap}
tr{break-inside:avoid}thead{display:table-header-group}
.ch{background:#ffe2c9;font-weight:bold}.led td{background:#fdf3d7}.jump td.note{color:#a33a00}
.lab{color:#a33a00;font-weight:bold}.cm{color:#5a6a74}
.box{border:1pt solid #c9d2d8;border-left:4pt solid #2f6f8f;padding:6pt 9pt;margin:6pt 0;background:#f4f7f8}
.two{display:flex;gap:14pt}.two>div{flex:1}
.key span{display:inline-block;padding:1pt 5pt;margin-right:8pt}
tr.wait td.note{color:#1f5f7a}
.gap td{text-align:center;color:#5a6a74;font-style:italic;background:#eef2f4}
</style></head><body>""").replace('" + CFG["title"] + "', CFG["title"]))
o.append("<h1>" + CFG["title"] + "</h1>")
o.append('<p class="sub">' + CFG["sub"] + "</p>")
o.append("<h2>1. Τι έχει μέσα ο TH-4</h2><div class='two'><div><table><tr><th>Κομμάτι</th><th>Μέγεθος</th><th>Τι κάνει</th></tr>"
 "<tr><td class='m'>A</td><td>4 bits (0–15)</td><td>ο βασικός register· εδώ γίνονται οι πράξεις</td></tr>"
 "<tr><td class='m'>B</td><td>4 bits (0–15)</td><td>δεύτερος register· μετρητής για βρόχους</td></tr>"
 "<tr><td class='m'>Z</td><td>1 bit</td><td>flag: γίνεται 1 όταν ένα αποτέλεσμα είναι 0</td></tr>"
 "<tr><td class='m'>PC</td><td>8 bits</td><td>η διεύθυνση της εντολής που εκτελείται</td></tr>"
 "<tr><td class='m'>RAM</td><td>16 × 4 bits</td><td>16 θέσεις για μεταβλητές</td></tr>"
 "<tr><td class='m'>port_out</td><td>4 bits</td><td>καταχωρητής της θύρας εξόδου (πόδια uio[7:4])</td></tr><tr><td class='m'>port_in</td><td>4 πόδια</td><td>η θύρα εισόδου (πόδια uio[3:0])</td></tr><tr><td class='m'>timer</td><td>25 bits</td><td>μετράει παλμούς ρολογιού μόνο όσο εκτελείται ένα WAIT· αλλιώς είναι σταματημένος, για οικονομία ρεύματος</td></tr></table></div>"
 "<div><div class='box'><b>Πώς είναι μια εντολή (1 byte)</b><br><span class='m'>[7:4] = opcode &nbsp; [3:0] = n</span><br>"
 "Παράδειγμα: <span class='m'>ADD 3</span> = opcode 1, n 3 = <span class='m'>13</span> (hex).<br>"
 "Τα <span class='m'>JUMP</span>, <span class='m'>JZ</span>, <span class='m'>JNZ</span> πιάνουν <b>2 bytes</b>: το δεύτερο είναι η διεύθυνση.<br>Το opcode F είναι <span class='m'>TAB</span> όταν n = 0 και <span class='m'>WAIT n</span> όταν n = 1…15.</div>"
 "<div class='box'>" + CFG["box"] + "</div></div></div>")
o.append("<h2>2. Οι εντολές</h2><table><tr><th>Hex</th><th>Εντολή</th><th>Τι κάνει</th><th>Αλλάζει το Z</th><th>Hex</th><th>Εντολή</th><th>Τι κάνει</th><th>Αλλάζει το Z</th></tr>")
half = (len(INSTR) + 1) // 2
for i in range(half):
    a = INSTR[i]; b = INSTR[i + half] if i + half < len(INSTR) else ("", "", "", "")
    o.append(f"<tr><td class='m'>{a[0]}</td><td class='m'>{a[1]}</td><td>{a[2]}</td><td>{a[3]}</td><td class='m'>{b[0]}</td><td class='m'>{b[1]}</td><td>{b[2]}</td><td>{b[3]}</td></tr>")
o.append("</table>")
o.append("<h2 style='break-before:page'>3. Το πρόγραμμα στη μνήμη</h2><p>Αριστερά η διεύθυνση και τα bytes που γράφονται στη μνήμη προγράμματος, δεξιά η assembly.</p>"
         "<table><thead><tr><th>Διεύθ.</th><th>Bytes</th><th>Ετικέτα</th><th>Εντολή</th><th>Σχόλιο</th></tr></thead>")
for r in rows:
    by = " ".join(f"{b:02X}" for b in r["bytes"])
    o.append(f"<tr><td class='m'>{r['pc']:02x}</td><td class='m'>{by}</td><td class='m lab'>{e(r['label'])}</td>"
             f"<td class='m'>{r['name']} {e(r['arg'] or '')}</td><td class='cm'>{e(r['comment'])}</td></tr>")
o.append("</table>")
o.append("<h2>4. Η εκτέλεση, βήμα προς βήμα</h2>"
 "<p>Κάθε γραμμή δείχνει τις τιμές <b>μετά</b> την εκτέλεση της εντολής.</p>"
 "<p class='key'><span class='ch'>πορτοκαλί</span> η τιμή άλλαξε σε αυτό το βήμα <span style='background:#fdf3d7'>κίτρινη γραμμή</span> άλλαξε η θύρα εξόδου <span style='color:#a33a00'>κόκκινο κείμενο</span> έγινε άλμα</p>"
 "<table><thead><tr><th>#</th><th>PC</th><th>Εντολή</th><th>A</th><th>B</th><th>Z</th><th>OUT</th><th>Τι έγινε</th></tr></thead>")
def row(i, t):
    c = lambda f: " ch" if t[f] else ""
    return (f"<tr class='{t['kind'] if t['kind']!='led' or t['chL'] else ''}'><td>{i}</td><td class='m'>{t['pc']:02x}</td><td class='m'>{t['txt']}</td>"
            f"<td class='m{c('chA')}'>{t['A']}</td><td class='m{c('chB')}'>{t['B']}</td><td class='m{c('chZ')}'>{t['Z']}</td>"
            f"<td class='m{c('chL')}'>{b4(t['LED'])}</td><td class='note'>{t['note']}</td></tr>")
def gap(msg):
    return f"<tr class='gap'><td colspan='8'>{msg}</td></tr>"
show = [True] * len(trace); gaps = {}
if CFG.get("collapse"):
    i = 0
    while i + 3 < len(trace):
        j = i   # μέγιστη σειρά επαναλαμβανόμενων ζευγών (pc a, pc b)
        while j + 3 < len(trace) and trace[j]["pc"] == trace[j+2]["pc"] and trace[j+1]["pc"] == trace[j+3]["pc"]:
            j += 2
        pairs = (j - i) // 2 + 1
        if pairs >= 6:
            lo, hi = i + 4, i + 2 * pairs - 4          # κρατάμε 2 ζεύγη στην αρχή και 2 στο τέλος
            for k in range(lo, hi): show[k] = False
            gaps[lo] = f"… ο βρόχος επαναλαμβάνεται άλλες {(hi - lo)//2} φορές: ο B κατεβαίνει από {trace[lo]['B']} έως {trace[hi-1]['B']} …"
            i = j + 2
        else:
            i += 1
for lo, hi, msg in CFG.get("skip", []):
    for k in range(lo - 1, hi): show[k] = False
    gaps = {k: v for k, v in gaps.items() if not (lo - 1 <= k < hi)}
    gaps[lo - 1] = msg
for i, t in enumerate(trace, 1):
    if i - 1 in gaps and i <= CFG.get('last', len(trace)): o.append(gap(gaps[i - 1]))
    if show[i - 1] and i <= CFG.get("last", len(trace)): o.append(row(i, t))
o.append("</table>")
o.append("<div class='box'>" + CFG["result"] + "</div>")
o.append("<h2>5. Τι αξίζει να προσέξεις</h2><ul>" + "".join("<li>" + x + "</li>" for x in CFG["notes"]) + "</ul></body></html>")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(o))
