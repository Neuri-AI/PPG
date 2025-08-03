@echo off
set VERSION=1.2.0

echo 🔄 Actualizando datos del paquete en setup.py...
copy package.json ppg\builtin_commands\ /Y

echo 🧹 Limpiando builds anteriores...
rmdir /s /q build
rmdir /s /q dist
rmdir /s /q ppg.egg-info

echo 📦 Creando wheel para PPG v%VERSION%...
python setup.py sdist bdist_wheel

echo 📥 Instalando wheel local...
pip uninstall -y ppg
pip install dist\ppg-%VERSION%-py3-none-any.whl

echo ✅ Instalacion completada para PPG v%VERSION%
