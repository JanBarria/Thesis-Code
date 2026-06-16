----------------------------------------------------------------------------------
-- File        : top_wrapper.vhd
-- Description : Final top-level bridge connecting the Processing System (PS) 
--               AXI GPIO wrapper directly to the chaotic fabric math engine.
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity top_wrapper is
    port (
        -- Pass-through ports required by the Zynq Processing System architecture
        DDR_addr          : inout STD_LOGIC_VECTOR ( 14 downto 0 );
        DDR_ba            : inout STD_LOGIC_VECTOR ( 2 downto 0 );
        DDR_cas_n         : inout STD_LOGIC;
        DDR_ck_n          : inout STD_LOGIC;
        DDR_ck_p          : inout STD_LOGIC;
        DDR_cke           : inout STD_LOGIC;
        DDR_cs_n          : inout STD_LOGIC;
        DDR_dm            : inout STD_LOGIC_VECTOR ( 3 downto 0 );
        DDR_dq            : inout STD_LOGIC_VECTOR ( 31 downto 0 );
        DDR_dqs_n         : inout STD_LOGIC_VECTOR ( 3 downto 0 );
        DDR_dqs_p         : inout STD_LOGIC_VECTOR ( 3 downto 0 );
        DDR_odt           : inout STD_LOGIC;
        DDR_ras_n         : inout STD_LOGIC;
        DDR_reset_n       : inout STD_LOGIC;
        DDR_we_n          : inout STD_LOGIC;
        FIXED_IO_ddr_vrn  : inout STD_LOGIC;
        FIXED_IO_ddr_vrp  : inout STD_LOGIC;
        FIXED_IO_mio      : inout STD_LOGIC_VECTOR ( 53 downto 0 );
        FIXED_IO_ps_clk   : inout STD_LOGIC;
        FIXED_IO_ps_porb  : inout STD_LOGIC;
        FIXED_IO_ps_srstb : inout STD_LOGIC
    );
end entity top_wrapper;

architecture structural of top_wrapper is

    -- 1. Declare the Auto-Generated Vivado Block Design Wrapper Component
    component chaos_design_wrapper is
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
    end component chaos_design_wrapper;

    -- 2. Declare Your Team's Chaos Top Level Component
    component chaos_hybrid_single_board is
        port (
            clk_pl        : in  std_logic;
            rst_pl_n      : in  std_logic;
            gpio0_ch1_in  : in  std_logic_vector(31 downto 0);
            gpio0_ch2_out : out std_logic_vector(31 downto 0);
            gpio1_ch1_out : out std_logic_vector(31 downto 0);
            gpio1_ch2_out : out std_logic_vector(31 downto 0);
            gpio2_ch1_out : out std_logic_vector(31 downto 0);
            gpio2_ch2_out : out std_logic_vector(31 downto 0);
            gpio3_ch1_out : out std_logic_vector(31 downto 0);
            gpio3_ch2_out : out std_logic_vector(31 downto 0);
            gpio4_ch1_out : out std_logic_vector(31 downto 0);
            gpio4_ch2_out : out std_logic_vector(31 downto 0);
            gpio5_ch1_out : out std_logic_vector(31 downto 0);
            gpio5_ch2_out : out std_logic_vector(31 downto 0);
            gpio6_ch1_out : out std_logic_vector(31 downto 0);
            gpio6_ch2_out : out std_logic_vector(31 downto 0)
        );
    end component chaos_hybrid_single_board;

    -- 3. Interconnect Wires (Bridges between the two modules)
    signal W_gpio0_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio0_ch2 : std_logic_vector(31 downto 0);
    signal W_gpio1_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio1_ch2 : std_logic_vector(31 downto 0);
    signal W_gpio2_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio2_ch2 : std_logic_vector(31 downto 0);
    signal W_gpio3_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio3_ch2 : std_logic_vector(31 downto 0);
    signal W_gpio4_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio4_ch2 : std_logic_vector(31 downto 0);
    signal W_gpio5_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio5_ch2 : std_logic_vector(31 downto 0);
    signal W_gpio6_ch1 : std_logic_vector(31 downto 0);
    signal W_gpio6_ch2 : std_logic_vector(31 downto 0);

    -- Internal Clock & System Reset references extracted from the processor
    signal clk_internal : std_logic;
    signal rst_internal_n : std_logic;

begin

    -- Standard clock/reset ties derived from the fixed Processing System setup
    clk_internal   <= FIXED_IO_ps_clk;
    rst_internal_n <= FIXED_IO_ps_porb;

    -- Instantiation of the Automated Processing Subsystem Wrapper
    Processor_System_Block : component chaos_design_wrapper
        port map (
            DDR_addr          => DDR_addr,
            DDR_ba            => DDR_ba,
            DDR_cas_n         => DDR_cas_n,
            DDR_ck_n          => DDR_ck_n,
            DDR_ck_p          => DDR_ck_p,
            DDR_cke           => DDR_cke,
            DDR_cs_n          => DDR_cs_n,
            DDR_dm            => DDR_dm,
            DDR_dq            => DDR_dq,
            DDR_dqs_n         => DDR_dqs_n,
            DDR_dqs_p         => DDR_dqs_p,
            DDR_odt           => DDR_odt,
            DDR_ras_n         => DDR_ras_n,
            DDR_reset_n       => DDR_reset_n,
            DDR_we_n          => DDR_we_n,
            FIXED_IO_ddr_vrn  => FIXED_IO_ddr_vrn,
            FIXED_IO_ddr_vrp  => FIXED_IO_ddr_vrp,
            FIXED_IO_mio      => FIXED_IO_mio,
            FIXED_IO_ps_clk   => FIXED_IO_ps_clk,
            FIXED_IO_ps_porb  => FIXED_IO_ps_porb,
            FIXED_IO_ps_srstb => FIXED_IO_ps_srstb,
            
            -- Bus lines out to your custom VHDL structures
            gpio_rtl_0_tri_o  => W_gpio0_ch1,
            gpio_rtl_1_tri_i  => W_gpio0_ch2,
            gpio_rtl_2_tri_i  => W_gpio1_ch1,
            gpio_rtl_3_tri_i  => W_gpio1_ch2,
            gpio_rtl_4_tri_i  => W_gpio2_ch1,
            gpio_rtl_5_tri_i  => W_gpio2_ch2,
            gpio_rtl_6_tri_i  => W_gpio3_ch1,
            gpio_rtl_7_tri_i  => W_gpio3_ch2,
            gpio_rtl_8_tri_i  => W_gpio4_ch1,
            gpio_rtl_9_tri_i  => W_gpio4_ch2,
            gpio_rtl_10_tri_i => W_gpio5_ch1,
            gpio_rtl_11_tri_i => W_gpio5_ch2,
            gpio_rtl_12_tri_i => W_gpio6_ch1,
            gpio_rtl_13_tri_i => W_gpio6_ch2
        );

    -- Instantiation of your core Chaos secure top module 
    Chaos_Core_Block : component chaos_hybrid_single_board
        port map (
            clk_pl        => clk_internal,
            rst_pl_n      => rst_internal_n,
            gpio0_ch1_in  => W_gpio0_ch1,
            gpio0_ch2_out => W_gpio0_ch2,
            gpio1_ch1_out => W_gpio1_ch1,
            gpio1_ch2_out => W_gpio1_ch2,
            gpio2_ch1_out => W_gpio2_ch1,
            gpio2_ch2_out => W_gpio2_ch2,
            gpio3_ch1_out => W_gpio3_ch1,
            gpio3_ch2_out => W_gpio3_ch2,
            gpio4_ch1_out => W_gpio4_ch1,
            gpio4_ch2_out => W_gpio4_ch2,
            gpio5_ch1_out => W_gpio5_ch1,
            gpio5_ch2_out => W_gpio5_ch2,
            gpio6_ch1_out => W_gpio6_ch1,
            gpio6_ch2_out => W_gpio6_ch2
        );

end architecture structural;