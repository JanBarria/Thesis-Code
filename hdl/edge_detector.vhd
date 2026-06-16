--------------------------------------------------------------------------------
-- File        : edge_detector.vhd
-- Description : Rising-edge detector — converts a level input (e.g. from AXI GPIO)
--               into a single-cycle pulse synchronous to clk.
--
-- Why this exists:
--   The rossler_pipelined core expects state_step to be HIGH for exactly one
--   clock cycle to atomically advance state. Python cannot guarantee a
--   1-cycle write through AXI GPIO, so it instead toggles a "trigger" bit
--   and we synthesize the true 1-cycle pulse from its rising edge here.
--
-- Typical use:
--   trig_in  ← bit from AXI GPIO control register (held HIGH by Python)
--   pulse_out → state_step inputs of master and slave Rössler instances
--
--   Python sequence to issue one step:
--     1. write trigger bit = 1   (rising edge detected → pulse emitted)
--     2. write trigger bit = 0   (re-arms for next pulse)
--
-- Synchronization note:
--   trig_in is from PS clock domain (AXI bus). If your PL clock differs from
--   the AXI clock, instantiate an upstream 2-FF synchronizer. On the
--   chaos_sync_single_board top this is fine because we run the whole thing
--   off the PL clock and AXI GPIO updates are settled long before any pulse.
--------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity edge_detector is
    port (
        clk       : in  std_logic;
        rst       : in  std_logic;
        trig_in   : in  std_logic;
        pulse_out : out std_logic
    );
end entity edge_detector;

architecture rtl of edge_detector is
    signal trig_prev : std_logic := '0';
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                trig_prev <= '0';
            else
                trig_prev <= trig_in;
            end if;
        end if;
    end process;

    pulse_out <= trig_in and (not trig_prev);

end architecture rtl;
