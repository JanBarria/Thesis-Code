################################################################################
# Constraints File: pynq_z2_single_board.xdc
# Target: PYNQ-Z2 (xc7z020clg400-1) — single-board hybrid design
# Description: NO external pin constraints needed.
#
# Why this file is mostly empty:
#   The single-board design has zero external I/O signals from the PL fabric.
#   All communication between PS and PL happens over the internal AXI bus
#   (via AXI GPIO IPs). The PL clock comes from the Zynq PS's FCLK_CLK0,
#   which Vivado auto-constrains from the block design — no manual
#   create_clock needed.
#
# If you used the original pynq_z2.xdc (dual-board version) and got errors:
#   - "Cannot set property 'BITSTREAM.CONFIG.CONFIGRATE'" → wrong property name
#   - "create_clock: No valid object(s) found for FCLK_CLK0" → block design
#     hierarchy uses different naming than expected
#   - "BUFBIDI_INOUT0 conflict on PS_CLK" → manual create_clock conflicts
#     with auto-generated PS constraints
#   ...delete that file and use this one instead.
################################################################################

# Bitstream compression — keeps the .bit file smaller for faster transfer
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

# I/O bank voltages for unused I/O (silences DRC warnings)
set_property CONFIG_VOLTAGE 3.3 [current_design]
set_property CFGBVS VCCO     [current_design]

################################################################################
# That's it. No pin assignments, no manual clock constraints.
# Vivado handles everything else from the block design.
################################################################################
