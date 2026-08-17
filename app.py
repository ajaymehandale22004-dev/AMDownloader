from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# URL Checker
# -----------------------------

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


# -----------------------------
# Download
# -----------------------------

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


    # -------------------------
    # Platform Detection
    # -------------------------

    if "youtube.com" in url or "youtu.be" in url:
        platform = "youtube"

    elif "instagram.com" in url:
        platform = "instagram"

    elif "facebook.com" in url or "fb.watch" in url:
        platform = "facebook"

    else:
        return jsonify({
            "success": False,
            "message": "Unsupported URL."
        }), 400


    # -------------------------
    # Validate Type
    # -------------------------

    if media_type not in ["video", "audio"]:
        media_type = "video"


    file_id = str(uuid.uuid4())


    try:

        # ==================================================
        # AUDIO
        # ==================================================

        if media_type == "audio":

            # -------------------------
            # MP3
            # -------------------------

            if quality == "mp3":

                output_template = os.path.join(
                    DOWNLOAD_FOLDER,
                    file_id + ".%(ext)s"
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


            # -------------------------
            # M4A / Best Audio
            # -------------------------

            else:

                output_template = os.path.join(
                    DOWNLOAD_FOLDER,
                    file_id + ".%(ext)s"
                )

                options = {
                    "format": "bestaudio[ext=m4a]/bestaudio",

                    "outtmpl": output_template,

                    "noplaylist": True,

                    "quiet": True,

                    "no_warnings": True
                }


        # ==================================================
        # VIDEO
        # ==================================================

        else:

            output_template = os.path.join(
                DOWNLOAD_FOLDER,
                file_id + ".%(ext)s"
            )


            # -------------------------
            # Quality Selection
            # -------------------------

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

                video_format = (
                    "bestvideo+bestaudio/"
                    "best"
                )


            options = {
                "format": video_format,

                "outtmpl": output_template,

                "merge_output_format": "mp4",

                "noplaylist": True,

                "quiet": True,

                "no_warnings": True
            }


        # ==================================================
        # Download
        # ==================================================

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            downloaded_file = ydl.prepare_filename(info)


        # ==================================================
        # Find Downloaded File
        # ==================================================

        if not os.path.exists(downloaded_file):

            possible_files = []

            for filename in os.listdir(DOWNLOAD_FOLDER):

                if filename.startswith(file_id):

                    possible_files.append(
                        os.path.join(
                            DOWNLOAD_FOLDER,
                            filename
                        )
                    )


            if possible_files:

                downloaded_file = possible_files[0]


        # ==================================================
        # File Not Found
        # ==================================================

        if not os.path.exists(downloaded_file):

            return jsonify({
                "success": False,
                "message": "Downloaded file could not be found."
            }), 500


        # ==================================================
        # Output Filename
        # ==================================================

        if media_type == "audio":

            if quality == "mp3":

                filename = "AMDownloader-Audio.mp3"

            else:

                filename = "AMDownloader-Audio.m4a"


        else:

            filename = "AMDownloader-Video.mp4"


        # ==================================================
        # Send File
        # ==================================================

        return send_file(
            downloaded_file,
            as_attachment=True,
            download_name=filename
        )


    # ======================================================
    # Errors
    # ======================================================

    except Exception as e:

        error_text = str(e)

        print("=" * 60)
        print("DOWNLOAD ERROR")
        print(error_text)
        print("=" * 60)


        # -------------------------
        # YouTube Bot Error
        # -------------------------

        if (
            "Sign in to confirm" in error_text
            or "not a bot" in error_text
            or "confirm you're not a bot" in error_text
        ):

            message = (
                "YouTube is currently blocking this server request. "
                "Please try another public video later."
            )


        # -------------------------
        # Format Error
        # -------------------------

        elif (
            "Requested format is not available"
            in error_text
        ):

            message = (
                "The selected quality is not available "
                "for this media."
            )


        # -------------------------
        # Login / Private Content
        # -------------------------

        elif (
            "login required" in error_text.lower()
            or "private" in error_text.lower()
        ):

            message = (
                "This media is private or requires login."
            )


        # -------------------------
        # Generic Error
        # -------------------------

        else:

            message = (
                "Unable to download this media. "
                "Please check the URL and try again."
            )


        return jsonify({
            "success": False,
            "message": message
        }), 500


# -----------------------------
# Run Server
# -----------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )