#!/usr/bin/env fish

echo "🔧 CONFIGURACIÓN DEL ENTORNO VIRTUAL"
echo "====================================="

# Activar entorno virtual (Fish shell)
source venv/bin/activate.fish

echo ""
echo "✅ Entorno virtual activado"
echo "📦 Versión de Python:"
python --version

echo ""
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "🧪 Ejecutando test de inicialización..."
python test_sql_init.py

echo ""
echo "====================================="
echo "✅ Setup completado!"
echo ""
echo "Para activar el venv manualmente (Fish shell):"
echo "  source venv/bin/activate.fish"
echo ""
echo "Para iniciar el backend:"
echo "  uvicorn app.main:app --reload"
