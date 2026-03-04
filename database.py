import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ESTE Base ES EL ÚNICO Y VERDADERO (Los cimientos de nuestro rascacielos)
Base = declarative_base()

# 1. Búsqueda de la dirección de la base de datos (Nube vs Local)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./club_squash.db")

# 2. Lógica Bilingüe y Blindaje de Concurrencia
if DATABASE_URL.startswith("postgres"):
    # --- MODO PRODUCCIÓN (La Caja Fuerte de Titanio en Render) ---
    print("\033[1;96m☁️ [DATABASE] -> Conectando a la Caja Fuerte de Titanio (PostgreSQL) en la Nube.\033[0m")
    
    # Parche de compatibilidad para servidores modernos
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
    # Motor de alta capacidad para la Junta Directiva
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,          # 20 carriles de datos abiertos
        max_overflow=10,       # 10 carriles extra para emergencias
        pool_timeout=30,       # Espera 30 segundos antes de rendirse
        pool_pre_ping=True     # Verifica que la base esté viva antes de entrar
    )
else:
    # --- MODO LABORATORIO (La Libreta Local en tu PC) ---
    print("\033[1;33m💻 [DATABASE] -> Conectando a la Libreta Local (SQLite).\033[0m")
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False} # Permite que Alejandro haga varias cosas a la vez
    )

# 3. Fábrica de Sesiones (Donde se firman los cambios)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. El Portero de Datos (Para que main.py abra y cierre la conexión)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()