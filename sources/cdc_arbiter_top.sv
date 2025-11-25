`timescale 1ns/1ps

module cdc_arbiter_top #(
  parameter int N     = 5,
  parameter int WIDTH = 8,
  parameter int DELAY = 2
) (
  input  logic                     clk_s,
  input  logic                     reset_s,

  input  logic [N-1:0]             valid_s,
  input  logic [N-1:0][WIDTH-1:0]  data_s,
  output logic [N-1:0]             ready_s,

  input  logic                     clk_d,
  input  logic                     reset_d,

  input  logic                     ready_in,
  output logic                     valid_out,
  output logic [WIDTH-1:0]         data_out
);

  logic [N-1:0]             valid_d_vec;
  logic [N-1:0][WIDTH-1:0]  data_d_vec;
  logic [N-1:0]             ready_d_vec;

  // Instantiate CDC modules

  // Instantiate priority arbiter

endmodule
