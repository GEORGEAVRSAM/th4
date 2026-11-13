`timescale 1ns/1ps
`default_nettype none

// Αυτοέλεγχος του TH-4: τρέχει το selftest.hex και ελέγχει τη θύρα εξόδου.
module tb;
    reg        clk   = 0;
    reg        rst_n = 0;
    reg  [3:0] port_in = 4'b1010;          // η θύρα εισόδου = 10
    wire [7:0] addr, uio_out, uio_oe;

    // ---------- Η εξωτερική μνήμη προγράμματος ----------
    reg [7:0] rom [0:255];
    integer k;
    initial begin
        for (k = 0; k < 256; k = k + 1) rom[k] = 8'h00;
        $readmemh("selftest.hex", rom);
    end

    tt_um_th4 dut (
        .ui_in(rom[addr]), .uo_out(addr),
        .uio_in({4'b0, port_in}), .uio_out(uio_out), .uio_oe(uio_oe),
        .ena(1'b1), .clk(clk), .rst_n(rst_n)
    );

    always #50 clk = ~clk;

    `include "th4_disasm.vh"

    // ---------- Καταγραφή κάθε αλλαγής στη θύρα εξόδου ----------
    reg [3:0] seen [0:31];
    integer   when [0:31];      // σε ποιον παλμό έγινε η αλλαγή
    integer   nseen = 0, cyc = 0;
    reg [3:0] last_out = 0;
    always @(negedge clk) if (rst_n) cyc = cyc + 1;
    always @(negedge clk) if (rst_n && uio_out[7:4] !== last_out) begin
        seen[nseen] = uio_out[7:4];
        when[nseen] = cyc;
        nseen       = nseen + 1;
        last_out    = uio_out[7:4];
    end

    // ---------- Οι σωστές τιμές ----------
    reg [3:0] want [0:8];
    initial begin
        want[0]=8; want[1]=4; want[2]=10; want[3]=12;
        want[4]=2; want[5]=6; want[6]=10; want[7]=7; want[8]=9;
    end

    integer errors = 0, i, gap;
    initial begin
        $dumpfile("tb.vcd");
        $dumpvars(0, tb);
        repeat (3) @(posedge clk);
        rst_n = 1;
        repeat (2400) @(posedge clk);
        #10;

        $display("");
        if (uio_oe !== 8'hF0) begin
            $display("ERROR: uio_oe = %h", uio_oe); errors = errors + 1;
        end
        if (nseen !== 9) begin
            $display("ERROR: output port changed %0d times, expected 9", nseen); errors = errors + 1;
        end
        for (i = 0; i < 9 && i < nseen; i = i + 1)
            if (seen[i] !== want[i]) begin
                $display("ERROR: output value #%0d is %0d, expected %0d", i + 1, seen[i], want[i]);
                errors = errors + 1;
            end
        if (errors == 0) $display("Output sequence: 8, 4, 10, 12, 2, 6, 10, 7, 9  OK");

        // Timer: ανάμεσα στο 7 και στο 9 υπάρχουν δύο WAIT 1 (1026 παλμοί το καθένα)
        // και τα LOAD 9, OUT (2 παλμοί): σύνολο ακριβώς 2054.
        if (nseen == 9) begin
            gap = when[8] - when[7];
            if (gap != 2054) begin
                $display("ERROR: WAIT 1 + WAIT 1 took %0d clock pulses, expected 2054", gap);
                errors = errors + 1;
            end else
                $display("Timer: two WAIT 1 took %0d clock pulses  OK", gap);
        end

        if (errors == 0) $display("\n*** ALL TESTS PASSED ***");
        else             $display("\n*** %0d ERRORS ***", errors);
        $finish;
    end
endmodule
