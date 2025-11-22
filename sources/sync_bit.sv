`timescale 1ns/1ps
module sync_bit #(
    parameter int DELAY = 2
) (
    input  logic clk_d,
    input  logic rst,
    input  logic in_s,
    output logic out_d
);

  logic [DELAY-1:0] signal_pipe;

  always_ff @(posedge clk_d) begin
      if (rst) begin
          signal_pipe <= '0;
      end else begin
          signal_pipe <= { signal_pipe[DELAY-2:0], in_s };
      end
  end

  assign out_d = signal_pipe[DELAY-1];
endmodule
