(function() {
    'use strict';
    
    let observer;
    let isInitialized = false;

    function init() {
        if (isInitialized) return;
        isInitialized = true;
        
        console.log(' TikDown Extension initialisée');
        
        injectDownloadButtons();
        setupMutationObserver();
        setupNavigationListener();
    }

    function setupNavigationListener() {
        let currentURL = window.location.href;
        
        setInterval(() => {
            if (window.location.href !== currentURL) {
                currentURL = window.location.href;
                console.log('Navigation SPA détectée');
                setTimeout(injectDownloadButtons, 800);
            }
        }, 500);
    }

    function setupMutationObserver() {
        observer = new MutationObserver(function(mutations) {
            let shouldInject = false;
            
            for (let mutation of mutations) {
                if (mutation.type === 'childList') {
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType === 1 && isVideoNode(node)) {
                            shouldInject = true;
                            break;
                        }
                    }
                }
                if (shouldInject) break;
            }
            
            if (shouldInject) {
                setTimeout(injectDownloadButtons, 500);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    function isVideoNode(node) {
        const selectors = [
            '[data-e2e="recommend-list-item-container"]',
            '[data-e2e="browse-video"]'
        ];
        
        return selectors.some(selector => 
            node.matches?.(selector) || node.querySelector?.(selector)
        );
    }

    function injectDownloadButtons() {
        const videoSelectors = [
            '[data-e2e="recommend-list-item-container"]',
            '[data-e2e="browse-video"]'
        ];
        
        let injectedCount = 0;
        
        videoSelectors.forEach(selector => {
            const containers = document.querySelectorAll(selector);
            
            containers.forEach(container => {
                if (!container.querySelector('.tiktok-download-btn')) {
                    addDownloadButton(container);
                    injectedCount++;
                }
            });
        });
        
        if (injectedCount > 0) {
            console.log(`✅ ${injectedCount} boutons injectés`);
        }
    }

    function addDownloadButton(container) {
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'tiktok-download-btn';
        downloadBtn.innerHTML = '📥 Télécharger';
        downloadBtn.style.cssText = `
            background: linear-gradient(45deg, #000000ff, #1a0907ff);
            color: white;
            border: none;
            padding: 8px 14px;
            border-radius: 18px;
            font-size: 11px;
            font-weight: bold;
            cursor: pointer;
            margin: 8px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            position: relative;
            z-index: 999999;
            pointer-events: auto;
            display: block;
        `;

        downloadBtn.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.boxShadow = '0 4px 12px rgba(0,0,0,0.4)';
        });

        downloadBtn.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
            this.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
        });

        downloadBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            await handleDownloadClick(this);
        });

        downloadBtn.addEventListener('mousedown', function(e) {
            e.stopPropagation();
            e.stopImmediatePropagation();
        });

        const actionBar = container.querySelector('[data-e2e="browse-like"]')?.parentElement?.parentElement;
        if (actionBar) {
            actionBar.appendChild(downloadBtn);
        } else {
            container.appendChild(downloadBtn);
        }
    }

    async function copyToClipboard(text) {
        if (!text) return false;

        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            try {
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            } catch (fallbackErr) {
                return false;
            }
        }
    }

    async function handleDownloadClick(button) {
        const originalText = button.innerHTML;
        
        try {
            button.innerHTML = '⏳...';
            button.disabled = true;
            button.style.opacity = '0.7';

            const videoUrl = window.location.href;

            console.log(' Début du téléchargement...');
            
            const response = await fetch('http://localhost:5000/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: videoUrl
                })
            });

            const result = await response.json();
            
            if (result.success) {
                if (result.cleaned_caption) {
                    const copySuccess = await copyToClipboard(result.cleaned_caption);
                    if (copySuccess) {
                        showNotification('✅ Caption copié!', 1500);
                    }
                }
                
                button.innerHTML = '✅ Réussi!';
                button.style.background = 'linear-gradient(45deg, #00b09b, #96c93d)';
                showNotification('✅ Vidéo téléchargée!');
                
            } else {
                button.innerHTML = '❌ Erreur';
                button.style.background = 'linear-gradient(45deg, #ff416c, #ff4b2b)';
                showNotification('❌ ' + (result.error || 'Erreur'));
            }

        } catch (error) {
            console.error('❌ Erreur:', error);
            button.innerHTML = '❌ Erreur';
            button.style.background = 'linear-gradient(45deg, #ff416c, #ff4b2b)';
            showNotification('❌ Erreur de connexion');
        } finally {
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
                button.style.opacity = '1';
                button.style.background = 'linear-gradient(45deg, #000000ff, #680f0fff)';
            }, 2000);
        }
    }

    function showNotification(message, duration = 2000) {
        const existingNotifications = document.querySelectorAll('.tiktok-downloader-notification');
        existingNotifications.forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = 'tiktok-downloader-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 12px 18px;
            border-radius: 8px;
            z-index: 1000001;
            font-size: 13px;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            border: 1px solid #00F2EA;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            pointer-events: none;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();