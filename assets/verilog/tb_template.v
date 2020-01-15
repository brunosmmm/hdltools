module mytb
  #(
    parameter integer register_size = 32,
    parameter integer register_count = 32,
    parameter integer input_vector_size = 32,
    parameter integer output_vector_size = 32,
    parameter integer fifo_depth = 512,
    parameter integer saddr_w = 24
    )
  ();

   // testbench controlled signals
   reg                        logic_reset;
   reg                        clk;

   // hack: stuff all configuration registers into an array
   reg [register_size-1:0]             config_regs [0:register_count-1];
   reg [input_vector_size-1:0]         input_vector;
   wire [output_vector_size-1:0]       output_vector;

   // load configuration
   integer                    configfile, inputfile, outputfile;
   integer                    configline = 0;
   string                     configfname, inputfname, outputfname;
   initial begin
      if (!$value$plusargs("configfile=%s", configfname)) begin
         $display("FATAL: specify configuration file name with +configfile=<FILE>");
         $finish();
      end
      configfile=$fopen(configfname, "r");
      if (!configfile) begin
         $display("FATAL: could not open configuration file");
         $finish();
      end
      while (!$feof(configfile)) begin
         if (configline < register_count) begin
            $fscanf(configfile, "%h\n", config_regs[configline]);
            configline = configline + 1;
         end
         else begin
            $display("WARNING: too many values in configuration file");
         end
      end
      $display("INFO: loaded configuration");
   end

   initial begin
      $dumpfile("mytb.vcd");
      $dumpvars(0, mytb);
      input_vector <= 0;
      logic_reset <= 1;
      clk <= 0;
      #10 logic_reset <= 0;
      #10000 $finish();
   end

   // generate clock
   always begin
      #1 clk <= !clk;
   end

   // read input vector
   initial begin
      #10; //wait for reset to clear
      if (!$value$plusargs("inputfile=%s", inputfname)) begin
         $display("FATAL: specify input file name with +inputfile=<FILE>");
         $finish();
      end
      inputfile=$fopen(inputfname, "r");
      if (!inputfile) begin
         $display("FATAL: could not open input file");
         $finish();
      end
      while(!$feof(inputfile)) begin
         $fscanf(inputfile, "%h\n", input_vector);
         #2; // wait for next clock cycle
      end
      // finish simulation if we get here, as there is no more input
      $display("INFO: no more input available, terminating");
      $finish();
   end

   // write output vector
   initial begin
      if (!$value$plusargs("outputfile=%s", outputfname)) begin
         $display("WARN: using default output.txt as output file");
         outputfname = "output.txt";
      end
      outputfile=$fopen(outputfname, "w");
      if (!outputfile) begin
         $display("FATAL: could not open output file for writing");
         $finish();
      end
      while (1) begin
         $fwrite(outputfile, "%h\n", output_vector);
         #2; // wait for next clock cycle
      end
   end

   // instantiate here

endmodule
