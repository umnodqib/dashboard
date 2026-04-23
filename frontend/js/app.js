// ✅ CHANGE FROM:
// const API_BASE = 'http://localhost:5000';

// ✅ TO:
const API_BASE = '/api';  // Relative path, works dengan Cloudflare
const AUTH_KEY = 'GHOST_SECRET_2026';

document.addEventListener('DOMContentLoaded', loadPanels);
setInterval(loadPanels, 5000);

async function loadPanels() {
    try {
        const response = await fetch(`${API_BASE}/status`, {
            headers: { 'X-Auth-Key': AUTH_KEY }
        });
        const data = await response.json();
        renderPanels(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

function renderPanels(data) {
    const grid = document.getElementById('panels-grid');
    grid.innerHTML = '';
    
    document.getElementById('stat-online').textContent = data.online;
    document.getElementById('stat-busy').textContent = data.busy;
    
    data.panels.forEach(panel => {
        const card = document.createElement('div');
        card.className = 'panel-card';
        card.innerHTML = `
            <div class="panel-slot">SLOT ${panel.slot}</div>
            <span class="status-badge ${panel.status.toLowerCase()}">${panel.status}</span>
            <div style="margin-top: 1rem; font-size: 0.85rem;">
                <div>IP: ${panel.ip}</div>
                <div>State: ${panel.state}</div>
                <div>Emails: ${panel.data.emails}</div>
                <div>Links: ${panel.data.links}</div>
            </div>
        `;
        grid.appendChild(card);
    });
}
