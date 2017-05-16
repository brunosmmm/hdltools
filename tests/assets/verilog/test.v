module my_module
  #(
    parameter integer MY_PARAM_0 = 0,
    parameter integer MY_PARAM_1 = 1,
    parameter integer MY_PARAM_2 = 2,
    parameter integer DATA_WIDTH = 8
    )
  (
   input wire clk,
   input wire rst,

   output reg A,
   output wire [7:0] B,
   output wire [(MY_PARAM_0-MY_PARAM_1)+MY_PARAM_2+1:0] C,
   input wire [$clog2(DATA_WIDTH)-1:0] D
   );

   //rest gets ignored for now!
   wire                        test;

endmodule
