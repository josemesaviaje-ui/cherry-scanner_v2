#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import threading
import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor
import ftplib
import re
import time
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ===== CONFIGURACIÓN =====
TIMEOUT = 3
MAX_WORKERS = 100

# ===== PUERTOS IPTV COMPLETOS =====
IPTV_PORTS = [
    80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 443, 444, 445,
    8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089,
    8443, 8444, 8445, 8446, 8447, 8448, 8449,
    8880, 8881, 8882, 8883, 8884, 8885, 8886, 8887, 8888, 8889,
    2082, 2083, 2086, 2087, 2095, 2096, 2052, 2053,
    25461, 25462, 25463, 25464, 25465, 25466, 25467, 25468, 25469, 25470,
    25500, 25501, 25502, 25503, 25504, 25505,
    1935, 1936, 1937, 1938, 1939, 1940, 554, 8554,
    5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009,
    3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009,
    4000, 4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008, 4009,
    6000, 6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009,
    7000, 7001, 7002, 7003, 7004, 7005, 7006, 7007, 7008, 7009,
    8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009,
    9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009,
    10000, 10001, 10002, 10003, 10004, 10005, 11000, 12000, 13000,
    14000, 15000, 16000, 17000, 18000, 19000, 20000, 21000, 22000,
    23000, 24000, 25000, 26000, 27000, 28000, 29000, 30000
]

# ===== ENDPOINTS IPTV =====
IPTV_ENDPOINTS = [
    '/player_api.php', '/get.php', '/panel_api.php', '/api.php',
    '/xmltv.php', '/live', '/movie', '/series',
    '/streaming/clients_live.php', '/portal.php', '/enigma2.php',
    '/playlist.m3u', '/tv.m3u', '/live.m3u8', '/index.php',
    '/admin.php', '/login.php', '/user.php', '/users.php',
    '/clients.php', '/client.php', '/api/live.php', '/api/movie.php',
    '/api/series.php', '/panel/', '/admin/', '/manager/', '/control/',
    '/server/', '/iptv/', '/stream/', '/hls/', '/dash/', '/vod/',
    '/movies/', '/series/', '/channels/', '/live/', '/livestream/',
    '/livetv/', '/tv/', '/radio/'
]

# ===== CREDENCIALES COMUNES =====
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

# ===== FUNCIONES DE UTILIDAD =====
def get_service_name(port):
    services = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 80: 'HTTP',
        110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 993: 'IMAPS',
        995: 'POP3S', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
        5900: 'VNC', 6379: 'Redis', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt',
        25461: 'IPTV', 25462: 'IPTV', 25463: 'IPTV', 25464: 'IPTV', 25465: 'IPTV',
        27017: 'MongoDB'
    }
    return services.get(port, f'Port-{port}')

def grab_banner(host, port):
    """Obtiene banner del servicio"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect((host, port))
        
        if port in [21, 25, 110, 143, 443, 993, 995, 22]:
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
        elif port in [80, 443, 8080, 8443, 25461, 25462, 25463]:
            sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
        else:
            banner = ""
        sock.close()
        return banner[:200]
    except:
        return ""

# ===== EXPLOITS REALES =====
def check_ftp_vulnerabilities(host, port=21):
    """Comprueba FTP anónimo y credenciales comunes"""
    results = {'anonymous': False, 'creds': []}
    
    # FTP anónimo
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=5)
        ftp.login()
        results['anonymous'] = True
        try:
            files = ftp.nlst()
            results['files'] = files[:10]
        except:
            pass
        ftp.quit()
    except:
        pass
    
    # Credenciales comunes
    for user, pwd in COMMON_CREDS[:10]:
        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=3)
            ftp.login(user, pwd)
            results['creds'].append({'username': user, 'password': pwd})
            ftp.quit()
            break
        except:
            continue
    
    return results

def check_http_vulnerabilities(host, port, ssl=False):
    """Busca paneles admin, archivos sensibles y M3U"""
    protocol = 'https' if ssl else 'http'
    base_url = f"{protocol}://{host}:{port}"
    results = {'admin_panels': [], 'm3u_files': [], 'sensitive_files': [], 'creds': []}
    
    paths = {
        'admin': ['/admin', '/panel', '/cpanel', '/login', '/wp-admin', '/manager'],
        'm3u': ['/playlist.m3u', '/tv.m3u', '/live.m3u', '/get.php', '/player_api.php'],
        'sensitive': ['/phpinfo.php', '/.env', '/config.php', '/backup.sql', '/info.php']
    }
    
    for category, path_list in paths.items():
        for path in path_list:
            try:
                url = base_url + path
                r = requests.get(url, timeout=2, verify=False)
                if r.status_code == 200:
                    if category == 'admin':
                        results['admin_panels'].append(url)
                    elif category == 'm3u' and ('#EXTM3U' in r.text or '.m3u' in url):
                        results['m3u_files'].append(url)
                    elif category == 'sensitive':
                        results['sensitive_files'].append(url)
            except:
                continue
    
    return results

def check_iptv_vulnerabilities(host, port):
    """Prueba credenciales IPTV"""
    protocol = 'https' if port in [443, 8443, 25462, 25464] else 'http'
    base_url = f"{protocol}://{host}:{port}"
    results = {'creds': [], 'm3u_urls': []}
    
    for endpoint in IPTV_ENDPOINTS[:10]:
        for user, pwd in COMMON_CREDS[:10]:
            try:
                if 'player_api' in endpoint or 'api.php' in endpoint:
                    url = f"{base_url}{endpoint}?username={user}&password={pwd}"
                elif 'get.php' in endpoint:
                    url = f"{base_url}{endpoint}?username={user}&password={pwd}&type=m3u_plus"
                else:
                    continue
                
                r = requests.get(url, timeout=2, verify=False)
                if r.status_code == 200:
                    if 'player_api' in endpoint:
                        try:
                            data = r.json()
                            if data.get('user_info', {}).get('auth') == 1:
                                results['creds'].append({'username': user, 'password': pwd})
                        except:
                            pass
                    elif '#EXTM3U' in r.text:
                        results['m3u_urls'].append(url)
                        results['creds'].append({'username': user, 'password': pwd})
            except:
                continue
    
    return results

# ===== ESCANEO PRINCIPAL =====
def scan_port(host, port):
    """Escanea un puerto y detecta vulnerabilidades"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            service = get_service_name(port)
            banner = grab_banner(host, port)
            vulnerabilities = []
            
            # Detectar vulnerabilidades según el puerto
            if port == 21:
                ftp_res = check_ftp_vulnerabilities(host, port)
                if ftp_res.get('anonymous'):
                    vulnerabilities.append({'type': 'ftp_anonymous', 'risk': 'high'})
                if ftp_res.get('creds'):
                    vulnerabilities.append({'type': 'ftp_weak_creds', 'creds': ftp_res['creds'], 'risk': 'critical'})
            
            elif port in [80, 443, 8080, 8443, 25461, 25462, 25463]:
                http_res = check_http_vulnerabilities(host, port, ssl=(port in [443,8443,25462]))
                if http_res.get('admin_panels'):
                    vulnerabilities.append({'type': 'admin_panel', 'urls': http_res['admin_panels'], 'risk': 'medium'})
                if http_res.get('m3u_files'):
                    vulnerabilities.append({'type': 'm3u_exposed', 'urls': http_res['m3u_files'], 'risk': 'high'})
                if http_res.get('sensitive_files'):
                    vulnerabilities.append({'type': 'sensitive_exposed', 'urls': http_res['sensitive_files'], 'risk': 'critical'})
                
                iptv_res = check_iptv_vulnerabilities(host, port)
                if iptv_res.get('creds'):
                    vulnerabilities.append({'type': 'iptv_creds', 'creds': iptv_res['creds'], 'risk': 'critical'})
                if iptv_res.get('m3u_urls'):
                    vulnerabilities.append({'type': 'iptv_m3u', 'urls': iptv_res['m3u_urls'], 'risk': 'high'})
            
            sock.close()
            
            return {
                'port': port,
                'open': True,
                'service': service,
                'banner': banner,
                'vulnerabilities': vulnerabilities,
                'vulnerable': len(vulnerabilities) > 0
            }
        sock.close()
        return {'port': port, 'open': False}
    except Exception as e:
        return {'port': port, 'open': False, 'error': str(e)}

# ===== RUTAS API =====
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'version': '5.0',
        'ports_count': len(IPTV_PORTS),
        'message': '🔥 CHERRY BACKEND FUNCIONANDO'
    })

@app.route('/api/scan', methods=['POST'])
def scan():
    data = request.json
    host = data.get('host', '').strip()
    ports_str = data.get('ports', '').strip()
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    # Parsear puertos
    port_list = []
    if ports_str:
        for p in ports_str.split(','):
            try:
                port_list.append(int(p.strip()))
            except:
                pass
    else:
        port_list = IPTV_PORTS[:100]
    
    # Escanear en paralelo
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(scan_port, host, p): p for p in port_list}
        for future in futures:
            try:
                results.append(future.result(timeout=5))
            except:
                results.append({'port': futures[future], 'open': False})
    
    open_ports = [r for r in results if r.get('open')]
    vulnerable = [r for r in results if r.get('vulnerable')]
    
    return jsonify({
        'host': host,
        'results': results,
        'open_ports': open_ports,
        'vulnerable_ports': vulnerable,
        'open': len(open_ports),
        'vulnerable': len(vulnerable),
        'total': len(results)
    })

@app.route('/api/deep-analyze', methods=['POST'])
def deep_analyze():
    data = request.json
    host = data.get('host')
    port = data.get('port')
    
    if not host or not port:
        return jsonify({'error': 'Host y puerto requeridos'}), 400
    
    # Análisis específico del puerto
    result = scan_port(host, port)
    
    return jsonify({
        'success': True,
        'results': result
    })

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🍒 CHERRY BACKEND DEFINITIVO v5.0")
    print("="*70)
    print(f"📋 Puertos configurados: {len(IPTV_PORTS)}")
    print(f"🔑 Credenciales: {len(COMMON_CREDS)}")
    print(f"🎯 Endpoints IPTV: {len(IPTV_ENDPOINTS)}")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
