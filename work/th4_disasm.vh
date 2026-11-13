// Κοινό κομμάτι για tb.v και run.v: τυπώνει τι εκτελεί ο TH-4.
// Χρειάζεται: clk, rst_n, addr, rom, uio_out και το chip με όνομα dut.
    reg [8*10:1] txt;
    reg [7:0]    pc_now, pc_prev = 8'hFF;
    integer      same = 0;
    always @(posedge clk) if (rst_n && dut.state == 0) begin
        pc_now = addr;
        case (rom[addr][7:4])
            4'h0: $sformat(txt, "LOAD  %0d", rom[addr][3:0]);
            4'h1: $sformat(txt, "ADD   %0d", rom[addr][3:0]);
            4'h2: $sformat(txt, "SUB   %0d", rom[addr][3:0]);
            4'h3: $sformat(txt, "AND   %0d", rom[addr][3:0]);
            4'h4: txt = "IN";
            4'h5: txt = "OUT";
            4'h6: $sformat(txt, "JUMP  %h", rom[addr + 8'd1]);
            4'h7: $sformat(txt, "JZ    %h", rom[addr + 8'd1]);
            4'h8: $sformat(txt, "STORE %0d", rom[addr][3:0]);
            4'h9: $sformat(txt, "LOADM %0d", rom[addr][3:0]);
            4'hA: $sformat(txt, "LDB   %0d", rom[addr][3:0]);
            4'hB: txt = "DECB";
            4'hC: $sformat(txt, "JNZ   %h", rom[addr + 8'd1]);
            4'hD: $sformat(txt, "ADDM  %0d", rom[addr][3:0]);
            4'hE: $sformat(txt, "SUBM  %0d", rom[addr][3:0]);
            4'hF: if (rom[addr][3:0] == 0) txt = "TAB"; else $sformat(txt, "WAIT  %0d", rom[addr][3:0]);
        endcase
        #1;
        same = (pc_now == pc_prev) ? same + 1 : 0;
        if (same < 1)     // ένα "JUMP στον εαυτό του" το γράφουμε μία φορά
            $display("PC=%h  %-9s ->  A=%2d  B=%2d  Z=%b  OUT=%b",
                     pc_now, txt, dut.A, dut.B, dut.Z, uio_out[7:4]);
        pc_prev = pc_now;
    end
