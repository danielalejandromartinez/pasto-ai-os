import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ESTE Base ES EL ÚNICO Y VERDADERO (Los cimientos de nuestro rascacielos)
Base = declarative_base()

# --- 🛡️ MEJORA DE ROBUSTEZ: DETECCIÓN DE ENTORNO ---
# Render inyecta automáticamente la variable 'RENDER'. Si no existe, estamos en LOCAL.
IS_RENDER = os.getenv("RENDER") is not None

if IS_RENDER:
    # 1. MODO PRODUCCIÓN (La Caja Fuerte de Titanio en Render)
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Parche de compatibilidad para servidores modernos
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
    print("\033[1;96m☁️ [DATABASE] -> Conectando a la Caja Fuerte de Titanio (PostgreSQL) en la Nube.\033[0m")
    
    engine = create_engine(
        DATABASE_URL,
        pool_size=25,
        max_overflow=15,
        pool_timeout=60,
        pool_pre_ping=True,
        pool_recycle=1800
    )
else:
    # 2. MODO LABORATORIO (La Libreta Local en tu PC)
    # Forzamos SQLite en local para que no intente usar la URL de Render de tu .env
    DATABASE_URL = "sqlite:///./club_squash.db"
    
    print("\033[1;33m💻 [DATABASE] -> Conectando a la Libreta Local (SQLite).\033[0m")
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False} # Permite que Alejandro haga varias cosas a la vez
    )
# --------------------------------------------------

# 3. Fábrica de Sesiones (Donde se firman los cambios)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. El Portero de Datos (Para que main.py abra y cierre la conexión)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()