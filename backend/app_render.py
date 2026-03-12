#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import threading
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor
import re
import time
from datetime import datetime
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ===== CONFIGURACIÓN =====
TIMEOUT = 5
MAX_WORKERS = 50

# ===== PUERTOS COMUNES IPTV (de tu script) =====
IPTV_PORTS = [
    80, 443, 21, 22, 23,
    25461, 25462, 25463, 25464, 25465, 25466, 25467, 25468, 25469,
    2082, 2083, 2086, 2087, 2095, 2096,
    8080, 8081, 8082, 8083, 8084, 8085, 8086, 8088, 8089,
    8880, 8881, 8888, 8889, 8899,
    8181, 8182, 8183, 8090, 8091, 8095, 8099,
    8200, 8280, 8383, 8443, 8883, 9443,
    2053, 2052, 2083, 2087, 2020, 2021, 2022,
    2222, 2323, 2468, 3000, 3001, 3010, 3020, 3030, 3128,
    4000, 4040, 4443, 4500, 5000, 5001, 5050, 5080,
    5100, 5200, 5600, 5800, 5900, 6000, 6001, 6060,
    6666, 6767, 7000, 7001, 7070, 7171, 7200, 7777,
    8000, 8001, 8010, 8020, 8333, 8443, 8500, 8600,
    9000, 9001, 9010, 9020, 9090, 9091, 9443, 9990, 9999
]

# ===== CREDENCIALES COMUNES (de tu script) =====
COMMON_CREDS = [
    ('admin', 'admin'), ('admin', '1234'), ('admin', 'password'),
    ('admin', '123456'), ('admin', 'admin123'), ('admin', '12345'),
    ('root', 'root'), ('root', 'toor'), ('root', '123456'),
    ('user', 'user'), ('user', '1234'), ('test', 'test'),
    ('test', '1234'), ('demo', 'demo'), ('demo', '1234'),
    ('administrator', 'administrator'), ('guest', 'guest'),
    ('support', 'support'), ('ftp', 'ftp'), ('mysql', 'mysql'),
    ('postgres', 'postgres'), ('oracle', 'oracle'), ('tomcat', 'tomcat'),
    ('manager', 'manager'), ('supervisor', 'supervisor')
]

# ===== FUNCIÓN DE GEOLOCALIZACIÓN (de tu script) =====
def get_ip_location(ip: str) -> dict:
    """Obtiene localización de IP usando ip-api.com (GRATIS)"""
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('status') == 'success':
                location = ""
                if data.get('city'):
                    location += data['city'] + ", "
                if data.get('regionName'):
                    location += data['regionName'] + ", "
                if data.get('country'):
                    location += data['country']
                
                location = location.strip(', ')
                
                country_code = data.get('countryCode', '')
                flag = '🌍'
                if country_code and len(country_code) == 2:
                    try:
                        flag = ''.join(chr(ord(c.upper()) + 127397) for c in country_code)
                    except:
                        pass
                
                return {
                    'location': location if location else 'Ubicación desconocida',
                    'country_flag': flag,
                    'isp': data.get('isp', ''),
                    'org': data.get('org', '')
                }
    except:
        pass
    
    return {
        'location': 'No disponible',
        'country_flag': '🌍',
        'isp': '',
        'org': ''
    }

# ===== FUNCIÓN PARA OBTENER PROXYS GRATIS =====
def get_free_proxies():
    """Obtiene proxies gratis de fuentes públicas (de tu script)"""
    proxies = []
    sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000",
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
    ]
    
    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                for line in r.text.strip().split('\n'):
                    proxy = line.strip()
                    if ':' in proxy:
                        proxies.append(proxy)
                        if len(proxies) >= 50:
                            break
        except:
            continue
    
    return list(set(proxies))[:30]  # Devolver hasta 30 proxies únicos

# ===== FUNCIÓN PRINCIPAL DE ESCANEO (usa sockets REALES) =====
def scan_port_real(host, port):
    """Escaneo REAL usando socket (igual que en tu script)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            # Puerto abierto
            service_name = get_service_name(port)
            
            # Intentar obtener banner
            banner = ""
            try:
                if port in [80, 8080, 8888, 25461, 25462]:
                    sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                    banner = sock.recv(1024).decode('utf-8', errors='ignore')[:100]
                elif port in [21, 22, 23]:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore')[:100]
            except:
                pass
            
            sock.close()
            
            return {
                'port': port,
                'open': True,
                'service': service_name,
                'banner': banner,
                'vulnerabilities': detect_vulnerabilities(host, port)
            }
        sock.close()
        return {'port': port, 'open': False}
    except Exception as e:
        return {'port': port, 'open': False, 'error': str(e)}

def get_service_name(port):
    """Identifica servicio por puerto"""
    services = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 80: 'HTTP',
        110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 993: 'IMAPS',
        995: 'POP3S', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
        5900: 'VNC', 6379: 'Redis', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt',
        25461: 'IPTV', 25462: 'IPTV', 25463: 'IPTV', 25464: 'IPTV', 25465: 'IPTV',
        8888: 'HTTP-Proxy', 8081: 'HTTP-Alt2'
    }
    return services.get(port, f'Port-{port}')

def detect_vulnerabilities(host, port):
    """Detecta vulnerabilidades básicas"""
    vulns = []
    
    # FTP anónimo
    if port == 21:
        try:
            import ftplib
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=3)
            ftp.login()
            vulns.append({'type': 'ftp_anonymous', 'risk': 'high'})
            ftp.quit()
        except:
            pass
    
    # HTTP con paneles comunes
    if port in [80, 8080, 8888, 25461, 25462]:
        try:
            url = f"http://{host}:{port}/panel.php"
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                vulns.append({'type': 'panel_access', 'risk': 'medium'})
        except:
            pass
    
    return vulns

# ===== RUTAS API =====
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'version': '5.0 - ULTIMATE EDITION',
        'ports_available': len(IPTV_PORTS),
        'message': '🔥 CHERRY BACKEND CON TECNOLOGÍA ULTIMATE HOST'
    })

@app.route('/api/scan', methods=['POST'])
def scan():
    data = request.json
    host = data.get('host', '').strip()
    ports_str = data.get('ports', '').strip()
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    # Limpiar host
    host = host.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]
    
    # Parsear puertos
    port_list = []
    if ports_str:
        for p in ports_str.split(','):
            try:
                port_list.append(int(p.strip()))
            except:
                pass
    else:
        port_list = IPTV_PORTS
    
    # Limitar a 50 puertos para rendimiento
    if len(port_list) > 50:
        port_list = port_list[:50]
    
    # Escaneo REAL con threads
    results = []
    open_ports = []
    
    print(f"Escaneando {host} con {len(port_list)} puertos...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scan_port_real, host, p): p for p in port_list}
        for future in futures:
            try:
                result = future.result(timeout=TIMEOUT+2)
                results.append(result)
                if result.get('open'):
                    open_ports.append(result)
            except:
                results.append({'port': futures[future], 'open': False})
    
    # Geolocalización
    location = get_ip_location(host)
    
    # Obtener proxies gratis (opcional)
    proxies = get_free_proxies()
    
    return jsonify({
        'host': host,
        'location': location,
        'results': results,
        'open_ports': open_ports,
        'total': len(results),
        'open_count': len(open_ports),
        'proxies_available': len(proxies),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/scan-quick', methods=['POST'])
def scan_quick():
    """Escaneo rápido de solo puertos críticos IPTV"""
    data = request.json
    host = data.get('host', '').strip()
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    host = host.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]
    
    # Puertos críticos IPTV (los más comunes)
    critical_ports = [80, 443, 8080, 8443, 8888, 25461, 25462, 25463, 8081]
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_port_real, host, p): p for p in critical_ports}
        for future in futures:
            try:
                result = future.result(timeout=3)
                results.append(result)
            except:
                pass
    
    return jsonify({
        'host': host,
        'results': results,
        'open_ports': [r for r in results if r.get('open')]
    })

@app.route('/api/proxies', methods=['GET'])
def get_proxies():
    """Endpoint para obtener proxies gratis"""
    proxies = get_free_proxies()
    return jsonify({
        'proxies': proxies,
        'count': len(proxies),
        'source': 'public_lists'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🍒 CHERRY BACKEND - ULTIMATE HOST EDITION")
    print("="*60)
    print(f"📋 Puertos configurados: {len(IPTV_PORTS)}")
    print(f"🔧 Escaneo REAL con sockets")
    print(f"🌍 Geolocalización vía ip-api.com")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
