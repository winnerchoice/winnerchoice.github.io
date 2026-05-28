#!/usr/bin/env python3
import json
import os
import urllib.request
import re
from datetime import datetime

def obtener_fecha_activa_oasis():
    url_oasis = "http://eloasiss.com/revistas_gac.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        req = urllib.request.Request(url_oasis, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # Busca cualquier patrón de descarga para extraer la fecha que el sitio tiene activa hoy
        patron = r'descargas/revista/download/(\d{4}-\d{2}-\d{2})/'
        coincidencia = re.search(patron, html)
        
        if coincidencia:
            return coincidencia.group(1)
        
        # Respaldo en caso de que no lea el HTML, usar fecha actual del sistema
        return datetime.now().strftime("%Y-%m-%d")
    except Exception as e:
        print(f"⚠️ Error conectando a El Oasis: {e}")
        return datetime.now().strftime("%Y-%m-%d")

def descargar_revista(fecha, codigo, destino):
    url_pdf = f"http://eloasiss.com/descargas/revista/download/{fecha}/{codigo}.pdf"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        req = urllib.request.Request(url_pdf, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(destino, 'wb') as f:
                f.write(response.read())
        return True
    except:
        # Si da error 404 o similar, asumimos con seguridad que no hay jornadas para este hipódromo hoy
        return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    ruta_originales = os.path.join(root_dir, "data", "urls_originales.json")
    ruta_salida = os.path.join(root_dir, "data", "revistas.json")
    ruta_pdfs = os.path.join(root_dir, "pdfs")
    
    if not os.path.exists(ruta_originales):
        print("Error: No se encontró urls_originales.json")
        return

    with open(ruta_originales, "r", encoding="utf-8") as f:
        fuente_data = json.load(f)
        
    fecha_oasis = obtener_fecha_activa_oasis()
    print(f"Procesando revistas de El Oasis para la fecha: {fecha_oasis}")
    
    data_web = {
        "metadata": {
            "lastUpdate": datetime.now().isoformat(),
            "fechaCartelera": fecha_oasis,
            "totalHipodromos": len(fuente_data.get("hipodromos", []))
        },
        "hipodromos": []
    }
    
    for hipo in fuente_data.get("hipodromos", []):
        id_hipo = hipo["id"]
        codigo = hipo["codigo_oasis"]
        nombre_archivo = f"{codigo}.pdf"
        destino_local = os.path.join(ruta_pdfs, nombre_archivo)
        
        print(f" -> Verificando: {hipo['nombre']} ({codigo}.pdf)...")
        exito = descargar_revista(fecha_oasis, codigo, destino_local)
        
        ruta_final_pdf = f"pdfs/{nombre_archivo}" if exito else "#"
        
        data_web["hipodromos"].append({
            "id": id_hipo,
            "nombre": hipo["nombre"],
            "logo": hipo["logo"],
            "revistas": {
                "espanol": ruta_final_pdf
            },
            "activo": exito,
            "ultimaActualizacion": datetime.now().strftime("%Y-%m-%d")
        })
        
        print(f"    Resultado -> {'[ACTIVO]' if exito else '[NO JUEGA]'}")
        
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(data_web, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
