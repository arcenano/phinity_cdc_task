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

  logic en_s;
  logic en_latch_s;
  logic ack_s;
  logic ack_ff_s;
  logic ack_fedge;
  logic [WIDTH-1:0] data_latch_s;

  logic en_d;
  logic en_prev_d;
  wire  en_redge;
  logic ack_d;
  logic ack_latch_d;

  always_comb begin
    en_s = (reset_s) ? (0) : (valid_s && ready_s);
    ack_fedge =  !ack_s && ack_ff_s;
  end

  always_ff @(posedge clk_s) begin
    if (reset_s) begin
      data_latch_s <= '0;
      ack_ff_s <= '0;
      ready_s <= 1'b1;
      en_latch_s <= '0;
    end else begin
      if (en_s) begin
        data_latch_s <= data_s;
        ready_s <= '0;
        en_latch_s <= '1;
      end else begin
        ready_s <= ack_fedge | ready_s;
        en_latch_s <= en_latch_s && !ack_s;
      end
      ack_ff_s <= ack_s;
    end
  end

    sync_bit #(
    .DELAY(DELAY)
    ) sync_dst_2_src_i (
    .in_s (ack_latch_d),
    .rst(reset_s),
    .clk_d(clk_s),
    .out_d(ack_s)
  );

  assign en_redge =  en_d && !en_prev_d;

  always_ff @(posedge clk_d) begin
    if (reset_d) begin
      data_d    <= '0;
      en_prev_d <= '0;
      valid_d <= '0;
      ack_d <= '0;
      ack_latch_d <= '0;
    end else begin
      if (en_redge) begin
        data_d <= data_latch_s;
        valid_d <= 1;
      end else begin
        valid_d <= valid_d && !ready_d;
      end
      ack_d <= valid_d && ready_d;
      ack_latch_d <= ack_d | (ack_latch_d && en_d);

      en_prev_d <= en_d;
    end
  end

  sync_bit #(
    .DELAY(DELAY)
  ) sync_src_2_dst_i (
    .in_s (en_latch_s),
    .rst(reset_d),
    .clk_d(clk_d),
    .out_d(en_d)
  );
endmodule
