--Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
--Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
----------------------------------------------------------------------------------
--Tool Version: Vivado v.2024.1 (win64) Build 5076996 Wed May 22 18:37:14 MDT 2024
--Date        : Tue Jun 16 20:11:13 2026
--Host        : DESKTOP-S8524M5 running 64-bit major release  (build 9200)
--Command     : generate_target chaos_design_wrapper.bd
--Design      : chaos_design_wrapper
--Purpose     : IP block netlist
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
library UNISIM;
use UNISIM.VCOMPONENTS.ALL;
entity chaos_design_wrapper is
  port (
    DDR_addr : inout STD_LOGIC_VECTOR ( 14 downto 0 );
    DDR_ba : inout STD_LOGIC_VECTOR ( 2 downto 0 );
    DDR_cas_n : inout STD_LOGIC;
    DDR_ck_n : inout STD_LOGIC;
    DDR_ck_p : inout STD_LOGIC;
    DDR_cke : inout STD_LOGIC;
    DDR_cs_n : inout STD_LOGIC;
    DDR_dm : inout STD_LOGIC_VECTOR ( 3 downto 0 );
    DDR_dq : inout STD_LOGIC_VECTOR ( 31 downto 0 );
    DDR_dqs_n : inout STD_LOGIC_VECTOR ( 3 downto 0 );
    DDR_dqs_p : inout STD_LOGIC_VECTOR ( 3 downto 0 );
    DDR_odt : inout STD_LOGIC;
    DDR_ras_n : inout STD_LOGIC;
    DDR_reset_n : inout STD_LOGIC;
    DDR_we_n : inout STD_LOGIC;
    FCLK_CLK0 : out STD_LOGIC;
    FIXED_IO_ddr_vrn : inout STD_LOGIC;
    FIXED_IO_ddr_vrp : inout STD_LOGIC;
    FIXED_IO_mio : inout STD_LOGIC_VECTOR ( 53 downto 0 );
    FIXED_IO_ps_clk : inout STD_LOGIC;
    FIXED_IO_ps_porb : inout STD_LOGIC;
    FIXED_IO_ps_srstb : inout STD_LOGIC;
    gpio_rtl_0_tri_o : out STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_10_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_11_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_12_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_13_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_1_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_2_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_3_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_4_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_5_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_6_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_7_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_8_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_9_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 )
  );
end chaos_design_wrapper;

architecture STRUCTURE of chaos_design_wrapper is
  component chaos_design is
  port (
    DDR_cas_n : inout STD_LOGIC;
    DDR_cke : inout STD_LOGIC;
    DDR_ck_n : inout STD_LOGIC;
    DDR_ck_p : inout STD_LOGIC;
    DDR_cs_n : inout STD_LOGIC;
    DDR_reset_n : inout STD_LOGIC;
    DDR_odt : inout STD_LOGIC;
    DDR_ras_n : inout STD_LOGIC;
    DDR_we_n : inout STD_LOGIC;
    DDR_ba : inout STD_LOGIC_VECTOR ( 2 downto 0 );
    DDR_addr : inout STD_LOGIC_VECTOR ( 14 downto 0 );
    DDR_dm : inout STD_LOGIC_VECTOR ( 3 downto 0 );
    DDR_dq : inout STD_LOGIC_VECTOR ( 31 downto 0 );
    DDR_dqs_n : inout STD_LOGIC_VECTOR ( 3 downto 0 );
    DDR_dqs_p : inout STD_LOGIC_VECTOR ( 3 downto 0 );
    FIXED_IO_mio : inout STD_LOGIC_VECTOR ( 53 downto 0 );
    FIXED_IO_ddr_vrn : inout STD_LOGIC;
    FIXED_IO_ddr_vrp : inout STD_LOGIC;
    FIXED_IO_ps_srstb : inout STD_LOGIC;
    FIXED_IO_ps_clk : inout STD_LOGIC;
    FIXED_IO_ps_porb : inout STD_LOGIC;
    gpio_rtl_0_tri_o : out STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_1_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_2_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_3_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_4_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_5_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_6_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_7_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_8_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_9_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_10_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_11_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_12_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    gpio_rtl_13_tri_i : in STD_LOGIC_VECTOR ( 31 downto 0 );
    FCLK_CLK0 : out STD_LOGIC
  );
  end component chaos_design;
begin
chaos_design_i: component chaos_design
     port map (
      DDR_addr(14 downto 0) => DDR_addr(14 downto 0),
      DDR_ba(2 downto 0) => DDR_ba(2 downto 0),
      DDR_cas_n => DDR_cas_n,
      DDR_ck_n => DDR_ck_n,
      DDR_ck_p => DDR_ck_p,
      DDR_cke => DDR_cke,
      DDR_cs_n => DDR_cs_n,
      DDR_dm(3 downto 0) => DDR_dm(3 downto 0),
      DDR_dq(31 downto 0) => DDR_dq(31 downto 0),
      DDR_dqs_n(3 downto 0) => DDR_dqs_n(3 downto 0),
      DDR_dqs_p(3 downto 0) => DDR_dqs_p(3 downto 0),
      DDR_odt => DDR_odt,
      DDR_ras_n => DDR_ras_n,
      DDR_reset_n => DDR_reset_n,
      DDR_we_n => DDR_we_n,
      FCLK_CLK0 => FCLK_CLK0,
      FIXED_IO_ddr_vrn => FIXED_IO_ddr_vrn,
      FIXED_IO_ddr_vrp => FIXED_IO_ddr_vrp,
      FIXED_IO_mio(53 downto 0) => FIXED_IO_mio(53 downto 0),
      FIXED_IO_ps_clk => FIXED_IO_ps_clk,
      FIXED_IO_ps_porb => FIXED_IO_ps_porb,
      FIXED_IO_ps_srstb => FIXED_IO_ps_srstb,
      gpio_rtl_0_tri_o(31 downto 0) => gpio_rtl_0_tri_o(31 downto 0),
      gpio_rtl_10_tri_i(31 downto 0) => gpio_rtl_10_tri_i(31 downto 0),
      gpio_rtl_11_tri_i(31 downto 0) => gpio_rtl_11_tri_i(31 downto 0),
      gpio_rtl_12_tri_i(31 downto 0) => gpio_rtl_12_tri_i(31 downto 0),
      gpio_rtl_13_tri_i(31 downto 0) => gpio_rtl_13_tri_i(31 downto 0),
      gpio_rtl_1_tri_i(31 downto 0) => gpio_rtl_1_tri_i(31 downto 0),
      gpio_rtl_2_tri_i(31 downto 0) => gpio_rtl_2_tri_i(31 downto 0),
      gpio_rtl_3_tri_i(31 downto 0) => gpio_rtl_3_tri_i(31 downto 0),
      gpio_rtl_4_tri_i(31 downto 0) => gpio_rtl_4_tri_i(31 downto 0),
      gpio_rtl_5_tri_i(31 downto 0) => gpio_rtl_5_tri_i(31 downto 0),
      gpio_rtl_6_tri_i(31 downto 0) => gpio_rtl_6_tri_i(31 downto 0),
      gpio_rtl_7_tri_i(31 downto 0) => gpio_rtl_7_tri_i(31 downto 0),
      gpio_rtl_8_tri_i(31 downto 0) => gpio_rtl_8_tri_i(31 downto 0),
      gpio_rtl_9_tri_i(31 downto 0) => gpio_rtl_9_tri_i(31 downto 0)
    );
end STRUCTURE;
