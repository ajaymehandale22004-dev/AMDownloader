from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/check-url", methods=["POST"])
def check_url():
    data = request.get_json() or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "message": "Please enter a URL."
        })

    if "youtube.com" in url or "youtu.be" in url:
        platform = "YouTube"

    elif "instagram.com" in url:
        platform = "Instagram"

    elif "facebook.com" in url or "fb.watch" in url:
        platform = "Facebook"

    else:
        return jsonify({
            "success": False,
            "message": "Please enter a valid YouTube, Instagram or Facebook URL."
        })

    return jsonify({
        "success": True,
        "platform": platform,
        "url": url
    })


@app.route("/download", methods=["POST"])
def download():

    data = request.get_json() or {}

    url = data.get("url", "").strip()
    media_type = data.get("type", "video")
    quality = data.get("quality", "best")

    if not url:
        return jsonify({
            "success": False,
            "message": "Please enter a URL."
        }), 400

    supported_url = (
        "youtube.com" in url
        or "youtu.be" in url
        or "instagram.com" in url
        or "facebook.com" in url
        or "fb.watch" in url
    )

    if not supported_url:
        return jsonify({
            "success": False,
            "message": "Unsupported URL."
        }), 400


    file_id = str(uuid.uuid4())


    try:

        # AUDIO

        if media_type == "audio":

            if quality == "mp3":

                output_template = os.path.join(
                    DOWNLOAD_FOLDER,
                    file_id + ".mp3"
                )

                options = {
                    "format": "bestaudio/best",
                    "outtmpl": output_template,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192"
                        }
                    ]
                }

            else:

                output_template = os.path.join(
                    DOWNLOAD_FOLDER,
                    file_id + ".m4a"
                )

                options = {
                    "format": "bestaudio[ext=m4a]/bestaudio",
                    "outtmpl": output_template,
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True
                }


        # VIDEO

        else:

            output_template = os.path.join(
                DOWNLOAD_FOLDER,
                file_id + ".%(ext)s"
            )


            if quality == "1080":

                video_format = (
                    "bestvideo[height<=1080]+bestaudio/"
                    "best[height<=1080]"
                )

            elif quality == "720":

                video_format = (
                    "bestvideo[height<=720]+bestaudio/"
                    "best[height<=720]"
                )

            elif quality == "480":

                video_format = (
                    "bestvideo[height<=480]+bestaudio/"
                    "best[height<=480]"
                )

            elif quality == "360":

                video_format = (
                    "bestvideo[height<=360]+bestaudio/"
                    "best[height<=360]"
                )

            else:

                video_format = "bestvideo+bestaudio/best"


            options = {
                "format": video_format,
                "outtmpl": output_template,
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True
            }


        # DOWNLOAD

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            downloaded_file = ydl.prepare_filename(info)


        # Find actual downloaded file

        if not os.path.exists(downloaded_file):

            possible_files = [
                os.path.join(
                    DOWNLOAD_FOLDER,
                    filename
                )
                for filename in os.listdir(DOWNLOAD_FOLDER)
                if filename.startswith(file_id)
            ]

            if possible_files:
                downloaded_file = possible_files[0]


        if not os.path.exists(downloaded_file):

            return jsonify({
                "success": False,
                "message": "Downloaded file could not be found."
            }), 500


        # Download filename

        if media_type == "audio":

            if quality == "mp3":
                filename = "AMDownloader-Audio.mp3"
            else:
                filename = "AMDownloader-Audio.m4a"

        else:

            filename = "AMDownloader-Video.mp4"


        return send_file(
            downloaded_file,
            as_attachment=True,
            download_name=filename
        )


    except Exception as e:

        print("Download error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to download this media. The selected format may not be available."
        }), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
    