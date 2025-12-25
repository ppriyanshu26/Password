@echo off
setlocal EnableDelayedExpansion

REM ========= CONFIG =========
set BASEDIR=%APPDATA%\Password-Manager
set CREDENTIALS=%BASEDIR%\credentials.json
set STARTUP_EXE=%BASEDIR%\Startup.exe
set MAIN_EXE=%BASEDIR%\Password-Manager.exe

set STARTUP_SHA=36cc6ab8e73fd60aaa2e6dd75fc688cfb04afe5e9768dc059c05118ab4f69607
set MAIN_SHA=dcfaf959122b42cf18c8ae7dc7324f22617da0cfa17ccb5bbd691d74e838f8e8

set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

set OK=[ OK ]
set FAIL=[FAIL]

cls
echo ==================================================
echo   Password Manager - System Integrity Analyzer
echo ==================================================
echo   Target Directory : %BASEDIR%
echo   Current User     : %USERNAME%
echo ==================================================
echo.

set PASSCOUNT=0

REM ========= 1. credentials.json =========
echo [1/5] credentials.json
echo     - File existence check
echo     - JSON format validation

set RESULT=%FAIL%
if exist "%CREDENTIALS%" (
    powershell -NoProfile -Command ^
      "try { Get-Content '%CREDENTIALS%' -Raw | ConvertFrom-Json | Out-Null; exit 0 } catch { exit 1 }"
    if !ERRORLEVEL! EQU 0 (
        set RESULT=%OK%
        set /a PASSCOUNT+=1
    )
)

echo     Result ...................................... %RESULT%
echo.

REM ========= 2. Startup.exe =========
echo [2/5] Startup.exe
echo     - File existence check
echo     - SHA256 fingerprint verification

set RESULT=%FAIL%
if exist "%STARTUP_EXE%" (
    for /f "tokens=1" %%H in ('
        certutil -hashfile "%STARTUP_EXE%" SHA256 ^| findstr /R /C:"^[0-9A-F]"
    ') do (
        if /I "%%H"=="%STARTUP_SHA%" (
            set RESULT=%OK%
            set /a PASSCOUNT+=1
        )
    )
)

echo     Result ...................................... %RESULT%
echo.

REM ========= 3. Password-Manager.exe =========
echo [3/5] Password-Manager.exe
echo     - File existence check
echo     - SHA256 fingerprint verification

set RESULT=%FAIL%
if exist "%MAIN_EXE%" (
    for /f "tokens=1" %%H in ('
        certutil -hashfile "%MAIN_EXE%" SHA256 ^| findstr /R /C:"^[0-9A-F]"
    ') do (
        if /I "%%H"=="%MAIN_SHA%" (
            set RESULT=%OK%
            set /a PASSCOUNT+=1
        )
    )
)

echo     Result ...................................... %RESULT%
echo.

REM ========= 4. Startup registration =========
echo [4/5] Startup registration
echo     - Startup folder shortcut inspection

set RESULT=%FAIL%
for %%L in ("%STARTUP_FOLDER%\*.lnk") do (
    powershell -NoProfile -Command ^
      "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%%~fL'); if ($s.TargetPath -eq '%STARTUP_EXE%') { exit 0 } else { exit 1 }"
    if !ERRORLEVEL! EQU 0 (
        set RESULT=%OK%
        set /a PASSCOUNT+=1
    )
)

echo     Result ...................................... %RESULT%
echo.

REM ========= 5. Windows Credential =========
echo [5/5] Windows Credential
echo     - Credential Manager lookup

set RESULT=%FAIL%
powershell -NoProfile -Command ^
  "cmdkey /list | Select-String 'Password Manager' > $null; if ($?) { exit 0 } else { exit 1 }"
if %ERRORLEVEL% EQU 0 (
    set RESULT=%OK%
    set /a PASSCOUNT+=1
)

echo     Result ...................................... %RESULT%
echo.

REM ========= SUMMARY =========
echo ==================================================
echo   Analysis Summary
echo ==================================================
echo   Passed Checks : %PASSCOUNT% / 5

if %PASSCOUNT% EQU 5 (
    echo   STATUS : SYSTEM INTEGRITY VERIFIED
) else (
    echo   STATUS : ATTENTION REQUIRED
)

echo ==================================================
echo.
pause
