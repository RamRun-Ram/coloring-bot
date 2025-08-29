{ pkgs, runCommand, python }:

let
  # Прямое указание использовать python311 из Nixpkgs
  python_3_11 = pkgs.python311;

  # Устанавливаем python311 и его пакеты, включая инструменты для сборки
  # Важно: Здесь мы не используем .withPackages, а собираем среду целиком
  pythonEnvWithBuildTools = pkgs.mkShell {
    packages = with pkgs; [
      # Сам Python 3.11
      python_3_11

      # Системные зависимости для компиляции
      gcc
      gnumake
      cmake
      pkg-config
      libglvnd
      libjpeg
      zlib
      libpng

      # Устанавливаем pip и setuptools через Nix, чтобы они были доступны
      # и гарантированно работали с Python 3.11
      # Это может помочь обойти проблемы с ModuleNotFoundError: No module named 'distutils'
      # путем предоставления правильной версии setuptools, которая знает, как собрать без distutils
      # или с альтернативами, если таковые в Nixpkgs реализованы.
      python_3_11.pkgs.pip
      python_3_11.pkgs.setuptools
      python_3_11.pkgs.wheel
    ];

    # Добавляем Python 3.11 bin в PATH
    shellHook = ''
      export PATH="${python_3_11}/bin:$PATH"

      # Убедимся, что pip и setuptools работают корректно
      # и что мы используем именно тот Python, что установлен Nix
      ${python_3_11}/bin/python -m pip install --upgrade pip setuptools wheel

      # Установка зависимостей из requirements.txt
      # Теперь pip должен работать в среде, управляемой Nix,
      # и использовать нужные версии инструментов.
      ${python_3_11}/bin/pip install -r requirements.txt
    '';
  };
in
pythonEnvWithBuildTools
