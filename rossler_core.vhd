--------------------------------------------------------------------------------
-- File        : rossler_core.vhd
-- Description : 4-stage pipelined Rössler chaotic oscillator
--               Fixed-point Q16.16 arithmetic
--               Designed for timing closure at 40 MHz on PYNQ-Z2
--               Throughput: 1 state update per clock after 4-cycle latency
--
-- Pipeline Stages:
--   Stage 0 (Input):  Register x, y, z state variables
--   Stage 1 (Mult):   Compute a*y and (x-c), register results
--   Stage 2 (Mult):   Compute z*(x-c), register result
--   Stage 3 (Add):    Compute dx, dy, dz from staged results
--   Stage 4 (Output): Compute x+dt*dx, y+dt*dy, z+dt*dz, write state
--
-- Parameters (Q16.16 fixed-point encoding):
--   a = 0.2   → 13107
--   b = 0.2   → 13107
--   c = 5.7   → 373554
--   dt = 0.001 → 66
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity rossler_core is
    port (
        clk          : in  std_logic;
        rst          : in  std_logic;   -- Synchronous active-high reset

        -- Oscillator enable
        -- Hold high for continuous operation
        -- Pull low to freeze state (useful for UART transmission windows)
        enable       : in  std_logic;

        -- Pecora-Carroll synchronization interface
        -- Transmitter: sync_enable = '0', x_drive ignored
        -- Receiver:    sync_enable = '1', x_drive = received x from UART
        sync_enable  : in  std_logic;
        x_drive      : in  std_logic_vector(31 downto 0);

        -- State outputs (Q16.16 format)
        x_out        : out std_logic_vector(31 downto 0);
        y_out        : out std_logic_vector(31 downto 0);
        z_out        : out std_logic_vector(31 downto 0);

        -- Keystream for XOR encryption
        -- 16 most-entropic bits of x state
        keystream    : out std_logic_vector(15 downto 0);

        -- Pipeline valid flag
        -- Goes high after first 4 cycles, stays high
        -- Python should wait for this before reading keystream
        output_valid : out std_logic
    );
end entity rossler_core;

architecture rtl of rossler_core is

    ----------------------------------------------------------------------------
    -- Fixed-point constants (Q16.16)
    -- Conversion: integer_value = float_value * 65536
    ----------------------------------------------------------------------------
    constant A_PARAM  : signed(31 downto 0) := to_signed(13107,  32); -- 0.2
    constant B_PARAM  : signed(31 downto 0) := to_signed(13107,  32); -- 0.2
    constant C_PARAM  : signed(31 downto 0) := to_signed(373554, 32); -- 5.7
    constant DT_PARAM : signed(31 downto 0) := to_signed(66,     32); -- 0.001

    ----------------------------------------------------------------------------
    -- State registers (the actual chaotic attractor state)
    -- These only update at the END of the pipeline (Stage 4)
    -- Initial conditions: x=1.0, y=1.0, z=1.0 for Rössler
    ----------------------------------------------------------------------------
    signal x_state : signed(31 downto 0) := to_signed(65536, 32);
    signal y_state : signed(31 downto 0) := to_signed(65536, 32);
    signal z_state : signed(31 downto 0) := to_signed(65536, 32);

    ----------------------------------------------------------------------------
    -- Pipeline Stage 0 → Stage 1 registers
    -- These capture the state at the START of computation
    -- Named with suffix _s0 (stage 0 output / stage 1 input)
    ----------------------------------------------------------------------------
    signal x_s0 : signed(31 downto 0) := (others => '0');
    signal y_s0 : signed(31 downto 0) := (others => '0');
    signal z_s0 : signed(31 downto 0) := (others => '0');

    ----------------------------------------------------------------------------
    -- Pipeline Stage 1 → Stage 2 registers
    -- Holds: a*y (for dy computation)
    --        (x - c) (intermediate for dz computation)
    --        x, y, z passed through for later stages
    -- Multiplication result is 64-bit, we keep 32-bit after shift
    ----------------------------------------------------------------------------
    signal ay_s1    : signed(31 downto 0) := (others => '0'); -- a*y result
    signal x_sub_c  : signed(31 downto 0) := (others => '0'); -- (x-c)
    signal x_s1     : signed(31 downto 0) := (others => '0'); -- x passthrough
    signal y_s1     : signed(31 downto 0) := (others => '0'); -- y passthrough
    signal z_s1     : signed(31 downto 0) := (others => '0'); -- z passthrough

    ----------------------------------------------------------------------------
    -- Pipeline Stage 2 → Stage 3 registers
    -- Holds: z*(x-c) (second multiply for dz)
    --        a*y passed through
    --        x, y, z passed through
    ----------------------------------------------------------------------------
    signal z_x_c_s2 : signed(31 downto 0) := (others => '0'); -- z*(x-c)
    signal ay_s2    : signed(31 downto 0) := (others => '0'); -- a*y passthrough
    signal x_s2     : signed(31 downto 0) := (others => '0'); -- x passthrough
    signal y_s2     : signed(31 downto 0) := (others => '0'); -- y passthrough
    signal z_s2     : signed(31 downto 0) := (others => '0'); -- z passthrough

    ----------------------------------------------------------------------------
    -- Pipeline Stage 3 → Stage 4 registers
    -- Holds: dx, dy, dz (fully computed derivatives)
    --        x, y, z passed through for final integration
    ----------------------------------------------------------------------------
    signal dx_s3    : signed(31 downto 0) := (others => '0');
    signal dy_s3    : signed(31 downto 0) := (others => '0');
    signal dz_s3    : signed(31 downto 0) := (others => '0');
    signal x_s3     : signed(31 downto 0) := (others => '0');
    signal y_s3     : signed(31 downto 0) := (others => '0');
    signal z_s3     : signed(31 downto 0) := (others => '0');

    ----------------------------------------------------------------------------
    -- Pipeline validity shift register
    -- Tracks when pipeline has been flushed with valid data
    -- Bit 0 set on cycle 1, shifts right each cycle
    -- When bit 3 is set, output is valid
    ----------------------------------------------------------------------------
    signal valid_sr  : std_logic_vector(3 downto 0) := (others => '0');

begin

    ----------------------------------------------------------------------------
    -- STAGE 0: Capture current state into pipeline
    -- This register separates state-holding from computation
    -- Gives one full cycle for state to stabilize before math begins
    ----------------------------------------------------------------------------
    stage_0 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                x_s0 <= (others => '0');
                y_s0 <= (others => '0');
                z_s0 <= (others => '0');
            elsif enable = '1' then
                -- Pecora-Carroll: receiver uses driven x, transmitter uses free x
                if sync_enable = '1' then
                    x_s0 <= signed(x_drive);  -- Forced synchronization
                else
                    x_s0 <= x_state;           -- Free-running chaos
                end if;
                y_s0 <= y_state;
                z_s0 <= z_state;
            end if;
        end if;
    end process stage_0;

    ----------------------------------------------------------------------------
    -- STAGE 1: Register first multiplication results
    -- mult_ay is combinational from stage_0 outputs
    -- By registering here, we give the DSP48 a full clock cycle to settle
    -- Critical path: DSP48 multiply = ~5-7 ns, fits in 25 ns budget easily
    ----------------------------------------------------------------------------
    stage_1 : process(clk)
        variable mult_ay : signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ay_s1   <= (others => '0');
                x_sub_c <= (others => '0');
                x_s1    <= (others => '0');
                y_s1    <= (others => '0');
                z_s1    <= (others => '0');
            elsif enable = '1' then
                -- Synchronous multiplication
                mult_ay := A_PARAM * y_s0;
                ay_s1   <= mult_ay(47 downto 16);

                -- Simple subtraction for (x - c)
                x_sub_c <= x_s0 - C_PARAM;

                -- Pass state through pipeline
                x_s1 <= x_s0;
                y_s1 <= y_s0;
                z_s1 <= z_s0;
            end if;
        end if;
    end process stage_1;

    ----------------------------------------------------------------------------
    -- STAGE 2: Register second multiplication result
    -- mult_zxc is combinational using z_s1 and x_sub_c (both from stage 1)
    -- Both inputs are already registered - DSP48 gets clean, stable inputs
    -- This is the key: no cascaded multiplications in one cycle
    ----------------------------------------------------------------------------
    stage_2 : process(clk)
        variable mult_zxc : signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                z_x_c_s2 <= (others => '0');
                ay_s2    <= (others => '0');
                x_s2     <= (others => '0');
                y_s2     <= (others => '0');
                z_s2     <= (others => '0');
            elsif enable = '1' then
                -- Synchronous multiplication
                mult_zxc := z_s1 * x_sub_c;
                z_x_c_s2 <= mult_zxc(47 downto 16);
                
                ay_s2    <= ay_s1;   -- Pass through
                x_s2     <= x_s1;
                y_s2     <= y_s1;
                z_s2     <= z_s1;
            end if;
        end if;
    end process stage_2;

    ----------------------------------------------------------------------------
    -- STAGE 3: Compute derivatives dx, dy, dz
    -- All inputs are now registered - pure addition/subtraction here
    -- Additions are fast (~0.5-1 ns), no timing concern at all
    --
    -- Rössler equations:
    --   dx = -y - z
    --   dy = x + (a*y)     [a*y = ay_s2, already computed]
    --   dz = b + z*(x-c)   [z*(x-c) = z_x_c_s2, already computed]
    ----------------------------------------------------------------------------
    stage_3 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                dx_s3 <= (others => '0');
                dy_s3 <= (others => '0');
                dz_s3 <= (others => '0');
                x_s3  <= (others => '0');
                y_s3  <= (others => '0');
                z_s3  <= (others => '0');
            elsif enable = '1' then
                -- Rössler derivatives (all additions - timing trivial)
                dx_s3 <= (- y_s2) - z_s2;
                dy_s3 <= x_s2 + ay_s2;
                dz_s3 <= B_PARAM + z_x_c_s2;

                -- Pass state through for Euler integration in stage 4
                x_s3 <= x_s2;
                y_s3 <= y_s2;
                z_s3 <= z_s2;
            end if;
        end if;
    end process stage_3;

    ----------------------------------------------------------------------------
    -- STAGE 4: Euler integration - update state registers
    -- x_new = x + dt * dx
    -- mult_dtdx is combinational from stage_3 outputs
    -- These three DSP48 multiplications are INDEPENDENT (parallel, not serial)
    -- Parallel multiplications do not stack timing - each fits in one cycle
    ----------------------------------------------------------------------------
    stage_4 : process(clk)
        variable mult_dtdx : signed(63 downto 0);
        variable mult_dtdy : signed(63 downto 0);
        variable mult_dtdz : signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                x_state <= to_signed(65536, 32);   -- 1.0 initial condition
                y_state <= to_signed(65536, 32);   -- 1.0 initial condition
                z_state <= to_signed(65536, 32);   -- 1.0 initial condition
            elsif enable = '1' then
                -- Synchronous multiplications (parallel)
                mult_dtdx := DT_PARAM * dx_s3;
                mult_dtdy := DT_PARAM * dy_s3;
                mult_dtdz := DT_PARAM * dz_s3;
                
                -- Euler integration: state = state + dt * derivative
                x_state <= x_s3 + mult_dtdx(47 downto 16);
                y_state <= y_s3 + mult_dtdy(47 downto 16);
                z_state <= z_s3 + mult_dtdz(47 downto 16);
            end if;
        end if;
    end process stage_4;

    ----------------------------------------------------------------------------
    -- Pipeline validity tracking
    -- Shift register fills with '1' as pipeline stages fill with valid data
    -- After 4 cycles, all stages contain valid data
    ----------------------------------------------------------------------------
    valid_tracking : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                valid_sr <= (others => '0');
            elsif enable = '1' then
                valid_sr <= valid_sr(2 downto 0) & '1';
            end if;
        end if;
    end process valid_tracking;

    ----------------------------------------------------------------------------
    -- Output assignments
    ----------------------------------------------------------------------------
    x_out        <= std_logic_vector(x_state);
    y_out        <= std_logic_vector(y_state);
    z_out        <= std_logic_vector(z_state);

    -- Keystream: bits [23:8] have maximum entropy in Q16.16 chaos
    -- Avoid MSBs (mostly sign/integer part, low entropy for small attractors)
    -- Avoid LSBs (quantization noise, low entropy)
    keystream    <= std_logic_vector(x_state(23 downto 8));

    output_valid <= valid_sr(3);

end architecture rtl;