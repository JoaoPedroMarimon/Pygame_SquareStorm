@echo off
echo ========================================
echo  CONFIGURAR FIREWALL PARA MULTIPLAYER
echo ========================================
echo.
echo Este script abrira a porta 5555 no firewall do Windows
echo para permitir conexoes multiplayer.
echo.
echo IMPORTANTE: Execute como Administrador!
echo (Clique com botao direito e escolha "Executar como administrador")
echo.
pause

netsh advfirewall firewall add rule name="SquareStorm Multiplayer" dir=in action=allow protocol=TCP localport=5555

echo.
echo ========================================
if %errorlevel% == 0 (
    echo SUCESSO! Porta 5555 liberada no firewall
) else (
    echo ERRO! Execute este arquivo como Administrador
)
echo ========================================
echo.
pause
