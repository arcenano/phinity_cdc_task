`timescale 1ns/1ps

module top #(
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

  genvar i;
  generate
    for (i = 0; i < N; i++) begin : g_cdc
      cdc #(
        .WIDTH(WIDTH),
        .DELAY(DELAY)
      ) u_cdc (
        .clk_s   (clk_s),
        .reset_s (reset_s),
        .valid_s (valid_s[i]),
        .data_s  (data_s[i]),
        .ready_s (ready_s[i]),

        .clk_d   (clk_d),
        .reset_d (reset_d),
        .ready_d (ready_d_vec[i]),
        .data_d  (data_d_vec[i]),
        .valid_d (valid_d_vec[i])
      );
    end
  endgenerate

  priority_arbiter #(
    .N    (N),
    .WIDTH(WIDTH)
  ) u_arb (
    .clk       (clk_d),
    .rst       (reset_d),

    .valid_in  (valid_d_vec),
    .data_in   (data_d_vec),
    .ready_out (ready_d_vec),

    .data_out  (data_out),
    .valid_out (valid_out),
    .ready_in  (ready_in)
  );

endmodule
