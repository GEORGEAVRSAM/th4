`default_nettype none

// =====================================================================
//  TH-4 v1.2 : 4-bit μικροελεγκτής με timer που τρέχει μόνο όταν χρειάζεται
// =====================================================================
//  Registers : A (4 bit), B (4 bit), Z (flag), PC (8 bit)
//  RAM       : 16 θέσεις x 4 bit  (δεν μηδενίζεται στο reset)
//  Πρόγραμμα : εξωτερική μνήμη, 256 bytes
//
//  Εντολές (8 bits: [7:4] = opcode, [3:0] = n)
//    0n     LOAD  n    A <- n                 Z
//    1n     ADD   n    A <- A + n             Z
//    2n     SUB   n    A <- A - n             Z
//    3n     AND   n    A <- A & n             Z
//    40     IN         A <- θύρα εισόδου      Z
//    50     OUT        θύρα εξόδου <- A
//    60 aa  JUMP  aa   PC <- aa
//    70 aa  JZ    aa   αν Z=1: PC <- aa
//    8n     STORE n    RAM[n] <- A
//    9n     LOADM n    A <- RAM[n]            Z
//    An     LDB   n    B <- n
//    B0     DECB       B <- B - 1             Z
//    C0 aa  JNZ   aa   αν Z=0: PC <- aa
//    Dn     ADDM  n    A <- A + RAM[n]        Z
//    En     SUBM  n    A <- A - RAM[n]        Z
//    F0     TAB        B <- A
//    Fn     WAIT  n    (n = 1..15) περίμενε έναν χτύπο του timer
//
//  Timer: μετρητής 25 bit που τρέχει ΜΟΝΟ όσο εκτελείται ένα WAIT (για
//  οικονομία ρεύματος: όταν δεν μετράει, τα flip-flops του δεν αλλάζουν).
//  Το WAIT n μηδενίζει τον timer και σταματάει το πρόγραμμα μέχρι να
//  ανέβει το bit (n+9), δηλαδή για 2^(n+9) παλμούς ρολογιού:
//      WAIT 1  = 1.024 παλμοί        (0,1 ms στα 10 MHz)
//      WAIT 11 = 1.048.576 παλμοί    (0,1 s  στα 10 MHz)
//      WAIT 13 = 4.194.304 παλμοί    (0,42 s στα 10 MHz)
//      WAIT 15 = 16.777.216 παλμοί   (1,68 s στα 10 MHz)
//  Κάθε WAIT κρατάει ακριβώς τον ίδιο χρόνο (+2 παλμούς για την εντολή).
//
//  Πόδια:
//    uo_out[7:0]  -> διεύθυνση προς τη μνήμη προγράμματος (PC)
//    ui_in[7:0]   <- εντολή από τη μνήμη προγράμματος
//    uio[3:0]     <- θύρα εισόδου  port_in  (π.χ. 4 κουμπιά)
//    uio[7:4]     -> θύρα εξόδου   port_out (π.χ. 4 LED)
// =====================================================================
module tt_um_th4 (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

    // Ονόματα για τα opcodes (σαν #define στη C)
    localparam OP_LOAD  = 4'h0, OP_ADD   = 4'h1, OP_SUB  = 4'h2, OP_AND  = 4'h3,
               OP_IN    = 4'h4, OP_OUT   = 4'h5, OP_JUMP = 4'h6, OP_JZ   = 4'h7,
               OP_STORE = 4'h8, OP_LOADM = 4'h9, OP_LDB  = 4'hA, OP_DECB = 4'hB,
               OP_JNZ   = 4'hC, OP_ADDM  = 4'hD, OP_SUBM = 4'hE, OP_TAB  = 4'hF;
    // Το opcode F είναι TAB όταν n = 0 και WAIT n όταν n = 1..15

    // Καταστάσεις της μονάδας ελέγχου
    localparam S_FETCH = 2'd0,   // διαβάζω εντολή
               S_ADDR  = 2'd1,   // διαβάζω τη διεύθυνση ενός άλματος
               S_WAIT  = 2'd2;   // περιμένω τον timer

    // ---------- Registers (flip-flops) ----------
    reg [7:0] pc;            // Program Counter
    reg [3:0] A;             // Accumulator
    reg [3:0] B;             // δεύτερος register (μετρητής βρόχων)
    reg       Z;             // Zero flag
    reg [3:0] port_out;      // καταχωρητής της θύρας εξόδου
    reg [1:0] state;         // S_FETCH, S_ADDR ή S_WAIT
    reg [3:0] jop;           // θυμάται ποιο jump περιμένει τη διεύθυνσή του
    reg [3:0] ram [0:15];    // RAM 16 x 4 bit
    reg [24:0] timer;        // timer: μετράει παλμούς ρολογιού μόνο μέσα σε WAIT

    // ---------- Αποκωδικοποίηση της εντολής ----------
    wire [3:0] op      = ui_in[7:4];
    wire [3:0] n       = ui_in[3:0];
    wire [3:0] port_in = uio_in[3:0];
    wire [3:0] m       = ram[n];         // η θέση της RAM που δείχνει το n

    // ---------- ALU: υπολογίζει τη νέα τιμή του A ----------
    reg [3:0] res;
    always @(*) begin
        case (op)
            OP_LOAD:  res = n;
            OP_ADD:   res = A + n;
            OP_SUB:   res = A - n;
            OP_AND:   res = A & n;
            OP_IN:    res = port_in;
            OP_LOADM: res = m;
            OP_ADDM:  res = A + m;
            OP_SUBM:  res = A - m;
            default:  res = A;
        endcase
    end

    wire [3:0] b_dec = B - 4'd1;

    // Το bit του timer που διαλέγει το WAIT n: bit (n + 9).
    // Όσο περιμένουμε, ο PC δεν αλλάζει, άρα το ui_in δείχνει ακόμα το ίδιο WAIT n.
    wire [4:0] tsel = {1'b0, n} + 5'd9;
    wire       tbit = timer[tsel];

    // Πηδάμε; (ισχύει στην κατάσταση 1)
    wire take = (jop == OP_JUMP) |
                (jop == OP_JZ  &  Z) |
                (jop == OP_JNZ & ~Z);

    // ---------- Μονάδα ελέγχου ----------
    always @(posedge clk) begin
        if (!rst_n) begin
            pc    <= 8'd0;
            A     <= 4'd0;
            B     <= 4'd0;
            Z     <= 1'b0;
            port_out  <= 4'd0;
            state <= S_FETCH;
            jop   <= 4'd0;
            timer <= 25'd0;
        end else if (state == S_FETCH) begin
            // ===== ΚΑΤΑΣΤΑΣΗ 0: το byte στο ui_in είναι ΕΝΤΟΛΗ =====
            pc <= pc + 8'd1;
            case (op)
                OP_LOAD, OP_ADD, OP_SUB, OP_AND, OP_IN,
                OP_LOADM, OP_ADDM, OP_SUBM: begin
                    A <= res;
                    Z <= (res == 4'd0);
                end
                OP_OUT:   port_out   <= A;
                OP_STORE: ram[n] <= A;
                OP_LDB:   B      <= n;
                OP_TAB: begin
                    if (n == 4'd0) begin
                        B <= A;                 // F0 = TAB
                    end else begin              // Fn = WAIT n
                        timer <= 25'd0;         // ο timer ξεκινάει από 0
                        state <= S_WAIT;
                        pc    <= pc;            // μένουμε στην ίδια εντολή όσο περιμένουμε
                    end
                end
                OP_DECB: begin
                    B <= b_dec;
                    Z <= (b_dec == 4'd0);
                end
                OP_JUMP, OP_JZ, OP_JNZ: begin
                    jop   <= op;
                    state <= S_ADDR;
                end
                default: ;
            endcase
        end else if (state == S_ADDR) begin
            // ===== ΚΑΤΑΣΤΑΣΗ 1: το byte στο ui_in είναι ΔΙΕΥΘΥΝΣΗ =====
            pc    <= take ? ui_in : pc + 8'd1;
            state <= S_FETCH;
        end else begin
            // ===== ΚΑΤΑΣΤΑΣΗ 2: WAIT, ο timer μετράει μέχρι να ανέβει το bit του =====
            if (tbit) begin
                pc    <= pc + 8'd1;             // τέλος αναμονής, ο timer σταματάει
                state <= S_FETCH;
            end else begin
                timer <= timer + 25'd1;
            end
        end
    end

    // ---------- Έξοδοι ----------
    assign uo_out  = pc;
    assign uio_out = {port_out, 4'b0000};
    assign uio_oe  = 8'b1111_0000;     // σαν DDR = 0xF0

    wire _unused = &{ena, uio_in[7:4], 1'b0};

endmodule
