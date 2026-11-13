## How it works

TH-4 is a small 4-bit microcontroller designed from scratch.

- **Registers:** accumulator `A` (4 bits), loop register `B` (4 bits), zero flag `Z`, program counter `PC` (8 bits).
- **RAM:** 16 locations of 4 bits, on chip. Not cleared by reset.
- **Program memory:** external, up to 256 bytes. The chip drives the program counter on `uo_out[7:0]` and reads the instruction byte on `ui_in[7:0]`.
- **I/O:** a 4-bit input port on `uio[3:0]` and a 4-bit latched output port on `uio[7:4]`.
- **Timer:** 25 bits. It counts only while a `WAIT` instruction executes, to save power.

Every instruction is one byte: upper 4 bits opcode, lower 4 bits a number `n` (0-15).
Jumps take a second byte with the target address. One-byte instructions take 1 cycle, jumps 2.

| Hex     | Instruction | Operation               | Sets Z |
|---------|-------------|-------------------------|--------|
| `0n`    | `LOAD n`    | A = n                   | yes    |
| `1n`    | `ADD n`     | A = A + n               | yes    |
| `2n`    | `SUB n`     | A = A - n               | yes    |
| `3n`    | `AND n`     | A = A AND n             | yes    |
| `40`    | `IN`        | A = input port          | yes    |
| `50`    | `OUT`       | output port = A         | no     |
| `60 aa` | `JUMP aa`   | PC = aa                 | no     |
| `70 aa` | `JZ aa`     | if Z = 1 then PC = aa   | no     |
| `8n`    | `STORE n`   | RAM[n] = A              | no     |
| `9n`    | `LOADM n`   | A = RAM[n]              | yes    |
| `An`    | `LDB n`     | B = n                   | no     |
| `B0`    | `DECB`      | B = B - 1               | yes    |
| `C0 aa` | `JNZ aa`    | if Z = 0 then PC = aa   | no     |
| `Dn`    | `ADDM n`    | A = A + RAM[n]          | yes    |
| `En`    | `SUBM n`    | A = A - RAM[n]          | yes    |
| `F0`    | `TAB`       | B = A                   | no     |
| `Fn`    | `WAIT n`    | wait 2^(n+9) + 2 cycles (n = 1..15) | no |

Example, a counter on the output port with a timer delay:

```
        LOAD 0
loop:   OUT
        WAIT 13         ; 0.42 s at 10 MHz
        ADD 1
        JUMP loop
```

Machine code: `00 50 FD 11 60 01`.

## How to test

1. Connect a program memory: address inputs to `uo_out[7:0]`, data outputs to `ui_in[7:0]`.
   It must answer combinationally (a parallel EEPROM, or a microcontroller emulating one).
2. Load the program bytes starting at address 0.
3. Apply the clock, hold `rst_n` low for at least one cycle, then release it. Execution starts at address 0.
4. Watch the output port on `uio[7:4]`.

The cocotb test runs a self-test program that uses every instruction and the timer.
With the input port at 10 it must write 8, 4, 10, 12, 2, 6, 10, 7, 9 to the output port.

## External hardware

- Program memory with 8 address inputs and 8 data outputs (parallel EEPROM, or a microcontroller acting as ROM).
- 4 LEDs with resistors on `uio[7:4]`, and optionally 4 switches or buttons on `uio[3:0]`.
