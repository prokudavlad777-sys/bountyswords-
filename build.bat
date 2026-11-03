@echo off
chcp 65001 >nul
echo [1/3] Збірка C++ бібліотеки...
g++ -O2 -shared -static-libgcc -static-libstdc++ -o voice_dsp.dll effects.cpp || goto :err
echo [2/3] Встановлення залежностей...
pip install -r requirements.txt pyinstaller || goto :err
echo [3/3] Збірка EXE...
pyinstaller --noconfirm --onefile --noconsole --name VoiceChanger --icon icon.ico --add-binary "voice_dsp.dll;." --add-data "icon.ico;." --collect-all sounddevice voice_changer.py || goto :err
echo.
echo Готово: dist\VoiceChanger.exe
pause
exit /b 0
:err
echo.
echo ПОМИЛКА збірки. Потрібні Python, pip і g++ (MinGW) у PATH.
pause
exit /b 1
