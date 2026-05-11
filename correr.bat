@echo off
cd /d "C:\Users\USUARIO\Desktop\bot_whatsapp\.claude\worktrees\nifty-margulis-b52c27\postulaciones"

echo === [1/4] Postulando en portales (Computrabajo, ZonaJobs, BumerAN) ===
python postular.py

echo.
echo === [2/4] Leyendo vacantes de Gmail ===
python leer_vacantes.py

echo.
echo === [3/4] Generando cartas y borradores Gmail ===
python main.py

echo.
echo === Listo! Abri Gmail y revisa los borradores ===
pause
