from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import re
import json
import os
import time
from urllib.parse import unquote
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TikTokDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        })
        self.downloads_folder = "downloads"
        os.makedirs(self.downloads_folder, exist_ok=True)
    
    def get_video_info(self, url):
        try:
            logger.info(f"🎯 Récupération des informations pour: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            patterns = [
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
                r'window\.__INITIAL_STATE__=(.*?);</script>',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response.text)
                if match:
                    data = json.loads(match.group(1))
                    video_data = self._extract_video_data(data)
                    if video_data:
                        logger.info("🎯 Informations vidéo récupérées avec succès")
                        return video_data
            
            logger.error("❌ Aucune donnée vidéo trouvée dans la page")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération: {e}")
            return None
    
    def _extract_video_data(self, data):
        try:
            paths_to_try = [
                ['__DEFAULT_SCOPE__', 'webapp.video-detail', 'itemInfo', 'itemStruct'],
                ['__DEFAULT_SCOPE__', 'webapp.video-detail', 'itemInfo', 'itemStruct', 'video'],
                ['ItemModule'],
                ['props', 'pageProps'],
            ]
            
            for path in paths_to_try:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    if current and isinstance(current, dict):
                        # Recherche du lien @hd
                        video_url = self._find_video_url(current)
                        if video_url:
                            return {
                                'video_url': video_url,
                                'title': current.get('desc', ''),
                                'author': current.get('author', {}).get('uniqueId', ''),
                                'duration': current.get('video', {}).get('duration', 0)
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction données: {e}")
            return None
    
    def _find_video_url(self, data):
        try:
            if isinstance(data, dict):
                play_addr = data.get('video', {}).get('playAddr')
                if play_addr:
                    return play_addr.replace('playwm', 'play')
                
                download_addr = data.get('video', {}).get('downloadAddr')
                if download_addr:
                    return download_addr
                
                play_url = data.get('video', {}).get('playUrl')
                if play_url:
                    return play_url
                
                for key, value in data.items():
                    if isinstance(value, dict):
                        result = self._find_video_url(value)
                        if result:
                            return result
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche URL: {e}")
            return None
    
    def download_video(self, video_url, filename=None):
        try:
            if not filename:
                filename = f"tiktok_video_{int(time.time())}.mp4"
            
            filepath = os.path.join(self.downloads_folder, filename)
            
            logger.info(f"🎯 Début du téléchargement: {filename}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/',
                'Range': 'bytes=0-',
            }
            
            start_time = time.time()
            response = self.session.get(video_url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            download_time = time.time() - start_time
            file_size = os.path.getsize(filepath)
            
            logger.info(f"✅ Téléchargement réussi: {filename}")
            logger.info(f"🎯 Taille: {file_size / (1024*1024):.2f} MB")
            logger.info(f"🎯 Temps: {download_time:.2f} secondes")
            
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur téléchargement: {e}")
            return None

    def clean_caption(self, caption):
        if not caption:
            return ""
        
        caption = re.sub(r'@\w+', '', caption)
        
        caption = re.sub(r'\s+', ' ', caption)
        
        caption = caption.strip()
        
        return caption

downloader = TikTokDownloader()

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'online', 'message': 'Serveur TikTok Downloader actif'})

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        tiktok_url = data.get('url')
        
        if not tiktok_url:
            return jsonify({'success': False, 'error': 'URL manquante'})
        
        logger.info(f"🎯 Nouvelle demande de téléchargement: {tiktok_url}")
        
        video_info = downloader.get_video_info(tiktok_url)
        
        if not video_info:
            return jsonify({'success': False, 'error': 'Impossible de récupérer les informations de la vidéo'})
        
        original_caption = video_info.get('title', '')
        cleaned_caption = downloader.clean_caption(original_caption)
        
        logger.info(f"🎯 Caption récupéré: {cleaned_caption}")
        
        safe_author = "".join(c for c in video_info['author'] if c.isalnum())
        filename = f"tiktok_{safe_author}_{int(time.time())}.mp4"
        
        filepath = downloader.download_video(video_info['video_url'], filename)
        
        if filepath:
            return jsonify({
                'success': True,
                'message': 'Vidéo téléchargée avec succès',
                'filename': filename,
                'title': video_info['title'],
                'cleaned_caption': cleaned_caption,
                'author': video_info['author'],
                'filepath': filepath
            })
        else:
            return jsonify({'success': False, 'error': 'Échec du téléchargement de la vidéo'})
            
    except Exception as e:
        logger.error(f"❌ Erreur endpoint /download: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/downloads/<filename>', methods=['GET'])
def get_downloaded_file(filename):
    try:
        filepath = os.path.join(downloader.downloads_folder, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'Fichier non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🎯 Démarrage du serveur TikTok Downloader...")
    print("🎯 Dossier de téléchargement:", downloader.downloads_folder)
    print("🎯 Serveur accessible sur: http://localhost:5000")
    print("⚡ Version optimisée et rapide")
    app.run(host='0.0.0.0', port=5000, debug=False)  