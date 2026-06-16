--------------------------------------------------------------------------------
-- File        : chaos_sync_single_board.vhd
-- Description : SO3 single-board top: master + slave Rossler oscillators on
--               the same FPGA, coupled in fabric (no UART).
--
-- Scope note:
--   The verbatim SO3 wording says "between transmitter and receiver FPGAs"
--   (two devices). This single-board build co-locates both oscillators on
--   ONE FPGA — a legitimate verification of the Pecora-Carroll technique
--   itself but NOT a literal two-FPGA demonstration.
--   See docs/SINGLE_BOARD_SO3.md for the wording recommendation.
--
-- Architecture:
--
--   AXI GPIO0 ch1 (input  PS->PL): control register
--     [0] rst         (active-high reset, level)
--     [1] step_trig   (level; rising edge ⇒ one state_step pulse)
--   AXI GPIO0 ch2 (output PL->PS): m_x
--   AXI GPIO1 ch1/ch2 (PL->PS):    m_y / m_z
--   AXI GPIO2 ch1/ch2 (PL->PS):    s_x / s_y
--   AXI GPIO3 ch1     (PL->PS):    s_z
--   AXI GPIO3 ch2     (PL->PS):    status_word [31:16]=m_keystream
--                                              [15:0] =s_keystream
--
--   Pecora-Carroll wiring (in fabric, zero serialization):
--      master.x_out  ──────────►  slave.x_drive
--
-- Both instances share:
--   * the same clk and rst
--   * the same state_step pulse (lockstep advance)
--
-- This top-level deliberately omits the EMIO UART and master/slave generic
-- toggling used by the dual-board chaos_sync_top.vhd. They are unnecessary
-- here because the inter-oscillator transport is internal.
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chaos_sync_single_board is
    port (
        -- Programmable Logic clock and reset (from PS via Processor System Reset IP)
        clk_pl        : in  std_logic;
        rst_pl_n      : in  std_logic;

        -- AXI GPIO 0: control input + m_x output
        gpio0_ch1_in  : in  std_logic_vector(31 downto 0);   -- control reg
        gpio0_ch2_out : out std_logic_vector(31 downto 0);   -- m_x

        -- AXI GPIO 1: m_y, m_z
        gpio1_ch1_out : out std_logic_vector(31 downto 0);   -- m_y
        gpio1_ch2_out : out std_logic_vector(31 downto 0);   -- m_z

        -- AXI GPIO 2: s_x, s_y
        gpio2_ch1_out : out std_logic_vector(31 downto 0);   -- s_x
        gpio2_ch2_out : out std_logic_vector(31 downto 0);   -- s_y

        -- AXI GPIO 3: s_z, packed keystreams
        gpio3_ch1_out : out std_logic_vector(31 downto 0);   -- s_z
        gpio3_ch2_out : out std_logic_vector(31 downto 0)    -- {m_ks, s_ks}
    );
end entity chaos_sync_single_board;

architecture structural of chaos_sync_single_board is

    -- Internal control signals decoded from AXI GPIO0 ch1
    signal soft_rst       : std_logic;
    signal step_trig      : std_logic;
    signal combined_rst   : std_logic;
    signal step_pulse     : std_logic;

    -- Master state outputs
    signal m_x, m_y, m_z  : std_logic_vector(31 downto 0);
    signal m_keystream    : std_logic_vector(15 downto 0);

    -- Slave state outputs
    signal s_x, s_y, s_z  : std_logic_vector(31 downto 0);
    signal s_keystream    : std_logic_vector(15 downto 0);

    -- Tied-off master x_drive (not used since sync_enable='0')
    constant ZERO32       : std_logic_vector(31 downto 0) := (others => '0');

    -- Component declarations
    component rossler_pipelined is
        generic (
            Y0_INIT : integer := 65536;
            Z0_INIT : integer := 65536
        );
        port (
            clk          : in  std_logic;
            rst          : in  std_logic;
            state_step   : in  std_logic;
            sync_enable  : in  std_logic;
            x_drive      : in  std_logic_vector(31 downto 0);
            x_out        : out std_logic_vector(31 downto 0);
            y_out        : out std_logic_vector(31 downto 0);
            z_out        : out std_logic_vector(31 downto 0);
            keystream    : out std_logic_vector(15 downto 0)
        );
    end component;

    component edge_detector is
        port (
            clk       : in  std_logic;
            rst       : in  std_logic;
            trig_in   : in  std_logic;
            pulse_out : out std_logic
        );
    end component;

begin

    ----------------------------------------------------------------------------
    -- Control register decode (AXI GPIO0 ch1)
    --   bit 0 : soft reset
    --   bit 1 : step trigger (level → rising edge → 1-cycle pulse)
    ----------------------------------------------------------------------------
    soft_rst     <= gpio0_ch1_in(0);
    step_trig    <= gpio0_ch1_in(1);
    combined_rst <= (not rst_pl_n) or soft_rst;   -- async-released by PS RST IP

    ----------------------------------------------------------------------------
    -- Edge detector: produce a 1-cycle pulse on rising edge of step_trig
    ----------------------------------------------------------------------------
    step_pulse_inst : edge_detector
        port map (
            clk       => clk_pl,
            rst       => combined_rst,
            trig_in   => step_trig,
            pulse_out => step_pulse
        );

    ----------------------------------------------------------------------------
    -- MASTER oscillator: free-running, default ICs (1.0, 1.0, 1.0)
    ----------------------------------------------------------------------------
    master_inst : rossler_pipelined
        generic map (
            Y0_INIT => 65536,   -- 1.0
            Z0_INIT => 65536    -- 1.0
        )
        port map (
            clk          => clk_pl,
            rst          => combined_rst,
            state_step   => step_pulse,
            sync_enable  => '0',         -- free-running
            x_drive      => ZERO32,      -- don't-care
            x_out        => m_x,
            y_out        => m_y,
            z_out        => m_z,
            keystream    => m_keystream
        );

    ----------------------------------------------------------------------------
    -- SLAVE oscillator: x_drive ← master.x_out (fabric coupling)
    -- Deliberately different IC: (1.0, 0.5, 1.5) to make y,z convergence visible
    ----------------------------------------------------------------------------
    slave_inst : rossler_pipelined
        generic map (
            Y0_INIT => 32768,   -- 0.5
            Z0_INIT => 98304    -- 1.5
        )
        port map (
            clk          => clk_pl,
            rst          => combined_rst,
            state_step   => step_pulse,
            sync_enable  => '1',         -- driven by master.x_out
            x_drive      => m_x,
            x_out        => s_x,
            y_out        => s_y,
            z_out        => s_z,
            keystream    => s_keystream
        );

    ----------------------------------------------------------------------------
    -- AXI GPIO outputs (PL → PS): wire state words and packed keystreams
    ----------------------------------------------------------------------------
    gpio0_ch2_out <= m_x;
    gpio1_ch1_out <= m_y;
    gpio1_ch2_out <= m_z;
    gpio2_ch1_out <= s_x;
    gpio2_ch2_out <= s_y;
    gpio3_ch1_out <= s_z;
    gpio3_ch2_out <= m_keystream & s_keystream;   -- pack {m_ks[15:0], s_ks[15:0]}

end architecture structural;
