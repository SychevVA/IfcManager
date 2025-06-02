@echo off
setlocal enabledelayedexpansion

:: Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python не установлен! Пожалуйста, установите Python с сайта https://www.python.org/downloads/
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

:: Проверка наличия pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip не установлен! Пожалуйста, переустановите Python с включенным pip.
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
    exit /b 1
)

:: Проверка и установка необходимых пакетов
echo Проверка необходимых пакетов...
python -m pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo Ошибка при установке зависимостей!
    echo Попытка установить пакеты по отдельности...
    
    :: Установка основных зависимостей
    python -m pip install ttkbootstrap
    python -m pip install ifcopenshell
    python -m pip install ifctester
    python -m pip install beautifulsoup4
    
    if %errorlevel% neq 0 (
        echo Не удалось установить необходимые пакеты!
        echo Пожалуйста, проверьте подключение к интернету и попробуйте снова.
        echo.
        echo Нажмите любую клавишу для выхода...
        pause >nul
        exit /b 1
    )
)

:: Запуск программы
echo Запуск IFC Manager...
python main.py

:: Если программа завершилась с ошибкой
if %errorlevel% neq 0 (
    echo.
    echo Программа завершилась с ошибкой!
    echo Проверьте журнал операций для получения дополнительной информации.
    echo.
    echo Нажмите любую клавишу для выхода...
    pause >nul
)

endlocal 