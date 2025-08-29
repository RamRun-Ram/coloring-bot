{ pkgs }:
with pkgs;

# Определяем, какие пакеты нам нужны
let
  pythonEnv = python311.withPackages (ps: with ps; [
    # pip и setuptools обязательны
    pip
    setuptools
    wheel

    # Библиотеки, которые мы устанавливаем из requirements.txt
    # NumPy и OpenCV теперь будут собираться Nix, а не pip
    # Поэтому их напрямую здесь включать необязательно,
    # но мы обеспечим, чтобы они устанавливались в правильной среде.

    # Пакеты, нужные для сборки C-расширений (например, для numpy/opencv)
    # Это могут быть:
    pkgs.pkg-config # Инструмент для поиска библиотек
    pkgs.gcc # Компилятор C/C++
    pkgs.gnumake # Инструмент для управления сборкой
    pkgs.cmake # Система управления сборкой
    pkgs.libglvnd # Для OpenCV
    pkgs.libjpeg # Для обработки изображений
    pkgs.zlib # Для обработки изображений
    pkgs.libpng # Для обработки изображений
  ]);
in
# Создаем окружение для сборки
mkShell {
  packages = [
    pythonEnv

    # Системные зависимости, которые могут быть нужны для сборки
    # Если будут ошибки, можно добавлять сюда пакеты из nixos.org/packages
    # Например, для OpenCV может потребоваться ffmpeg, если будут проблемы
  ];

  # Команды, которые выполняются при активации оболочки
  # Здесь мы устанавливаем зависимости через pip
  shellHook = ''
    # Убедимся, что pip и setuptools обновлены
    ${pythonEnv}/bin/python -m pip install --upgrade pip setuptools wheel

    # Установка всех зависимостей из requirements.txt
    # Pip будет использовать уже установленный в Nix Python 3.11
    ${pythonEnv}/bin/pip install -r requirements.txt

    # Если pip все равно не находит distutils, это означает,
    # что сам Python 3.11, предоставленный Nix, не имеет его,
    # и придется искать обходные пути или явно добавлять его в buildInputs.
    # Но обычно Nixpkgs включает все необходимое для стандартных пакетов.
  '';
}
