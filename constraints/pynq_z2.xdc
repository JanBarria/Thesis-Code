################################################################################
# Constraints File: pynq_z2.xdc
# Target: PYNQ-Z2 Board (xc7z020clg400-1)
# Description: Pin assignments and timing constraints for chaos synchronization
################################################################################

# PMOD A Pin Assignments (JA connector)
# Physical wiring:
#   Board1 JA1 (TX) -> Board2 JA2 (RX)
#   Board1 JA2 (RX) -> Board2 JA1 (TX)
#   Board1 JA5 (GND) - Board2 JA5 (GND)

# PMOD JA Pin 1 - UART TX (output from this board)
set_property PACKAGE_PIN Y18 [get_ports uart_txd]
set_property IOSTANDARD LVCMOS33 [get_ports uart_txd]

# PMOD JA Pin 2 - UART RX (input to this board)
set_property PACKAGE_PIN Y19 [get_ports uart_rxd]
set_property IOSTANDARD LVCMOS33 [get_ports uart_rxd]

# Note: Pins 3,4,7,8 of PMOD JA are available for future expansion
# Pin 5,11 are GND, Pin 6,12 are VCC

################################################################################
# Timing Constraints
################################################################################

# PL Clock from PS (FCLK_CLK0) - 100 MHz
create_clock -period 10.000 -name clk_pl -waveform {0.000 5.000} [get_pins system_i/processing_system7_0/inst/FCLK_CLK0]

# Input delay for UART RX (assume 5ns from external source)
set_input_delay -clock clk_pl -max 5.000 [get_ports uart_rxd]
set_input_delay -clock clk_pl -min 1.000 [get_ports uart_rxd]

# Output delay for UART TX (assume 5ns to external destination)
set_output_delay -clock clk_pl -max 5.000 [get_ports uart_txd]
set_output_delay -clock clk_pl -min 1.000 [get_ports uart_txd]

# False paths for asynchronous signals
# UART is asynchronous to system clock, handled by PS UART controller
set_false_path -from [get_ports uart_rxd]
set_false_path -to [get_ports uart_txd]

################################################################################
# Additional Constraints
################################################################################

# Bitstream configuration
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
set_property BITSTREAM.CONFIG.CONFIGRATE 50 [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO [current_design]

# DRC waivers (if needed)
# set_property SEVERITY {Warning} [get_drc_checks NSTD-1]
# set_property SEVERITY {Warning} [get_drc_checks UCIO-1]