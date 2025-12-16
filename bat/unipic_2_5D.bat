@echo off
set EXE=D:\UNIPIC\Unipic2.5D_Training\UNIPIC20240819\bin\pic\Unipic2_5D.exe
set WORKDIR=D:\AAA_PIC\Parser\MCL_PLYParser\src\data\TM03_60GHz_Double\Simulation
set BINPATH=D:\UNIPIC\Unipic2.5D_Training\UNIPIC20240819\bin\pic

echo Running Unipic2.5D...

REM 临时把 exe 所在目录加入 PATH
set PATH=%BINPATH%;%PATH%

"%EXE%" -wd "%WORKDIR%"

pause
