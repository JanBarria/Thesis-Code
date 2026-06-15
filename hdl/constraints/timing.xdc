# Constrain our input clock pin to a stable 40 MHz (25.0 ns period)
create_clock -period 25.000 -name master_clk [get_ports clk_pin]