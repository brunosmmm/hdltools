module my_module
  (
   input wire clk,
   input wire rst,

   output reg A,
   output wire [7:0] B,
   output wire [SOME_EXPR-1:0] C
   );

   //rest gets ignored for now!
   wire                        test;

endmodule
