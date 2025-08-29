{ pkgs }:

let
  # Указываем, что хотим использовать python311
  pythonEnv = pkgs.python311.withPackages (ps: with ps; [
    # Подключаем необходимые инструменты для сборки
    setuptools
    wheel
    pkg-config
    # Библиотеки, которые могут потребовать системных зависимостей
    # Для opencv-python-headless и numpy, Nixpkgs обычно хорошо их собирает
    # Если возникнут другие ошибки сборки, сюда можно добавливать системные пакеты
  ]);
in
pkgs.mkShell {
  # Здесь мы устанавливаем Python и pip
  packages = [
    pythonEnv
    # Дополнительные системные пакеты, если понадобятся для других библиотек
    # Например, для некоторых OpenCV зависимостей могут потребоваться:
    # pkgs.libjpeg
    # pkgs.zlib
    # pkgs.libpng
  ];

  # Переменные окружения, которые будут доступны во время сборки
  # Например, чтобы pip знал, где искать установленный Python
  shellHook = ''
    export PATH="$(/opt/venv/bin/python -m site --user-base)/bin:$PATH"
    # Устанавливаем pip и setuptools заранее
    ${pythonEnv}/bin/pip install --upgrade pip setuptools wheel
    # Устанавливаем зависимости
    ${pythonEnv}/bin/pip install -r requirements.txt
  '';
}
