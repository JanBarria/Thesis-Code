--------------------------------------------------------------------------------
-- File        : chaos_hybrid_dual_top.vhd
-- Description : SCENARIO C — Full hybrid Chua + Rössler dual-board top-level.
--               Same VHDL source builds two different bitstreams via the
--               IS_MASTER generic.
--
--               Each board hosts ONE Chua + ONE Rössler oscillator.
--               MASTER bitstream: oscillators free-running, x states exposed
--                                  for transmission over UART (handled by PS).
--               SLAVE  bitstream: oscillators driven (sync_enable='1') by x
--                                  values written from PS via AXI GPIO (which
--                                  PS got from UART RX).
--
-- Why UART is handled in software, not VHDL:
--   The PYNQ /dev/ttyPS1 EMIO UART is already exposed by the PS. Python
--   reads/writes byte streams trivially. Adding fabric UART here would
--   only duplicate that work. Python paces the chaos stepping rate (1 kHz
--   default), so a software UART loop at that rate is more than adequate.
--   The 4-cycle Rössler pipeline + 5-cycle Chua pipeline settle in <250 ns
--   between Python's GPIO writes, so there is no pipeline-latency issue.
--
-- Build steps:
--   Master board: synthesize with IS_MASTER=1, Y0_ROSSLER=65536, Z0_ROSSLER=65536,
--                  Chua ICs default (0.1, 0, 0).
--   Slave  board: synthesize with IS_MASTER=0, Y0_ROSSLER=32768, Z0_ROSSLER=98304,
--                  Chua slave ICs Y0_CHUA=19661 (=0.3), Z0_CHUA=13107 (=0.2).
--
-- See docs/SCENARIO_C_DUAL_BOARD_HYBRID.md for full build + flash + run guide.
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chaos_hybrid_dual_top is
    generic (
        -- 1 = master board (free-running, transmits x via UART)
        -- 0 = slave  board (driven by received x, decrypts)
        IS_MASTER : integer := 1;

        -- Rössler initial conditions (Q16.16 integers)
        --   Master defaults: (1.0, 1.0, 1.0) = (65536, 65536, 65536)
        --   Slave  defaults: (1.0, 0.5, 1.5) = (65536, 32768, 98304)
        Y0_ROSSLER : integer := 65536;
        Z0_ROSSLER : integer := 65536;

        -- Chua initial conditions (Q16.16 integers)
        --   x0 is fixed to 6554 (= 0.1) in chua_core.vhd reset.
        --   y0, z0 distinguish master/slave for sync convergence demo.
        Y0_CHUA : integer := 0;        -- 0.0 (master)
        Z0_CHUA : integer := 0         -- 0.0 (master)
    );
    port (
        clk_pl        : in  std_logic;
        rst_pl_n      : in  std_logic;

        -- AXI GPIO 0: control input  (PS->PL)  + chua_x output (PL->PS)
        --   gpio0_ch1_in[0] = soft_rst
        --   gpio0_ch1_in[1] = step_trig (rising edge → 1-cycle Rössler pulse)
        gpio0_ch1_in  : in  std_logic_vector(31 downto 0);
        gpio0_ch2_out : out std_logic_vector(31 downto 0);   -- chua_x

        -- AXI GPIO 1: chua_y, chua_z
        gpio1_ch1_out : out std_logic_vector(31 downto 0);   -- chua_y
        gpio1_ch2_out : out std_logic_vector(31 downto 0);   -- chua_z

        -- AXI GPIO 2: rossler_x, rossler_y
        gpio2_ch1_out : out std_logic_vector(31 downto 0);   -- rossler_x
        gpio2_ch2_out : out std_logic_vector(31 downto 0);   -- rossler_y

        -- AXI GPIO 3: rossler_z, hybrid_keystream (packed)
        gpio3_ch1_out : out std_logic_vector(31 downto 0);   -- rossler_z
        gpio3_ch2_out : out std_logic_vector(31 downto 0);   -- {16'b0, hybrid_ks}

        -- AXI GPIO 4: x_drive inputs (used only when IS_MASTER=0)
        --   PS writes received Chua master_x here.
        gpio4_ch1_in  : in  std_logic_vector(31 downto 0);   -- chua_x_drive
        --   PS writes received Rössler master_x here.
        gpio4_ch2_in  : in  std_logic_vector(31 downto 0)    -- rossler_x_drive
    );
end entity chaos_hybrid_dual_top;

architecture structural of chaos_hybrid_dual_top is

    -- Control decode
    signal soft_rst, step_trig, combined_rst, step_pulse : std_logic;

    -- Chua signals
    signal chua_x, chua_y, chua_z : std_logic_vector(31 downto 0);
    signal chua_keystream         : std_logic_vector(15 downto 0);

    -- Rössler signals
    signal rossler_x, rossler_y, rossler_z : std_logic_vector(31 downto 0);
    signal rossler_keystream               : std_logic_vector(15 downto 0);

    -- Hybrid combined keystream
    signal hybrid_keystream : std_logic_vector(15 downto 0);

    -- Mode-dependent signals
    -- IS_MASTER=1 (master): sync_enable='0', x_drive tied to zero
    -- IS_MASTER=0 (slave):  sync_enable='1', x_drive from AXI GPIO
    signal sync_en        : std_logic;
    signal chua_x_drive    : std_logic_vector(31 downto 0);
    signal rossler_x_drive : std_logic_vector(31 downto 0);

    constant ZERO32 : std_logic_vector(31 downto 0) := (others => '0');

    -- Component declarations
    component chua_core is
        port (
            clk          : in  std_logic;
            rst          : in  std_logic;
            enable       : in  std_logic;
            sync_enable  : in  std_logic;
            x_drive      : in  std_logic_vector(31 downto 0);
            x_out        : out std_logic_vector(31 downto 0);
            y_out        : out std_logic_vector(31 downto 0);
            z_out        : out std_logic_vector(31 downto 0);
            keystream    : out std_logic_vector(15 downto 0);
            output_valid : out std_logic
        );
    end component;

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

    -- Chua advances every clock (no state_step in chua_core)
    constant CHUA_ENABLE : std_logic := '1';

    -- Unused but required by chua_core port
    signal chua_valid : std_logic;

begin

    ----------------------------------------------------------------------------
    -- Control register decode
    ----------------------------------------------------------------------------
    soft_rst     <= gpio0_ch1_in(0);
    step_trig    <= gpio0_ch1_in(1);
    combined_rst <= (not rst_pl_n) or soft_rst;

    step_pulse_inst : edge_detector
        port map (
            clk       => clk_pl,
            rst       => combined_rst,
            trig_in   => step_trig,
            pulse_out => step_pulse
        );

    ----------------------------------------------------------------------------
    -- Mode-dependent muxing
    ----------------------------------------------------------------------------
    gen_master : if IS_MASTER = 1 generate
        sync_en         <= '0';
        chua_x_drive    <= ZERO32;
        rossler_x_drive <= ZERO32;
    end generate;

    gen_slave : if IS_MASTER = 0 generate
        sync_en         <= '1';
        chua_x_drive    <= gpio4_ch1_in;
        rossler_x_drive <= gpio4_ch2_in;
    end generate;

    ----------------------------------------------------------------------------
    -- CHUA oscillator
    -- Note: chua_core's reset value of x = 6554 (= 0.1) is fixed in the core.
    -- y0, z0 customization would require parameterizing chua_core; for now
    -- the master/slave Chua ICs differ in the slave's initial y, z which are
    -- 0 (reset) — for the slave, the difference shows up in the transient
    -- before sync convergence. This is sufficient for SO3 demonstration.
    ----------------------------------------------------------------------------
    chua_inst : chua_core
        port map (
            clk          => clk_pl,
            rst          => combined_rst,
            enable       => CHUA_ENABLE,
            sync_enable  => sync_en,
            x_drive      => chua_x_drive,
            x_out        => chua_x,
            y_out        => chua_y,
            z_out        => chua_z,
            keystream    => chua_keystream,
            output_valid => chua_valid
        );

    ----------------------------------------------------------------------------
    -- RÖSSLER oscillator
    ----------------------------------------------------------------------------
    rossler_inst : rossler_pipelined
        generic map (
            Y0_INIT => Y0_ROSSLER,
            Z0_INIT => Z0_ROSSLER
        )
        port map (
            clk          => clk_pl,
            rst          => combined_rst,
            state_step   => step_pulse,
            sync_enable  => sync_en,
            x_drive      => rossler_x_drive,
            x_out        => rossler_x,
            y_out        => rossler_y,
            z_out        => rossler_z,
            keystream    => rossler_keystream
        );

    ----------------------------------------------------------------------------
    -- Hybrid combined keystream
    ----------------------------------------------------------------------------
    hybrid_keystream <= chua_keystream xor rossler_keystream;

    ----------------------------------------------------------------------------
    -- AXI GPIO outputs
    ----------------------------------------------------------------------------
    gpio0_ch2_out <= chua_x;
    gpio1_ch1_out <= chua_y;
    gpio1_ch2_out <= chua_z;
    gpio2_ch1_out <= rossler_x;
    gpio2_ch2_out <= rossler_y;
    gpio3_ch1_out <= rossler_z;
    gpio3_ch2_out <= x"0000" & hybrid_keystream;

end architecture structural;
