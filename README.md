# Змінювач голосу

Легка програма для зміни голосу в реальному часі.
Python (вікно, звук) + C++ (обробка звуку). Просте біле вікно без меню.

**Ефекти:** свій тон (-12…+12 півтонів), білка, демон, робот, луна.

## Готовий EXE

Збирається автоматично на GitHub:

1. Завантаж проєкт у репозиторій на GitHub (гілка `main`).
2. Відкрий вкладку **Actions → Build EXE** і дочекайся зеленої позначки.
3. Скачай `VoiceChanger.exe` у розділі **Artifacts**.

Щоб exe з'явився в **Releases**, створи тег: `git tag v1.0 && git push --tags`.

## Збірка EXE локально (Windows)

Потрібні Python 3.9+ та g++ (MinGW) у PATH. Далі просто запусти `build.bat`.
Результат: `dist\VoiceChanger.exe`.

## Запуск з коду

```
pip install -r requirements.txt
g++ -O2 -shared -static-libgcc -static-libstdc++ -o voice_dsp.dll effects.cpp
python voice_changer.py
```

## Щоб Discord чи гра чули змінений голос

1. Встанови [VB-Cable](https://vb-audio.com/Cable/).
2. У програмі в полі «Вихід» обери `CABLE Input`.
3. У Discord/грі як мікрофон обери `CABLE Output`.

Слухай через навушники, щоб не було відлуння.

## Файли

| Файл | Призначення |
|------|-------------|
| `voice_changer.py` | вікно (tkinter) і звук (sounddevice) |
| `effects.cpp` | ефекти на C++ |
| `icon.ico` / `icon.png` | іконка |
| `build.bat` | локальна збірка exe |
| `.github/workflows/build.yml` | автозбірка exe на GitHub |
