`timescale 1ns/1ps
`default_nettype none

// Τρέχει ΟΠΟΙΟΔΗΠΟΤΕ πρόγραμμα από το prog.hex και δείχνει τι κάνει ο TH-4.
//   vvp run                      -> 60 παλμοί, θύρα εισόδου = 0
//   vvp run +cycles=200          -> 200 παλμοί
//   vvp run +in=5                -> θύρα εισόδου = 5 (0101)
module run;
    reg        clk   = 0;
    reg        rst_n = 0;
    integer    cycles  = 60;
    integer    port_in = 0;
    wire [7:0] addr, uio_out, uio_oe;

    reg [7:0] rom [0:255];
    integer k;
    initial begin
        for (k = 0; k < 256; k = k + 1) rom[k] = 8'h00;
        $readmemh("prog.hex", rom);
    end

    tt_um_th4 dut (
        .ui_in(rom[addr]), .uo_out(addr),
        .uio_in({4'b0, port_in[3:0]}), .uio_out(uio_out), .uio_oe(uio_oe),
        .ena(1'b1), .clk(clk), .rst_n(rst_n)
    );

    always #50 clk = ~clk;

    `include "th4_disasm.vh"

    initial begin
        if (!$value$plusargs("cycles=%d", cycles))   cycles  = 60;
        if (!$value$plusargs("in=%d", port_in)) port_in = 0;
        $dumpfile("run.vcd");
        $dumpvars(0, run);
        repeat (3) @(posedge clk);
        rst_n = 1;
        repeat (cycles) @(posedge clk);
        #10 $display("\n(stopped after %0d clock pulses)", cycles);
        $finish;
    end
endmodule
