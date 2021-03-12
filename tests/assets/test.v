module test
  #(
    parameter integer x = 2,
    parameter y = 4'b0000,
    parameter z = 8'h01
    )
   (
    input         clk,
    input         rst,

    inout         sig,
    input         sig_i,
    output reg    sig_o,
    input         sig_dir,
    output wire   is_valid,
    output        dummy,

    input [2:0]   config,
    input [x-1:0] some_input
    );

endmodule
