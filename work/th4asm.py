#!/usr/bin/env python3
"""Assembler για τον TH-4.   Χρήση:  python3 th4asm.py prog.asm > prog.hex

Ονόματα για θέσεις της RAM ή σταθερές (όπως το .equ του AVR):
    .equ temp = 0        ή απλά        temp = 0
"""
import sys

OPS = {  # όνομα: (opcode, είδος)   είδος: n = θέλει αριθμό 0-15, - = τίποτα, a = διεύθυνση (2 bytes)
    "LOAD": (0x0, "n"), "ADD": (0x1, "n"), "SUB": (0x2, "n"), "AND": (0x3, "n"),
    "IN": (0x4, "-"), "OUT": (0x5, "-"), "JUMP": (0x6, "a"), "JZ": (0x7, "a"),
    "STORE": (0x8, "n"), "LOADM": (0x9, "n"), "LDB": (0xA, "n"), "DECB": (0xB, "-"),
    "JNZ": (0xC, "a"), "ADDM": (0xD, "n"), "SUBM": (0xE, "n"), "TAB": (0xF, "-"),
    "WAIT": (0xF, "n"),   # Fn με n = 1..15 (το F0 είναι το TAB)
}

def num(s):
    return int(s, 0)

def main(path):
    lines = []
    for raw in open(path, encoding="utf-8"):
        text = raw.split(";")[0].strip()
        if text:
            lines.append((text, raw.rstrip()))
    # 1ο πέρασμα: διευθύνσεις των labels και ονόματα (.equ)
    labels, consts, pc, prog = {}, {}, 0, []
    for text, raw in lines:
        if "=" in text:                       # .equ temp = 0   ή   temp = 0
            left, right = text.split("=", 1)
            name = left.replace(".equ", " ").replace(".EQU", " ").split()
            if len(name) != 1:
                sys.exit(f"Δεν καταλαβαίνω τη γραμμή: {text}")
            consts[name[0]] = num(right)
            continue
        while ":" in text:
            lab, text = text.split(":", 1)
            labels[lab.strip()] = pc
            text = text.strip()
        if not text:
            continue
        parts = text.replace(",", " ").split()
        name = parts[0].upper()
        if name == "ORG":
            pc = num(parts[1]); prog.append(("org", pc, None, text)); continue
        if name not in OPS:
            sys.exit(f"Άγνωστη εντολή: {text}")
        prog.append((name, pc, parts[1] if len(parts) > 1 else None, text))
        pc += 2 if OPS[name][1] == "a" else 1
    # 2ο πέρασμα: παραγωγή hex
    for name, pc, arg, text in prog:
        if name == "org":
            print(f"@{pc:02X}"); continue
        op, kind = OPS[name]
        if kind == "n":
            if arg is None: sys.exit(f"Λείπει ο αριθμός: {text}")
            if arg in labels:
                sys.exit(f"Το '{arg}' είναι ετικέτα του προγράμματος, όχι θέση της RAM. Όρισέ το με:  {arg} = 0   ({text})")
            try:
                v = consts[arg] if arg in consts else num(arg)
            except ValueError:
                sys.exit(f"Άγνωστο όνομα '{arg}'. Όρισέ το με:  {arg} = 0   ({text})")
            if not 0 <= v <= 15: sys.exit(f"Ο αριθμός πρέπει να είναι 0-15: {text}")
            if name == "WAIT" and v == 0: sys.exit(f"Το WAIT θέλει αριθμό 1-15: {text}")
            print(f"{op:X}{v:X}       // {pc:02X}: {text}")
        elif kind == "-":
            print(f"{op:X}0       // {pc:02X}: {text}")
        else:
            if arg is None: sys.exit(f"Λείπει η διεύθυνση: {text}")
            try:
                a = labels[arg] if arg in labels else num(arg)
            except ValueError:
                sys.exit(f"Άγνωστη ετικέτα '{arg}'  ({text})")
            print(f"{op:X}0 {a:02X}    // {pc:02X}: {text}")

if __name__ == "__main__":
    main(sys.argv[1])
