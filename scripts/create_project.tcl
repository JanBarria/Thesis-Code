################################################################################
# Vivado TCL Script: create_project.tcl
# Description: Creates PYNQ-Z2 project for chaos synchronization
# Usage: vivado -mode batch -source create_project.tcl
#        Or from Vivado TCL console: source create_project.tcl
#
# Creates two project variants:
#   - chaos_sync_master: Y0=1.0, Z0=1.0, sync_enable=0
#   - chaos_sync_slave:  Y0=0.5, Z0=1.5, sync_enable=1
################################################################################

# Project configuration
set project_name "chaos_sync_master"
set project_dir "./vivado_project"
set part_name "xc7z020clg400-1"

# Get script directory
set script_dir [file dirname [file normalize [info script]]]
set hdl_dir [file normalize "$script_dir/../hdl"]
set constraints_dir [file normalize "$script_dir/../constraints"]

# Create project
create_project $project_name $project_dir -part $part_name -force
set_property board_part tul.com.tw:pynq-z2:part0:1.0 [current_project]

# Add VHDL source files
add_files -fileset sources_1 [glob $hdl_dir/*.vhd]
set_property library work [get_files [glob $hdl_dir/*.vhd]]

# Add constraints
add_files -fileset constrs_1 [glob $constraints_dir/*.xdc]

# Create block design
create_bd_design "system"

# Add Zynq PS
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7_0

# Configure Zynq PS
set_property -dict [list \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100} \
    CONFIG.PCW_USE_M_AXI_GP0 {1} \
    CONFIG.PCW_UART1_PERIPHERAL_ENABLE {1} \
    CONFIG.PCW_UART1_UART1_IO {EMIO} \
] [get_bd_cells processing_system7_0]

# Apply board preset
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset "1" Master "Disable" Slave "Disable" } \
    [get_bd_cells processing_system7_0]

# Add AXI Interconnect
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_interconnect_0
set_property -dict [list CONFIG.NUM_MI {5}] [get_bd_cells axi_interconnect_0]

# Add 5x AXI GPIO blocks
# GPIO0: Control/Status
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_0
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {32} \
    CONFIG.C_ALL_INPUTS {0} \
    CONFIG.C_ALL_OUTPUTS {0} \
    CONFIG.C_TRI_DEFAULT {0xFFFFFFFF} \
] [get_bd_cells axi_gpio_0]

# GPIO1: x_drive
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_1
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {32} \
    CONFIG.C_ALL_OUTPUTS {1} \
] [get_bd_cells axi_gpio_1]

# GPIO2: x_out
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_2
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {32} \
    CONFIG.C_ALL_INPUTS {1} \
] [get_bd_cells axi_gpio_2]

# GPIO3: y_out
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_3
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {32} \
    CONFIG.C_ALL_INPUTS {1} \
] [get_bd_cells axi_gpio_3]

# GPIO4: z_out
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 axi_gpio_4
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {32} \
    CONFIG.C_ALL_INPUTS {1} \
] [get_bd_cells axi_gpio_4]

# Connect AXI interfaces
connect_bd_intf_net [get_bd_intf_pins processing_system7_0/M_AXI_GP0] \
    [get_bd_intf_pins axi_interconnect_0/S00_AXI]

for {set i 0} {$i < 5} {incr i} {
    connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M0${i}_AXI] \
        [get_bd_intf_pins axi_gpio_${i}/S_AXI]
}

# Connect clocks
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
    [get_bd_pins processing_system7_0/M_AXI_GP0_ACLK]
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
    [get_bd_pins axi_interconnect_0/ACLK]
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
    [get_bd_pins axi_interconnect_0/S00_ACLK]

for {set i 0} {$i < 5} {incr i} {
    connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
        [get_bd_pins axi_interconnect_0/M0${i}_ACLK]
    connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
        [get_bd_pins axi_gpio_${i}/s_axi_aclk]
}

# Connect resets
connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] \
    [get_bd_pins axi_interconnect_0/ARESETN]
connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] \
    [get_bd_pins axi_interconnect_0/S00_ARESETN]

for {set i 0} {$i < 5} {incr i} {
    connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] \
        [get_bd_pins axi_interconnect_0/M0${i}_ARESETN]
    connect_bd_net [get_bd_pins processing_system7_0/FCLK_RESET0_N] \
        [get_bd_pins axi_gpio_${i}/s_axi_aresetn]
}

# Make GPIO pins external (will connect to HDL wrapper)
make_bd_pins_external [get_bd_pins axi_gpio_0/gpio_io_i]
make_bd_pins_external [get_bd_pins axi_gpio_0/gpio_io_o]
make_bd_pins_external [get_bd_pins axi_gpio_0/gpio_io_t]

make_bd_pins_external [get_bd_pins axi_gpio_1/gpio_io_i]
make_bd_pins_external [get_bd_pins axi_gpio_1/gpio_io_o]
make_bd_pins_external [get_bd_pins axi_gpio_1/gpio_io_t]

make_bd_pins_external [get_bd_pins axi_gpio_2/gpio_io_i]
make_bd_pins_external [get_bd_pins axi_gpio_2/gpio_io_o]
make_bd_pins_external [get_bd_pins axi_gpio_2/gpio_io_t]

make_bd_pins_external [get_bd_pins axi_gpio_3/gpio_io_i]
make_bd_pins_external [get_bd_pins axi_gpio_3/gpio_io_o]
make_bd_pins_external [get_bd_pins axi_gpio_3/gpio_io_t]

make_bd_pins_external [get_bd_pins axi_gpio_4/gpio_io_i]
make_bd_pins_external [get_bd_pins axi_gpio_4/gpio_io_o]
make_bd_pins_external [get_bd_pins axi_gpio_4/gpio_io_t]

# Make UART1 EMIO external
make_bd_pins_external [get_bd_pins processing_system7_0/UART1_TX]
make_bd_pins_external [get_bd_pins processing_system7_0/UART1_RX]

# Assign addresses
assign_bd_address

# Validate design
validate_bd_design
save_bd_design

# Create HDL wrapper
make_wrapper -files [get_files $project_dir/$project_name.srcs/sources_1/bd/system/system.bd] -top
add_files -norecurse $project_dir/$project_name.gen/sources_1/bd/system/hdl/system_wrapper.v
set_property top system_wrapper [current_fileset]

# Set synthesis strategy
set_property strategy Flow_PerfOptimized_high [get_runs synth_1]
set_property strategy Performance_ExplorePostRoutePhysOpt [get_runs impl_1]

puts "INFO: Project created successfully: $project_name"
puts "INFO: To synthesize and implement, run:"
puts "      launch_runs synth_1 -jobs 4"
puts "      wait_on_run synth_1"
puts "      launch_runs impl_1 -to_step write_bitstream -jobs 4"
puts "      wait_on_run impl_1"
puts ""
puts "INFO: For SLAVE variant, modify chaos_sync_top generics:"
puts "      Y0_INIT => 32768  (0.5)"
puts "      Z0_INIT => 98304  (1.5)"

# Made with Bob
