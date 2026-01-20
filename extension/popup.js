document.addEventListener('DOMContentLoaded', function() {
    checkServerStatus();
});

async function checkServerStatus() {
    try {
        const response = await fetch('http://localhost:5000/status');
        const data = await response.json();
        
        if (data.status === 'online') {
            showStatus('Serveur connecté ✓', 'success');
        } else {
            showStatus('Serveur hors ligne', 'error');
        }
    } catch (error) {
        showStatus('Serveur non disponible - Démarrez le serveur Flask', 'error');
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
}