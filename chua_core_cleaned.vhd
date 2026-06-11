--------------------------------------------------------------------------------
-- File        : chua_core.vhd
-- Description : 5-stage pipelined Chua chaotic oscillator
--               Fixed-point Q16.16 arithmetic
--               ALL multiplications now synchronous (inside processes)
--               Matches rossler_core architecture style
--
-- Pipeline Stages:
--   Stage 0: Capture state, compute (x+1) and (x-1) for Chua diode
--   Stage 1: Compute m1*x (first Chua diode multiply)
--   Stage 2: Compute abs values and half_diff*abs_sum
--   Stage 3: Assemble f(x), compute alpha*(y-x-f(x))
--   Stage 4: Compute derivatives dx, dy, dz
--   Stage 5: Euler integration, write state
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity chua_core is
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
end entity chua_core;

architecture rtl of chua_core is

    ----------------------------------------------------------------------------
    -- Chua parameters (Q16.16)
    -- alpha = 15.6  → 1022976
    -- beta  = 28.0  → 1835008
    -- m0    = -1.143 → -74907
    -- m1    = -0.714 → -46792
    -- dt    = 0.001  → 66
    ----------------------------------------------------------------------------
    constant ALPHA    : signed(31 downto 0) := to_signed(1022976, 32);
    constant BETA     : signed(31 downto 0) := to_signed(1835008, 32);
    constant M0       : signed(31 downto 0) := to_signed(-74907,  32);
    constant M1       : signed(31 downto 0) := to_signed(-46792,  32);
    constant DT_C     : signed(31 downto 0) := to_signed(66,      32);
    constant FP_ONE   : signed(31 downto 0) := to_signed(65536,   32); -- 1.0
    constant FP_HALF  : signed(31 downto 0) := to_signed(32768,   32); -- 0.5

    -- State registers
    signal x_state    : signed(31 downto 0) := to_signed(6554,  32); -- 0.1
    signal y_state    : signed(31 downto 0) := (others => '0');
    signal z_state    : signed(31 downto 0) := (others => '0');

    -- Stage 0 outputs
    signal x_s0       : signed(31 downto 0) := (others => '0');
    signal y_s0       : signed(31 downto 0) := (others => '0');
    signal z_s0       : signed(31 downto 0) := (others => '0');
    signal x_p1_s0    : signed(31 downto 0) := (others => '0'); -- x+1
    signal x_m1_s0    : signed(31 downto 0) := (others => '0'); -- x-1

    -- Stage 1 outputs
    signal m1x_s1     : signed(31 downto 0) := (others => '0'); -- m1*x
    signal half_diff  : signed(31 downto 0) := (others => '0'); -- 0.5*(m0-m1)
    signal x_p1_s1    : signed(31 downto 0) := (others => '0');
    signal x_m1_s1    : signed(31 downto 0) := (others => '0');
    signal x_s1       : signed(31 downto 0) := (others => '0');
    signal y_s1       : signed(31 downto 0) := (others => '0');
    signal z_s1       : signed(31 downto 0) := (others => '0');

    -- Stage 2 outputs
    signal fx_s2      : signed(31 downto 0) := (others => '0'); -- f(x) result
    signal x_s2       : signed(31 downto 0) := (others => '0');
    signal y_s2       : signed(31 downto 0) := (others => '0');
    signal z_s2       : signed(31 downto 0) := (others => '0');

    -- Stage 3 outputs
    signal alpha_arg  : signed(31 downto 0) := (others => '0'); -- y-x-f(x)
    signal x_s3       : signed(31 downto 0) := (others => '0');
    signal y_s3       : signed(31 downto 0) := (others => '0');
    signal z_s3       : signed(31 downto 0) := (others => '0');

    -- Stage 4 outputs (derivatives)
    signal dx_s4      : signed(31 downto 0) := (others => '0');
    signal dy_s4      : signed(31 downto 0) := (others => '0');
    signal dz_s4      : signed(31 downto 0) := (others => '0');
    signal x_s4       : signed(31 downto 0) := (others => '0');
    signal y_s4       : signed(31 downto 0) := (others => '0');
    signal z_s4       : signed(31 downto 0) := (others => '0');

    -- Valid tracking
    signal valid_sr   : std_logic_vector(4 downto 0) := (others => '0');

begin

    ----------------------------------------------------------------------------
    -- STAGE 0: Capture state
    -- Compute x+1 and x-1 for Chua diode (simple additions, no multipliers)
    ----------------------------------------------------------------------------
    stage_0 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                -- FIX: Initialize pipeline with initial conditions
                x_s0 <= to_signed(6554, 32);  -- 0.1
                y_s0 <= (others => '0');      -- 0.0
                z_s0 <= (others => '0');      -- 0.0
                x_p1_s0 <= to_signed(72090, 32);  -- 0.1 + 1.0 = 1.1
                x_m1_s0 <= to_signed(-58982, 32); -- 0.1 - 1.0 = -0.9
            elsif enable = '1' then
                if sync_enable = '1' then
                    x_s0 <= signed(x_drive);
                else
                    x_s0 <= x_state;
                end if;
                y_s0    <= y_state;
                z_s0    <= z_state;
                x_p1_s0 <= x_state + FP_ONE;   -- x + 1.0
                x_m1_s0 <= x_state - FP_ONE;   -- x - 1.0
            end if;
        end if;
    end process stage_0;

    ----------------------------------------------------------------------------
    -- STAGE 1: First multiply (m1*x) + compute half_diff constant
    -- SYNCHRONOUS multiplication inside process
    ----------------------------------------------------------------------------
    stage_1 : process(clk)
        variable mult_m1x : signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                m1x_s1    <= (others => '0');
                half_diff <= (others => '0');
                x_p1_s1   <= (others => '0');
                x_m1_s1   <= (others => '0');
                x_s1 <= (others => '0');
                y_s1 <= (others => '0');
                z_s1 <= (others => '0');
            elsif enable = '1' then
                -- Synchronous multiplication: m1 * x
                mult_m1x := M1 * x_s0;
                m1x_s1   <= mult_m1x(47 downto 16);
                
                -- 0.5*(m0-m1) is a constant, computed once
                -- = 0.5 * (-74907 - (-46792)) = 0.5 * (-28115) = -14058
                half_diff <= to_signed(-14058, 32);
                
                -- Pass through pipeline
                x_p1_s1   <= x_p1_s0;
                x_m1_s1   <= x_m1_s0;
                x_s1 <= x_s0;
                y_s1 <= y_s0;
                z_s1 <= z_s0;
            end if;
        end if;
    end process stage_1;

    ----------------------------------------------------------------------------
    -- STAGE 2: Second multiply (half_diff * abs_diff) → complete f(x)
    -- SYNCHRONOUS multiplication inside process
    -- Absolute values computed as local variables (mux on sign bit)
    ----------------------------------------------------------------------------
    stage_2 : process(clk)
        variable abs_xp1    : signed(31 downto 0);
        variable abs_xm1    : signed(31 downto 0);
        variable abs_diff   : signed(31 downto 0);
        variable mult_hd_abs: signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                fx_s2 <= (others => '0');
                x_s2  <= (others => '0');
                y_s2  <= (others => '0');
                z_s2  <= (others => '0');
            elsif enable = '1' then
                -- Compute absolute values (fast mux operations)
                abs_xp1 := x_p1_s1 when x_p1_s1 >= 0 else -x_p1_s1;
                abs_xm1 := x_m1_s1 when x_m1_s1 >= 0 else -x_m1_s1;
                abs_diff := abs_xp1 - abs_xm1;
                
                -- Synchronous multiplication: half_diff * abs_diff
                mult_hd_abs := half_diff * abs_diff;
                
                -- f(x) = m1*x + 0.5*(m0-m1)*(|x+1| - |x-1|)
                fx_s2 <= m1x_s1 + mult_hd_abs(47 downto 16);
                
                -- Pass through pipeline
                x_s2  <= x_s1;
                y_s2  <= y_s1;
                z_s2  <= z_s1;
            end if;
        end if;
    end process stage_2;

    ----------------------------------------------------------------------------
    -- STAGE 3: Assemble alpha argument (y - x - f(x))
    -- Pure addition/subtraction, no multipliers
    ----------------------------------------------------------------------------
    stage_3 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                alpha_arg <= (others => '0');
                x_s3 <= (others => '0');
                y_s3 <= (others => '0');
                z_s3 <= (others => '0');
            elsif enable = '1' then
                -- alpha_arg = y - x - f(x)
                alpha_arg <= y_s2 - x_s2 - fx_s2;
                
                -- Pass through pipeline
                x_s3 <= x_s2;
                y_s3 <= y_s2;
                z_s3 <= z_s2;
            end if;
        end if;
    end process stage_3;

    ----------------------------------------------------------------------------
    -- STAGE 4: Compute derivatives
    -- SYNCHRONOUS multiplications inside process
    -- Two independent multiplications: alpha * alpha_arg, beta * y
    ----------------------------------------------------------------------------
    stage_4 : process(clk)
        variable mult_alpha : signed(63 downto 0);
        variable mult_beta  : signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                dx_s4 <= (others => '0');
                dy_s4 <= (others => '0');
                dz_s4 <= (others => '0');
                x_s4  <= (others => '0');
                y_s4  <= (others => '0');
                z_s4  <= (others => '0');
            elsif enable = '1' then
                -- Synchronous multiplications (parallel, not cascaded)
                mult_alpha := ALPHA * alpha_arg;
                mult_beta  := BETA * y_s3;
                
                -- Chua derivatives:
                -- dx = alpha * (y - x - f(x))
                -- dy = x - y + z
                -- dz = -beta * y
                dx_s4 <= mult_alpha(47 downto 16);
                dy_s4 <= x_s3 - y_s3 + z_s3;
                dz_s4 <= -mult_beta(47 downto 16);
                
                -- Pass through pipeline
                x_s4  <= x_s3;
                y_s4  <= y_s3;
                z_s4  <= z_s3;
            end if;
        end if;
    end process stage_4;

    ----------------------------------------------------------------------------
    -- STAGE 5: Euler integration
    -- SYNCHRONOUS multiplications inside process
    -- Three independent multiplications: dt * dx, dt * dy, dt * dz
    ----------------------------------------------------------------------------
    stage_5 : process(clk)
        variable mult_dtdx : signed(63 downto 0);
        variable mult_dtdy : signed(63 downto 0);
        variable mult_dtdz : signed(63 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                x_state <= to_signed(6554,  32);
                y_state <= (others => '0');
                z_state <= (others => '0');
            elsif enable = '1' then
                -- Synchronous multiplications (parallel, not cascaded)
                mult_dtdx := DT_C * dx_s4;
                mult_dtdy := DT_C * dy_s4;
                mult_dtdz := DT_C * dz_s4;
                
                -- Euler integration: state = state + dt * derivative
                x_state <= x_s4 + mult_dtdx(47 downto 16);
                y_state <= y_s4 + mult_dtdy(47 downto 16);
                z_state <= z_s4 + mult_dtdz(47 downto 16);
            end if;
        end if;
    end process stage_5;

    ----------------------------------------------------------------------------
    -- Valid tracking (5 stages for Chua vs 4 for Rössler)
    ----------------------------------------------------------------------------
    valid_tracking : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                valid_sr <= (others => '0');
            elsif enable = '1' then
                valid_sr <= valid_sr(3 downto 0) & '1';
            end if;
        end if;
    end process valid_tracking;

    ----------------------------------------------------------------------------
    -- Output assignments
    ----------------------------------------------------------------------------
    x_out        <= std_logic_vector(x_state);
    y_out        <= std_logic_vector(y_state);
    z_out        <= std_logic_vector(z_state);
    keystream    <= std_logic_vector(x_state(23 downto 8));
    output_valid <= valid_sr(4);

end architecture rtl;