--------------------------------------------------------------------------------
-- File        : chaos_sync_top.vhd
-- Description : Top-level wrapper for Pecora-Carroll chaos synchronization
--               Integrates rossler_pipelined with AXI GPIO and UART EMIO
--
-- AXI GPIO Mapping:
--   GPIO0 (32-bit): Control/Status Register
--     [0]    : state_step (write 1 to pulse, auto-clears)
--     [1]    : sync_enable (0=master, 1=slave)
--     [2]    : rst (active high)
--     [31:16]: reserved
--   
--   GPIO1 (32-bit): x_drive input (for slave mode)
--   GPIO2 (32-bit): x_out readback
--   GPIO3 (32-bit): y_out readback
--   GPIO4 (32-bit): z_out readback
--
-- UART: Connected via EMIO to PS UART1, routed to PMOD A pins
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chaos_sync_top is
    generic (
        -- Set these differently for master vs slave builds
        Y0_INIT : integer := 65536;  -- Master: 65536 (1.0), Slave: 32768 (0.5)
        Z0_INIT : integer := 65536   -- Master: 65536 (1.0), Slave: 98304 (1.5)
    );
    port (
        -- System clock and reset from PS
        clk_pl          : in  std_logic;
        rst_pl_n        : in  std_logic;
        
        -- AXI GPIO interfaces (simplified - actual AXI signals handled by IP)
        -- These connect to AXI GPIO IP blocks in block design
        gpio0_in        : out std_logic_vector(31 downto 0);
        gpio0_out       : in  std_logic_vector(31 downto 0);
        gpio0_tri       : out std_logic_vector(31 downto 0);
        
        gpio1_in        : out std_logic_vector(31 downto 0);
        gpio1_out       : in  std_logic_vector(31 downto 0);
        gpio1_tri       : out std_logic_vector(31 downto 0);
        
        gpio2_in        : out std_logic_vector(31 downto 0);
        gpio2_out       : in  std_logic_vector(31 downto 0);
        gpio2_tri       : out std_logic_vector(31 downto 0);
        
        gpio3_in        : out std_logic_vector(31 downto 0);
        gpio3_out       : in  std_logic_vector(31 downto 0);
        gpio3_tri       : out std_logic_vector(31 downto 0);
        
        gpio4_in        : out std_logic_vector(31 downto 0);
        gpio4_out       : in  std_logic_vector(31 downto 0);
        gpio4_tri       : out std_logic_vector(31 downto 0);
        
        -- UART EMIO signals (connect to PS UART1 via EMIO in block design)
        uart_txd        : out std_logic;
        uart_rxd        : in  std_logic
    );
end entity chaos_sync_top;

architecture rtl of chaos_sync_top is

    -- Component declaration
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

    -- Internal signals
    signal rst_pl           : std_logic;
    signal state_step       : std_logic;
    signal state_step_req   : std_logic;
    signal state_step_prev  : std_logic;
    signal sync_enable      : std_logic;
    signal rst_core         : std_logic;
    signal x_drive          : std_logic_vector(31 downto 0);
    signal x_out            : std_logic_vector(31 downto 0);
    signal y_out            : std_logic_vector(31 downto 0);
    signal z_out            : std_logic_vector(31 downto 0);
    signal keystream        : std_logic_vector(15 downto 0);

begin

    -- Active-high reset
    rst_pl <= not rst_pl_n;

    -- GPIO0: Control/Status
    -- Extract control signals from GPIO0_out
    state_step_req <= gpio0_out(0);
    sync_enable    <= gpio0_out(1);
    rst_core       <= gpio0_out(2);
    
    -- Status readback (currently just echo control bits)
    gpio0_in  <= (0 => state_step_req, 
                  1 => sync_enable, 
                  2 => rst_core, 
                  others => '0');
    gpio0_tri <= (others => '1');  -- All inputs for readback

    -- GPIO1: x_drive input (for slave)
    x_drive   <= gpio1_out;
    gpio1_in  <= (others => '0');
    gpio1_tri <= (others => '0');  -- Output from PS perspective

    -- GPIO2: x_out readback
    gpio2_in  <= x_out;
    gpio2_tri <= (others => '1');  -- Input to PS

    -- GPIO3: y_out readback
    gpio3_in  <= y_out;
    gpio3_tri <= (others => '1');

    -- GPIO4: z_out readback
    gpio4_in  <= z_out;
    gpio4_tri <= (others => '1');

    -- State step pulse generator
    -- Converts level to single-cycle pulse
    process(clk_pl)
    begin
        if rising_edge(clk_pl) then
            if rst_pl = '1' then
                state_step_prev <= '0';
                state_step <= '0';
            else
                state_step_prev <= state_step_req;
                -- Generate pulse on rising edge
                if state_step_req = '1' and state_step_prev = '0' then
                    state_step <= '1';
                else
                    state_step <= '0';
                end if;
            end if;
        end if;
    end process;

    -- Rossler oscillator instance
    rossler_inst : rossler_pipelined
        generic map (
            Y0_INIT => Y0_INIT,
            Z0_INIT => Z0_INIT
        )
        port map (
            clk         => clk_pl,
            rst         => rst_core,
            state_step  => state_step,
            sync_enable => sync_enable,
            x_drive     => x_drive,
            x_out       => x_out,
            y_out       => y_out,
            z_out       => z_out,
            keystream   => keystream
        );

    -- UART pass-through (actual UART logic handled by PS)
    -- These signals connect to EMIO in block design
    uart_txd <= '1';  -- Idle high (handled by PS UART controller)

end architecture rtl;