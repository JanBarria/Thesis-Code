--------------------------------------------------------------------------------
-- File        : rossler_pipelined.vhd
-- Description : 4-stage pipelined Rossler chaotic oscillator, stepped operation
--               Fixed-point Q16.16. State updates only on state_step pulse.
--
-- Generics:
--   Y0_INIT, Z0_INIT - initial y/z state (Q16.16 integers)
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity rossler_pipelined is
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
end entity rossler_pipelined;

architecture rtl of rossler_pipelined is

    constant A_PARAM  : signed(31 downto 0) := to_signed(13107,  32);
    constant B_PARAM  : signed(31 downto 0) := to_signed(13107,  32);
    constant C_PARAM  : signed(31 downto 0) := to_signed(373554, 32);
    constant DT_PARAM : signed(31 downto 0) := to_signed(655,    32);

    signal x_state : signed(31 downto 0) := to_signed(65536, 32);
    signal y_state : signed(31 downto 0) := to_signed(Y0_INIT, 32);
    signal z_state : signed(31 downto 0) := to_signed(Z0_INIT, 32);

    signal x_s0, y_s0, z_s0 : signed(31 downto 0) := (others => '0');
    signal ay_s1, x_sub_c, x_s1, y_s1, z_s1 : signed(31 downto 0) := (others => '0');
    signal z_x_c_s2, ay_s2, x_s2, y_s2, z_s2 : signed(31 downto 0) := (others => '0');
    signal dx_s3, dy_s3, dz_s3, x_s3, y_s3, z_s3 : signed(31 downto 0) := (others => '0');

    signal mult_ay, mult_zxc, mult_dtdx, mult_dtdy, mult_dtdz : signed(63 downto 0);

begin

    mult_ay   <= A_PARAM * y_s0;
    mult_zxc  <= z_s1 * x_sub_c;
    mult_dtdx <= DT_PARAM * dx_s3;
    mult_dtdy <= DT_PARAM * dy_s3;
    mult_dtdz <= DT_PARAM * dz_s3;

    stage_0 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                x_s0 <= (others => '0'); y_s0 <= (others => '0'); z_s0 <= (others => '0');
            else
                if sync_enable = '1' then x_s0 <= signed(x_drive);
                else x_s0 <= x_state; end if;
                y_s0 <= y_state; z_s0 <= z_state;
            end if;
        end if;
    end process;

    stage_1 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ay_s1 <= (others=>'0'); x_sub_c <= (others=>'0');
                x_s1 <= (others=>'0'); y_s1 <= (others=>'0'); z_s1 <= (others=>'0');
            else
                ay_s1   <= mult_ay(47 downto 16);
                x_sub_c <= x_s0 - C_PARAM;
                x_s1 <= x_s0; y_s1 <= y_s0; z_s1 <= z_s0;
            end if;
        end if;
    end process;

    stage_2 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                z_x_c_s2 <= (others=>'0'); ay_s2 <= (others=>'0');
                x_s2 <= (others=>'0'); y_s2 <= (others=>'0'); z_s2 <= (others=>'0');
            else
                z_x_c_s2 <= mult_zxc(47 downto 16);
                ay_s2 <= ay_s1; x_s2 <= x_s1; y_s2 <= y_s1; z_s2 <= z_s1;
            end if;
        end if;
    end process;

    stage_3 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                dx_s3 <= (others=>'0'); dy_s3 <= (others=>'0'); dz_s3 <= (others=>'0');
                x_s3 <= (others=>'0'); y_s3 <= (others=>'0'); z_s3 <= (others=>'0');
            else
                dx_s3 <= (- y_s2) - z_s2;
                dy_s3 <= x_s2 + ay_s2;
                dz_s3 <= B_PARAM + z_x_c_s2;
                x_s3 <= x_s2; y_s3 <= y_s2; z_s3 <= z_s2;
            end if;
        end if;
    end process;

    stage_4 : process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                x_state <= to_signed(65536, 32);
                y_state <= to_signed(Y0_INIT, 32);
                z_state <= to_signed(Z0_INIT, 32);
            elsif state_step = '1' then
                x_state <= x_s3 + mult_dtdx(47 downto 16);
                y_state <= y_s3 + mult_dtdy(47 downto 16);
                z_state <= z_s3 + mult_dtdz(47 downto 16);
            end if;
        end if;
    end process;

    x_out     <= std_logic_vector(x_state);
    y_out     <= std_logic_vector(y_state);
    z_out     <= std_logic_vector(z_state);
    keystream <= std_logic_vector(x_state(23 downto 8));

end architecture rtl;