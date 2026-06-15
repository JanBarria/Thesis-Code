--------------------------------------------------------------------------------
-- File        : chaos_system_tb.vhd
-- Description : Comprehensive testbench for Rössler and Chua chaotic oscillators
--               Generates 40 MHz clock and active-high reset
--               Writes state vectors to external file when output_valid is high
--               File format: space-separated hexadecimal values (x y z)
--
-- Usage:
--   1. Simulate for desired duration (e.g., 100,000 cycles = 2.5 ms @ 40 MHz)
--   2. Output file 'chaotic_hardware_vectors.txt' contains state trajectory
--   3. Use Python script to parse file and visualize attractors
--
-- Author: Senior Digital Design Engineer
-- Date: 2026-06-11
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

-- TEXTIO libraries for file I/O
library STD;
use STD.TEXTIO.ALL;
use IEEE.STD_LOGIC_TEXTIO.ALL;

entity chaos_system_tb is
    -- Testbenches have no ports
end entity chaos_system_tb;

architecture behavioral of chaos_system_tb is

    ----------------------------------------------------------------------------
    -- Component Declarations
    ----------------------------------------------------------------------------
    
    -- Rössler oscillator core
    component rossler_core is
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

    -- Chua oscillator core
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

    ----------------------------------------------------------------------------
    -- Testbench Configuration Constants
    ----------------------------------------------------------------------------
    
    -- Clock period for 40 MHz (25 ns period)
    constant CLK_PERIOD : time := 25 ns;
    
    -- Simulation duration (number of clock cycles to simulate)
    -- 100,000 cycles = 2.5 ms of real time
    -- This captures ~2500 state updates (one per cycle after pipeline fills)
    constant SIM_CYCLES : integer := 100000;
    
    -- Reset duration (number of clock cycles)
    constant RESET_CYCLES : integer := 10;

    ----------------------------------------------------------------------------
    -- Testbench Signals
    ----------------------------------------------------------------------------
    
    -- Clock and reset
    signal clk          : std_logic := '0';
    signal rst          : std_logic := '1';  -- Start in reset
    signal enable       : std_logic := '1';  -- Always enabled for free-running
    
    -- Rössler signals
    signal rossler_x_out        : std_logic_vector(31 downto 0);
    signal rossler_y_out        : std_logic_vector(31 downto 0);
    signal rossler_z_out        : std_logic_vector(31 downto 0);
    signal rossler_keystream    : std_logic_vector(15 downto 0);
    signal rossler_output_valid : std_logic;
    
    -- Chua signals
    signal chua_x_out        : std_logic_vector(31 downto 0);
    signal chua_y_out        : std_logic_vector(31 downto 0);
    signal chua_z_out        : std_logic_vector(31 downto 0);
    signal chua_keystream    : std_logic_vector(15 downto 0);
    signal chua_output_valid : std_logic;
    
    -- Simulation control
    signal sim_done : boolean := false;
    
    -- Cycle counter
    signal cycle_count : integer := 0;

begin

    ----------------------------------------------------------------------------
    -- Clock Generation Process
    -- Generates 40 MHz clock (25 ns period)
    -- Stops when simulation is complete
    ----------------------------------------------------------------------------
    clk_gen : process
    begin
        while not sim_done loop
            clk <= '0';
            wait for CLK_PERIOD / 2;
            clk <= '1';
            wait for CLK_PERIOD / 2;
        end loop;
        wait;  -- Stop clock generation
    end process clk_gen;

    ----------------------------------------------------------------------------
    -- Reset Generation Process
    -- Asserts reset for RESET_CYCLES, then deasserts
    -- Active-high synchronous reset
    ----------------------------------------------------------------------------
    reset_gen : process
    begin
        rst <= '1';
        wait for CLK_PERIOD * RESET_CYCLES;
        wait until rising_edge(clk);  -- Synchronous deassertion
        rst <= '0';
        wait;  -- Hold reset low for rest of simulation
    end process reset_gen;

    ----------------------------------------------------------------------------
    -- Cycle Counter Process
    -- Tracks simulation progress
    ----------------------------------------------------------------------------
    cycle_counter : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                cycle_count <= 0;
            else
                cycle_count <= cycle_count + 1;
            end if;
        end if;
    end process cycle_counter;

    ----------------------------------------------------------------------------
    -- Simulation Control Process
    -- Terminates simulation after SIM_CYCLES
    ----------------------------------------------------------------------------
    sim_control : process
    begin
        wait for CLK_PERIOD * (SIM_CYCLES + RESET_CYCLES + 10);
        report "Simulation complete: " & integer'image(SIM_CYCLES) & " cycles simulated";
        sim_done <= true;
        wait;
    end process sim_control;

    ----------------------------------------------------------------------------
    -- Device Under Test: Rössler Oscillator
    ----------------------------------------------------------------------------
    uut_rossler : rossler_core
        port map (
            clk          => clk,
            rst          => rst,
            enable       => enable,
            sync_enable  => '0',                    -- Free-running mode
            x_drive      => (others => '0'),        -- Unused in free-running
            x_out        => rossler_x_out,
            y_out        => rossler_y_out,
            z_out        => rossler_z_out,
            keystream    => rossler_keystream,
            output_valid => rossler_output_valid
        );

    ----------------------------------------------------------------------------
    -- Device Under Test: Chua Oscillator
    ----------------------------------------------------------------------------
    uut_chua : chua_core
        port map (
            clk          => clk,
            rst          => rst,
            enable       => enable,
            sync_enable  => '0',                    -- Free-running mode
            x_drive      => (others => '0'),        -- Unused in free-running
            x_out        => chua_x_out,
            y_out        => chua_y_out,
            z_out        => chua_z_out,
            keystream    => chua_keystream,
            output_valid => chua_output_valid
        );

    ----------------------------------------------------------------------------
    -- File Writing Process: Rössler Data
    -- Writes x, y, z state vectors to file when output_valid is high
    -- Format: hexadecimal values, space-separated, one line per valid sample
    ----------------------------------------------------------------------------
    rossler_file_writer : process(clk)
        file output_file     : text;
        variable output_line : line;
        variable file_opened : boolean := false;
        variable sample_count : integer := 0;
    begin
        if rising_edge(clk) then
            -- Open file on first valid output (after pipeline fills)
            if rossler_output_valid = '1' and not file_opened then
                file_open(output_file, "rossler_hardware_vectors.txt", write_mode);
                file_opened := true;
                report "Rössler output file opened: rossler_hardware_vectors.txt";
            end if;
            
            -- Write data when output is valid
            if rossler_output_valid = '1' and file_opened then
                -- Write x value (hexadecimal, 8 hex digits for 32 bits)
                hwrite(output_line, rossler_x_out);
                write(output_line, string'(" "));
                
                -- Write y value
                hwrite(output_line, rossler_y_out);
                write(output_line, string'(" "));
                
                -- Write z value
                hwrite(output_line, rossler_z_out);
                
                -- Write line to file
                writeline(output_file, output_line);
                
                sample_count := sample_count + 1;
                
                -- Progress report every 10,000 samples
                if sample_count mod 10000 = 0 then
                    report "Rössler: " & integer'image(sample_count) & " samples written";
                end if;
            end if;
            
            -- Close file when simulation ends
            if sim_done and file_opened then
                file_close(output_file);
                report "Rössler output file closed. Total samples: " & integer'image(sample_count);
            end if;
        end if;
    end process rossler_file_writer;

    ----------------------------------------------------------------------------
    -- File Writing Process: Chua Data
    -- Writes x, y, z state vectors to file when output_valid is high
    -- Format: hexadecimal values, space-separated, one line per valid sample
    ----------------------------------------------------------------------------
    chua_file_writer : process(clk)
        file output_file     : text;
        variable output_line : line;
        variable file_opened : boolean := false;
        variable sample_count : integer := 0;
    begin
        if rising_edge(clk) then
            -- Open file on first valid output (after pipeline fills)
            if chua_output_valid = '1' and not file_opened then
                file_open(output_file, "chua_hardware_vectors.txt", write_mode);
                file_opened := true;
                report "Chua output file opened: chua_hardware_vectors.txt";
            end if;
            
            -- Write data when output is valid
            if chua_output_valid = '1' and file_opened then
                -- Write x value (hexadecimal, 8 hex digits for 32 bits)
                hwrite(output_line, chua_x_out);
                write(output_line, string'(" "));
                
                -- Write y value
                hwrite(output_line, chua_y_out);
                write(output_line, string'(" "));
                
                -- Write z value
                hwrite(output_line, chua_z_out);
                
                -- Write line to file
                writeline(output_file, output_line);
                
                sample_count := sample_count + 1;
                
                -- Progress report every 10,000 samples
                if sample_count mod 10000 = 0 then
                    report "Chua: " & integer'image(sample_count) & " samples written";
                end if;
            end if;
            
            -- Close file when simulation ends
            if sim_done and file_opened then
                file_close(output_file);
                report "Chua output file closed. Total samples: " & integer'image(sample_count);
            end if;
        end if;
    end process chua_file_writer;

    ----------------------------------------------------------------------------
    -- Console Monitoring Process
    -- Prints periodic status updates to console during simulation
    ----------------------------------------------------------------------------
    console_monitor : process(clk)
        variable last_report_cycle : integer := 0;
    begin
        if rising_edge(clk) then
            -- Report every 10,000 cycles
            if cycle_count - last_report_cycle >= 10000 then
                report "Simulation progress: " & integer'image(cycle_count) & " / " & 
                       integer'image(SIM_CYCLES) & " cycles (" & 
                       integer'image((cycle_count * 100) / SIM_CYCLES) & "%)";
                last_report_cycle := cycle_count;
            end if;
        end if;
    end process console_monitor;

    ----------------------------------------------------------------------------
    -- Initial Status Report
    ----------------------------------------------------------------------------
    initial_report : process
    begin
        wait for 1 ns;  -- Let signals initialize
        report "========================================";
        report "Chaos System Testbench Started";
        report "========================================";
        report "Clock frequency: 40 MHz (25 ns period)";
        report "Reset duration: " & integer'image(RESET_CYCLES) & " cycles";
        report "Simulation duration: " & integer'image(SIM_CYCLES) & " cycles";
        report "Expected runtime: " & integer'image(SIM_CYCLES * 25) & " ns";
        report "Output files:";
        report "  - rossler_hardware_vectors.txt";
        report "  - chua_hardware_vectors.txt";
        report "========================================";
        wait;
    end process initial_report;

end architecture behavioral;