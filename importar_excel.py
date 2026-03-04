import csv
import os
from database import SessionLocal
from models import WhiteList

def importar_socios():
    print("--- 🔍 INICIANDO DIAGNÓSTICO ---")
    
    # 1. Verificar dónde estamos parados
    directorio_actual = os.getcwd()
    print(f"📂 Estoy buscando en la carpeta: {directorio_actual}")
    
    archivo = "socios.csv"
    ruta_completa = os.path.join(directorio_actual, archivo)
    
    # 2. Verificar si el archivo existe
    if not os.path.exists(ruta_completa):
        print(f"❌ ERROR FATAL: No encuentro el archivo '{archivo}' en esta carpeta.")
        print("👉 Asegúrate de crearlo y guardarlo en la misma carpeta que este script.")
        return

    print(f"✅ Archivo encontrado. Abriendo...")

    try:
        db = SessionLocal()
        contador = 0
        
        with open(ruta_completa, mode='r', encoding='utf-8') as file:
            lector = csv.reader(file)
            filas = list(lector) # Leemos todo a la memoria para contar
            
            print(f"📊 El archivo tiene {len(filas)} líneas.")
            
            if len(filas) == 0:
                print("⚠️ El archivo está VACÍO. Escribe algo adentro y guarda.")
                return

            for fila in filas:
                if len(fila) < 2: 
                    print(f"⚠️ Línea ignorada (incompleta): {fila}")
                    continue
                
                nombre = fila[0].strip()
                telefono = fila[1].strip()
                
                print(f"Processing: {nombre} - {telefono}")

                existe = db.query(WhiteList).filter_by(phone_number=telefono).first()
                if existe:
                    print(f"   -> Ya existe.")
                else:
                    nuevo = WhiteList(phone_number=telefono, full_name=nombre, club_id=1, is_active=True)
                    db.add(nuevo)
                    contador += 1
                    print(f"   -> ✅ Agregado.")
        
        db.commit()
        db.close()
        print(f"\n🎉 FIN. Se agregaron {contador} socios.")

    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    importar_socios()