import os
import requests
import json
import asyncio
import edge_tts
import urllib.parse
from datetime import datetime

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def buat_naskah_dan_prompt():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt_utama = """
    Buat 1 naskah cerita pendek misteri atau fantasi gelap untuk YouTube Shorts (durasi 30 detik).
    Format respon harus JSON murni tanpa markdown: {"naskah": "...", "prompt_gambar": "dark fantasy vector art, highly detailed, polaroid aesthetic,..."}
    """
    data = {"contents": [{"parts": [{"text": prompt_utama}]}]}
    response = requests.post(url, headers=headers, json=data)
    
    # --- SISTEM PELAPORAN ERROR BARU ---
    data_json = response.json()
    if 'candidates' not in data_json:
        print("\n[PESAN PENOLAKAN DARI GOOGLE]:")
        print(data_json)
        raise ValueError("Gagal mendapatkan naskah! Kemungkinan API Key salah atau tidak terbaca.")
    # -----------------------------------
        
    hasil = data_json['candidates'][0]['content']['parts'][0]['text']
    return json.loads(hasil.replace('```json', '').replace('```', '').strip())

async def buat_suara(teks, nama_file):
    communicate = edge_tts.Communicate(teks, "id-ID-ArdiNeural")
    await communicate.save(nama_file)

def buat_gambar(prompt, nama_file):
    teks_url = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{teks_url}?width=1080&height=1920&nologo=true"
    response = requests.get(url)
    with open(nama_file, 'wb') as f:
        f.write(response.content)

def edit_video(audio_file, image_file, output_file):
    cmd = f"ffmpeg -loop 1 -i {image_file} -i {audio_file} -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest -y {output_file}"
    os.system(cmd)

def kirim_ke_telegram(file_video):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    with open(file_video, 'rb') as video:
        requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID}, files={'video': video})

async def eksekusi_utama():
    ide = buat_naskah_dan_prompt()
    waktu = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_audio, file_gambar, file_video = f"a_{waktu}.mp3", f"g_{waktu}.jpg", f"v_{waktu}.mp4"
    
    await buat_suara(ide["naskah"], file_audio)
    buat_gambar(ide["prompt_gambar"], file_gambar)
    edit_video(file_audio, file_gambar, file_video)
    kirim_ke_telegram(file_video)

if __name__ == "__main__":
    asyncio.run(eksekusi_utama())
