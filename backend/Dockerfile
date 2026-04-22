# Imagen base oficial de Python slim (menor tamaño)
FROM python:3.12-slim

# Evita que Python escriba .pyc y que bufferice stdout/stderr
# Importante para que los logs de Loguru aparezcan en tiempo real en Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiamos solo requirements primero para aprovechar la caché de Docker
# Si el código cambia pero no las dependencias, no reinstala todo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código
COPY . .

# Puerto que expone la API
EXPOSE 8000

# Comando de arranque en modo producción (sin --reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]