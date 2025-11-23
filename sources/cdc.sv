`timescale 1ns/1ps
module cdc #(
  parameter int WIDTH = 8,
  parameter int DELAY = 2
) (
  input  wire  clk_s,
  input  wire  reset_s,
  input  wire  valid_s,
  input  logic [WIDTH-1:0]  data_s,
  output logic  ready_s,

  input  wire  clk_d,
  input  wire  reset_d,
  input  wire  ready_d,
  output logic [WIDTH-1:0]  data_d,
  output logic valid_d
);

// Insert CDC logic

endmodule
