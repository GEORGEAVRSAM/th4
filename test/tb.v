`default_nettype none
`timescale 1ns / 1ps

/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
*/
module tb ();

  // Dump the signals to a FST file. You can view it with gtkwave or surfer.
  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb);
    #1;
  end

  // Wire up the inputs and outputs:
  reg clk;
  reg rst_n;
  reg ena;
  wire [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif

  // External program memory (ROM) for the TH-4. The CPU drives the program
  // counter on uo_out and reads the instruction byte back on ui_in.
  // Contents: the self-test program (selftest.asm). It uses every instruction
  // and the timer, and writes 8, 4, 10, 12, 2, 6, 10, 7, 9 to the output port.
  reg [7:0] rom [0:255];
  integer k;
  initial begin
    for (k = 0; k < 256; k = k + 1) rom[k] = 8'h00;
    rom[8'h00] = 8'h05;   // LOAD 5
    rom[8'h01] = 8'h13;   // ADD 3
    rom[8'h02] = 8'h50;   // OUT
    rom[8'h03] = 8'h28;   // SUB 8
    rom[8'h04] = 8'h70;   // JZ ok1
    rom[8'h05] = 8'h08;
    rom[8'h06] = 8'h60;   // JUMP fail
    rom[8'h07] = 8'h36;
    rom[8'h08] = 8'h0C;   // LOAD 12
    rom[8'h09] = 8'h36;   // AND 6
    rom[8'h0A] = 8'h50;   // OUT
    rom[8'h0B] = 8'h40;   // IN
    rom[8'h0C] = 8'h50;   // OUT
    rom[8'h0D] = 8'h83;   // STORE 3
    rom[8'h0E] = 8'h02;   // LOAD 2
    rom[8'h0F] = 8'h87;   // STORE 7
    rom[8'h10] = 8'h93;   // LOADM 3
    rom[8'h11] = 8'hD7;   // ADDM 7
    rom[8'h12] = 8'h50;   // OUT
    rom[8'h13] = 8'hE3;   // SUBM 3
    rom[8'h14] = 8'h50;   // OUT
    rom[8'h15] = 8'hE7;   // SUBM 7
    rom[8'h16] = 8'hC0;   // JNZ fail
    rom[8'h17] = 8'h36;
    rom[8'h18] = 8'hA3;   // LDB 3
    rom[8'h19] = 8'h00;   // LOAD 0
    rom[8'h1A] = 8'h12;   // ADD 2
    rom[8'h1B] = 8'hB0;   // DECB
    rom[8'h1C] = 8'hC0;   // JNZ lp1
    rom[8'h1D] = 8'h1A;
    rom[8'h1E] = 8'h50;   // OUT
    rom[8'h1F] = 8'h02;   // LOAD 2
    rom[8'h20] = 8'hF0;   // TAB
    rom[8'h21] = 8'h00;   // LOAD 0
    rom[8'h22] = 8'h15;   // ADD 5
    rom[8'h23] = 8'hB0;   // DECB
    rom[8'h24] = 8'hC0;   // JNZ lp2
    rom[8'h25] = 8'h22;
    rom[8'h26] = 8'h50;   // OUT
    rom[8'h27] = 8'h01;   // LOAD 1
    rom[8'h28] = 8'h70;   // JZ fail
    rom[8'h29] = 8'h36;
    rom[8'h2A] = 8'hC0;   // JNZ ok2
    rom[8'h2B] = 8'h2E;
    rom[8'h2C] = 8'h60;   // JUMP fail
    rom[8'h2D] = 8'h36;
    rom[8'h2E] = 8'h07;   // LOAD 7
    rom[8'h2F] = 8'h50;   // OUT
    rom[8'h30] = 8'hF1;   // WAIT 1
    rom[8'h31] = 8'hF1;   // WAIT 1
    rom[8'h32] = 8'h09;   // LOAD 9
    rom[8'h33] = 8'h50;   // OUT
    rom[8'h34] = 8'h60;   // JUMP end
    rom[8'h35] = 8'h34;
    rom[8'h36] = 8'h0F;   // LOAD 15
    rom[8'h37] = 8'h50;   // OUT
    rom[8'h38] = 8'h60;   // JUMP stop
    rom[8'h39] = 8'h38;
  end
  assign ui_in = rom[uo_out];

  tt_um_georgeavrsam_th4 user_project (

      // Include power ports for the Gate Level test:
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif

      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      .ena    (ena),      // enable - goes high when design is selected
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // not reset
  );

endmodule
