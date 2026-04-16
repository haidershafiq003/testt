from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os
import glob

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML = """ 
<!-- SAME HTML (no change needed) -->
"""  # (tum apna existing HTML yahan 그대로 rehne do)

def clean_old_files():
    files = glob.glob(f"{DOWNLOAD_FOLDER}/*")
    for f in files:
        try:
            os.remove(f)
        except:
            pass

@app.route("/", methods=["GET", "POST"])
def index():
    formats = None
    url = ""
    thumbnail = None
    error = None

    if request.method == "POST":
        url = request.form.get("url", "")
        action = request.form.get("action")

        # ---------- FETCH ----------
        if action == "fetch":
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)

                thumbnail = info.get("thumbnail")

                video_formats = []
                audio_formats = []

                for f in info["formats"]:
                    if f.get("vcodec") != "none" and f.get("height"):
                        video_formats.append({
                            "format_id": f["format_id"],
                            "resolution": f"{f.get('height')}p"
                        })

                    if f.get("acodec") != "none" and f.get("vcodec") == "none":
                        audio_formats.append({
                            "format_id": f["format_id"],
                            "abr": f.get("abr") or "audio"
                        })

                video_formats = sorted(
                    video_formats,
                    key=lambda x: int(x["resolution"].replace("p", "")),
                    reverse=True
                )

                formats = {"video": video_formats, "audio": audio_formats}

            except Exception:
                error = "❌ Invalid or unsupported link!"

        # ---------- DOWNLOAD VIDEO ----------
        elif action == "download_video":
            try:
                clean_old_files()

                fmt = request.form["format"]

                ydl_opts = {
                    'format': f'{fmt}+bestaudio/best',
                    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
                    'merge_output_format': 'mp4',
                    'noplaylist': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                file = max(
                    [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER)],
                    key=os.path.getctime
                )

                return send_file(file, as_attachment=True)

            except Exception:
                error = "❌ Video download failed!"

        # ---------- DOWNLOAD AUDIO ----------
        elif action == "download_audio":
            try:
                clean_old_files()

                fmt = request.form["format"]

                ydl_opts = {
                    'format': fmt,
                    'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
                    'noplaylist': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                file = max(
                    [os.path.join(DOWNLOAD_FOLDER, f) for f in os.listdir(DOWNLOAD_FOLDER)],
                    key=os.path.getctime
                )

                return send_file(file, as_attachment=True)

            except Exception:
                error = "❌ Audio download failed!"

    return render_template_string(
        HTML,
        formats=formats,
        url=url,
        thumbnail=thumbnail,
        error=error
    )


# IMPORTANT FOR DEPLOYMENT
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)