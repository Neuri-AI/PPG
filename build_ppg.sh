#!/bin/bash

VERSION="1.2.0"

# copy package.json data to ppg/builtin_commands/
echo "🔄 Actualizando datos del paquete en setup.py..."
cp package.json ppg/builtin_commands/

echo "🧹 Limpiando builds anteriores..."
rm -rf build dist ppg.egg-info

echo "📦 Creando wheel para PPG v$VERSION..."
python setup.py sdist bdist_wheel

echo "📥 Instalando wheel local..."
pip uninstall -y ppg
pip install "dist/ppg-$VERSION-py3-none-any.whl"

echo "✅ Instalación completada para PPG v$VERSION"
