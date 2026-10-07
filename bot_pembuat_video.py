import os
import time
import json
import asyncio
import edge_tts
import urllib.parse
import requests
from datetime import datetime
from google import genai
from google.genai import errors

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def buat_naskah_dan_prompt():
    print("[AI] Menghubungi Google GenAI...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt_utama = """
    Buat 1 naskah cerita pendek misteri atau fantasi gelap untuk YouTube Shorts (durasi 30 detik).
    Format respon harus JSON murni tanpa markdown: {"naskah": "...", "prompt_gambar": "dark fantasy vector art, highly detailed, polaroid aesthetic,..."}
    """
    
    for percobaan in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt_utama
            )
            hasil = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(hasil)
        except Exception as e:
            print(f"[AI] Gagal menghubungi Google (Percobaan {percobaan+1}/3). Error: {e}")
            time.sleep(5)
            
    raise ValueError("Gagal mendapatkan naskah setelah 3 percobaan.")

async def buat_suara(teks, nama_file):
    print("[AI] Merekam Voiceover...")
    communicate = edge_tts.Communicate(teks, "id-ID-ArdiNeural")
    await communicate.save(nama_file)

def buat_gambar(prompt, nama_file):
    print("[AI] Menggambar Visual...")
    teks_url = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{teks_url}?width=1080&height=1920&nologo=true"
    
    # Menambahkan batas waktu maksimal (timeout) 30 detik agar tidak stuck selamanya
    try:
        response = requests.get(url, timeout=30)
        with open(nama_file, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f"[AI] Pembuat gambar error/lambat: {e}")
        # Jika gagal menggambar, kita buat gambar darurat berwarna hitam
        os.system(f"ffmpeg -f lavfi -i color=c=black:s=1080x1920 -frames:v 1 {nama_file}")
        print("[AI] Menggunakan gambar darurat (hitam).")

def edit_video(audio_file, image_file, output_file):
    print("[AI] Merakit Video...")
    cmd = f"ffmpeg -loop 1 -i {image_file} -i {audio_file} -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest -y {output_file}"
    os.system(cmd)

def kirim_ke_telegram(file_video):
    print("[AI] Mengirim ke Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    try:
        with open(file_video, 'rb') as video:
            response = requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID}, files={'video': video}, timeout=60)
            # Baris baru untuk mencetak alasan penolakan Telegram
            print(f"[Laporan Kurir Telegram]: {response.text}")
    except Exception as e:
        print(f"[AI] Sistem pengiriman error: {e}")

async def eksekusi_utama():
    try:
        ide = buat_naskah_dan_prompt()
        waktu = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_audio = f"a_{waktu}.mp3"
        file_gambar = f"g_{waktu}.jpg"
        file_video = f"v_{waktu}.mp4"
        
        await buat_suara(ide["naskah"], file_audio)
        buat_gambar(ide["prompt_gambar"], file_gambar)
        edit_video(file_audio, file_gambar, file_video)
        kirim_ke_telegram(file_video)
    except Exception as e:
        print(f"\n[FATAL ERROR] Sistem berhenti: {e}")

if __name__ == "__main__":
    asyncio.run(eksekusi_utama())
