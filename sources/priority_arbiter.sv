`timescale 1ns/1ps
module priority_arbiter #(
  parameter int N     = 5,
  parameter int WIDTH = 8
) (
  input  logic                    clk,
  input  logic                    rst,

  input  logic [N-1:0]            valid_in,
  input  logic [N-1:0][WIDTH-1:0] data_in,
  output logic [N-1:0]            ready_out,

  output logic [WIDTH-1:0]        data_out,
  output logic                    valid_out,
  input  logic                    ready_in
);

  logic                 latch;
  logic                 bus;

  logic [$clog2(N)-1:0] sel, sel_ff;

  logic [N-1:0]         ready_out_d;

  assign latch = (|ready_out) && valid_in[sel_ff];
  assign busy = latch | (busy && !ready_in);

  always_comb begin
    ready_out_d = '0;
    if (!busy) begin
      ready_out_d[sel] = 1'b1;
    end
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      ready_out  <= '0;
      valid_out <= '0;
      data_out <= '0;
    end else begin
      ready_out  <= ready_out_d;
      if(latch)begin
        valid_out <= 1'b1;
        data_out <= data_in[sel_ff];
      end else begin
        valid_out <= valid_out && !ready_in;
      end
    end
  end

  always_ff @(posedge clk) begin
    if (rst) begin
      sel  <= '0;
      sel_ff <= '0;
    end else begin
      if(!busy) begin
        sel_ff <= sel;
        if (sel == N-1)
          sel <= '0;
        else
          sel <= sel + 1;
      end
    end
  end
endmodule
