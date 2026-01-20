import requests
import re
import json
import os
from urllib.parse import unquote
import time

class TikTokDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
        })
    
    def get_video_info(self, url):
        """Récupère les informations de la vidéo TikTok"""
        try:
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
                        return video_data
            
            return None
            
        except Exception as e:
            print(f"Erreur lors de la récupération des informations: {e}")
            return None
    
    def _extract_video_data(self, data):
        """Extrait les données vidéo de la structure JSON"""
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
            print(f"Erreur lors de l'extraction des données: {e}")
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
            print(f"Erreur lors de la recherche de l'URL: {e}")
            return None
    
    def download_video(self, video_url, filename=None):
        try:
            if not filename:
                filename = f"tiktok_video_{int(time.time())}.mp4"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/',
                'Range': 'bytes=0-',
            }
            
            response = self.session.get(video_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"🎯 100%: {filename}")
            print(f"🎯 Taille: {os.path.getsize(filename) / (1024*1024):.2f} MB")
            
            return filename
            
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement: {e}")
            return None

def main():
    downloader = TikTokDownloader()
    
    print("🎯  TikDown")
    print("=" * 40)
    
    video_url = input("🎯Collez le lien de la vidéo TikTok à telecharger: ").strip()
    
    if not video_url.startswith('https://www.tiktok.com/'):
        print("❌ URL TikTok invalide")
        return
    
    print("🎯 Récupération des informations de la vidéo...")
    
    video_info = downloader.get_video_info(video_url)
    
    if not video_info:
        print("❌ Impossible de récupérer les informations de la vidéo")
        return
    
    print(f"🎯 Titre: {video_info['title']}")
    print(f"🎯 Auteur: @{video_info['author']}")
    print(f"🎯 Durée: {video_info['duration']} secondes")
    
    print("🎯 Téléchargement de la vidéo...")
    
    filename = f"tiktok_{video_info['author']}_{int(time.time())}.mp4"
    result = downloader.download_video(video_info['video_url'], filename)
    
    if result:
        print("✅ Téléchargement terminé avec succès!")
    else:
        print("❌ Échec du téléchargement")

if __name__ == "__main__":
    main()