@echo off
echo ================================================================================
echo PYNQ BOARD IP ADDRESS FINDER
echo ================================================================================
echo.
echo Checking for PYNQ boards on your network...
echo.

echo Method 1: Checking USB Direct Connection (192.168.2.99)
echo -----------------------------------------------------------------------
ping -n 1 -w 1000 192.168.2.99 >nul 2>&1
if %errorlevel%==0 (
    echo [SUCCESS] Board found at 192.168.2.99 (USB connection)
    echo.
    echo Try connecting with:
    echo   ssh xilinx@192.168.2.99
    echo   Password: xilinx
    echo.
    echo Or open browser:
    echo   http://192.168.2.99:9090
    echo   Password: xilinx
    goto :end
) else (
    echo [NOT FOUND] No board at 192.168.2.99
)
echo.

echo Method 2: Checking Common Router IP Ranges
echo -----------------------------------------------------------------------
echo Scanning 192.168.1.x network...
for /L %%i in (1,1,254) do (
    ping -n 1 -w 100 192.168.1.%%i >nul 2>&1
    if !errorlevel!==0 (
        echo   Found device at 192.168.1.%%i
    )
)
echo.

echo Scanning 192.168.0.x network...
for /L %%i in (1,1,254) do (
    ping -n 1 -w 100 192.168.0.%%i >nul 2>&1
    if !errorlevel!==0 (
        echo   Found device at 192.168.0.%%i
    )
)
echo.

echo Method 3: Check Network Adapters
echo -----------------------------------------------------------------------
ipconfig | findstr /i "IPv4 Ethernet USB"
echo.

echo ================================================================================
echo MANUAL STEPS TO FIND PYNQ BOARD:
echo ================================================================================
echo.
echo 1. Open browser and try these addresses:
echo    - http://192.168.2.99:9090  (USB direct connection)
echo    - http://pynq:9090          (if mDNS works)
echo.
echo 2. Check your router's admin page:
echo    - Usually at: http://192.168.1.1 or http://192.168.0.1
echo    - Look for "Connected Devices" or "DHCP Clients"
echo    - Find device named "pynq" or "xilinx"
echo.
echo 3. Check Windows Network:
echo    - Open File Explorer
echo    - Click "Network" in left sidebar
echo    - Look for "PYNQ" device
echo.
echo 4. Use Advanced Network Scanner:
echo    - Download: https://www.advanced-ip-scanner.com/
echo    - Scan your network
echo    - Look for device with hostname "pynq"
echo.
echo ================================================================================
echo TROUBLESHOOTING:
echo ================================================================================
echo.
echo If board is not found:
echo   1. Check green LED on board (should be solid, not blinking)
echo   2. Check Ethernet cable is connected
echo   3. Check USB cable is connected
echo   4. Try unplugging and replugging USB cable
echo   5. Wait 30 seconds after power-on for boot to complete
echo.
echo If you see the board's IP:
echo   ssh xilinx@[IP_ADDRESS]
echo   Password: xilinx
echo.
echo ================================================================================

:end
pause

@REM Made with Bob
