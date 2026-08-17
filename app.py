from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import glob

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ------------------------------------------------
# ENVIRONMENT
# ------------------------------------------------

IS_RENDER = os.getenv("RENDER") == "true"

# Local bgutil server
# Render par 127.0.0.1:4416 use nahi karna
POT_SERVER = os.getenv(
    "POT_SERVER",
    "http://127.0.0.1:4416"
)


# ------------------------------------------------
# HOME
# ------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ------------------------------------------------
# CHECK URL
# ------------------------------------------------

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


# ------------------------------------------------
# DOWNLOAD
# ------------------------------------------------

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


    # ------------------------------------------------
    # SUPPORTED URL CHECK
    # ------------------------------------------------

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

        # ------------------------------------------------
        # COMMON OPTIONS
        # ------------------------------------------------

        output_template = os.path.join(
            DOWNLOAD_FOLDER,
            file_id + ".%(ext)s"
        )


        # ------------------------------------------------
        # AUDIO
        # ------------------------------------------------

        if media_type == "audio":

            if quality == "mp3":

                options = {

                    "format": "bestaudio/best",

                    "outtmpl": output_template,

                    "noplaylist": True,

                    "quiet": False,

                    "no_warnings": False,

                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192"
                        }
                    ]
                }

            else:

                options = {

                    "format": "bestaudio[ext=m4a]/bestaudio",

                    "outtmpl": output_template,

                    "noplaylist": True,

                    "quiet": False,

                    "no_warnings": False
                }


        # ------------------------------------------------
        # VIDEO
        # ------------------------------------------------

        else:

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

                "quiet": False,

                "no_warnings": False
            }


        # ------------------------------------------------
        # YOUTUBE CONFIGURATION
        # ------------------------------------------------

        is_youtube = (
            "youtube.com" in url
            or "youtu.be" in url
        )

        if is_youtube:

            print("")
            print("=" * 60)
            print("YOUTUBE CONFIGURATION")
            print("=" * 60)

            print(
                "MODE:",
                "RENDER" if IS_RENDER else "LOCAL"
            )

            print(
                "POT SERVER:",
                POT_SERVER
            )

            print("=" * 60)

            # Use mweb together with the bgutil HTTP POT provider
            # on both localhost and Render.
            options["extractor_args"] = {
                "youtube": {
                    "player_client": ["mweb"]
                },
                "youtubepot-bgutilhttp": {
                    "base_url": POT_SERVER,
                    "disable_innertube": "1"
                }
            }

            # Temporary verbose logging for Render debugging
            options["verbose"] = True

            options["socket_timeout"] = 30
            options["retries"] = 2
            options["fragment_retries"] = 2


        # LOG
        # ------------------------------------------------

        print("=" * 60)

        print("STARTING DOWNLOAD")

        print("URL:", url)

        print("TYPE:", media_type)

        print("QUALITY:", quality)

        print("RENDER:", IS_RENDER)

        print("=" * 60)


        # ------------------------------------------------
        # YT-DLP
        # ------------------------------------------------

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            downloaded_file = ydl.prepare_filename(info)


        # ------------------------------------------------
        # FIND ACTUAL FILE
        # ------------------------------------------------

        if not os.path.exists(downloaded_file):

            possible_files = glob.glob(
                os.path.join(
                    DOWNLOAD_FOLDER,
                    file_id + ".*"
                )
            )

            if possible_files:

                downloaded_file = possible_files[0]


        # ------------------------------------------------
        # FILE NOT FOUND
        # ------------------------------------------------

        if not os.path.exists(downloaded_file):

            return jsonify({

                "success": False,

                "message":
                    "Downloaded file could not be found."

            }), 500


        # ------------------------------------------------
        # FINAL FILE NAME
        # ------------------------------------------------

        if media_type == "audio":

            if quality == "mp3":

                filename = "AMDownloader-Audio.mp3"

            else:

                filename = "AMDownloader-Audio.m4a"

        else:

            filename = "AMDownloader-Video.mp4"


        print(
            "DOWNLOAD COMPLETED:",
            downloaded_file
        )


        # ------------------------------------------------
        # SEND FILE
        # ------------------------------------------------

        response = send_file(

            downloaded_file,

            as_attachment=True,

            download_name=filename
        )


        return response


    # ------------------------------------------------
    # ERRORS
    # ------------------------------------------------

    except yt_dlp.utils.DownloadError as e:

        error_text = str(e)

        print("=" * 60)

        print("YT-DLP DOWNLOAD ERROR")

        print(error_text)

        print("=" * 60)


        # YouTube bot verification

        if (
            "Sign in to confirm you're not a bot"
            in error_text
            or
            "Sign in to confirm you’re not a bot"
            in error_text
            or
            "not a bot" in error_text
        ):

            return jsonify({

                "success": False,

                "message":
                    "YouTube is currently blocking this server request. "
                    "Please try another public video later."

            }), 503


        # Video unavailable

        if (
            "Video unavailable"
            in error_text
        ):

            return jsonify({

                "success": False,

                "message":
                    "This video is unavailable or cannot be accessed."

            }), 404


        return jsonify({

            "success": False,

            "message":
                "The media could not be downloaded. "
                "Please try another public video."

        }), 500


    except Exception as e:

        print("=" * 60)

        print("GENERAL DOWNLOAD ERROR")

        print(str(e))

        print("=" * 60)


        return jsonify({

            "success": False,

            "message":
                "Unable to download this media. "
                "Please try again later."

        }), 500


# ------------------------------------------------
# RUN
# ------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False
    )