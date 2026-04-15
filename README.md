# 💶 Control de Préstamos Familiares

Aplicación web sencilla para llevar el recuento del dinero (en euros, €) que prestas a tus familiares. Diseñada para ser ligera, responsiva (móvil-first) y fácil de desplegar en un homelab.

## Funcionalidades

- **Dashboard** con resumen: Me Deben, Yo Debo, Balance Neto, Total Familiares
- **Lista de familiares** con su balance individual
- **Detalle por familiar** con historial de préstamos
- **Registrar préstamos**: yo presté (me deben) o me prestaron (yo debo)
- **Registrar pagos parciales** sobre cada préstamo
- **Eliminar** préstamos o familiares
- **Backup semanal** automático del fichero JSON

## Stack técnico

- **Python + Flask** — aplicación web
- **Gunicorn** — servidor WSGI de producción
- **JSON** — fichero como base de datos (`data/prestamos.json`)
- **Docker Compose** — despliegue con backup sidecar

## Despliegue rápido

### 1. Clonar el repositorio

```bash
git clone <repo-url> prestamos-familiares
cd prestamos-familiares
```

### 2. Configurar (opcional)

Edita `docker-compose.yml` para cambiar:
- **Puerto**: por defecto `8080` → cambia `8080:5000` si necesitas otro
- **SECRET_KEY**: cambia el valor por una clave segura

### 3. Levantar

```bash
docker compose up -d
```

La app estará disponible en `http://<tu-ip>:8080`

### 4. Parar

```bash
docker compose down
```

## Estructura de ficheros

```
├── app.py                  # Aplicación Flask
├── templates/
│   ├── base.html           # Layout base
│   ├── index.html          # Página principal
│   └── familiar.html       # Detalle de familiar
├── static/
│   └── style.css           # Estilos responsivos
├── data/
│   └── prestamos.json      # Base de datos (JSON)
├── backups/                # Backups semanales automáticos
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Datos

Toda la información se guarda en `data/prestamos.json`. Este fichero se monta como volumen Docker, así que persiste entre reinicios. **Todos los importes están en euros (€), con el símbolo al final (ejemplo: 123.45 €).**

### Backups

Un contenedor sidecar crea una copia de `prestamos.json` cada 7 días en la carpeta `backups/`. Se conservan los últimos 8 backups (≈2 meses).

Para hacer un backup manual:

```bash
cp data/prestamos.json backups/prestamos_manual_$(date +%Y%m%d).json
```

## Desarrollo local (sin Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
DATA_FILE=data/prestamos.json FLASK_DEBUG=1 python app.py
```

Abre `http://localhost:5000`
