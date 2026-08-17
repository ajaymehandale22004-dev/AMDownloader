from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import uuid
import glob


app = Flask(__name__)


# ============================================================
# DOWNLOAD FOLDER
# ============================================================

DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ============================================================
# ENVIRONMENT
# ============================================================

IS_RENDER = os.getenv("RENDER", "").lower() == "true"


# ============================================================
# BGUTIL POT SERVER
# ============================================================

# Local:
# http://127.0.0.1:4416
#
# Render:
# https://amdownloader-pot.onrender.com

POT_SERVER = os.getenv(
    "POT_SERVER",
    "http://127.0.0.1:4416"
).strip()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "success": True,
        "status": "online",
        "render": IS_RENDER,
        "pot_server": POT_SERVER
    })


# ============================================================
# CHECK URL
# ============================================================

@app.route("/check-url", methods=["POST"])
def check_url():

    data = request.get_json(silent=True) or {}

    url = data.get("url", "").strip()


    if not url:

        return jsonify({
            "success": False,
            "message": "Please enter a URL."
        }), 400


    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if (
        "youtube.com" in url.lower()
        or "youtu.be" in url.lower()
    ):

        platform = "YouTube"


    # --------------------------------------------------------
    # Instagram
    # --------------------------------------------------------

    elif "instagram.com" in url.lower():

        platform = "Instagram"


    # --------------------------------------------------------
    # Facebook
    # --------------------------------------------------------

    elif (
        "facebook.com" in url.lower()
        or "fb.watch" in url.lower()
    ):

        platform = "Facebook"


    else:

        return jsonify({
            "success": False,
            "message": (
                "Please enter a valid YouTube, "
                "Instagram or Facebook URL."
            )
        }), 400


    return jsonify({
        "success": True,
        "platform": platform,
        "url": url
    })


# ============================================================
# DOWNLOAD
# ============================================================

@app.route("/download", methods=["POST"])
def download():

    data = request.get_json(silent=True) or {}


    url = data.get("url", "").strip()

    media_type = data.get(
        "type",
        "video"
    )

    quality = data.get(
        "quality",
        "best"
    )


    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not url:

        return jsonify({
            "success": False,
            "message": "Please enter a URL."
        }), 400


    supported_url = (

        "youtube.com" in url.lower()
        or "youtu.be" in url.lower()

        or "instagram.com" in url.lower()

        or "facebook.com" in url.lower()
        or "fb.watch" in url.lower()

    )


    if not supported_url:

        return jsonify({
            "success": False,
            "message": "Unsupported URL."
        }), 400


    # ========================================================
    # FILE ID
    # ========================================================

    file_id = str(uuid.uuid4())


    try:

        # ====================================================
        # OUTPUT TEMPLATE
        # ====================================================

        output_template = os.path.join(
            DOWNLOAD_FOLDER,
            file_id + ".%(ext)s"
        )


        # ====================================================
        # AUDIO DOWNLOAD
        # ====================================================

        if media_type == "audio":

            # ------------------------------------------------
            # MP3
            # ------------------------------------------------

            if quality == "mp3":

                options = {

                    "format":
                        "bestaudio/best",

                    "outtmpl":
                        output_template,

                    "noplaylist":
                        True,

                    "quiet":
                        False,

                    "no_warnings":
                        False,

                    "postprocessors": [

                        {
                            "key":
                                "FFmpegExtractAudio",

                            "preferredcodec":
                                "mp3",

                            "preferredquality":
                                "192"
                        }

                    ]
                }


            # ------------------------------------------------
            # M4A
            # ------------------------------------------------

            else:

                options = {

                    "format":
                        "bestaudio[ext=m4a]/bestaudio",

                    "outtmpl":
                        output_template,

                    "noplaylist":
                        True,

                    "quiet":
                        False,

                    "no_warnings":
                        False
                }


        # ====================================================
        # VIDEO DOWNLOAD
        # ====================================================

        else:

            # ------------------------------------------------
            # 1080p
            # ------------------------------------------------

            if quality == "1080":

                video_format = (
                    "bestvideo[height<=1080]+bestaudio/"
                    "best[height<=1080]"
                )


            # ------------------------------------------------
            # 720p
            # ------------------------------------------------

            elif quality == "720":

                video_format = (
                    "bestvideo[height<=720]+bestaudio/"
                    "best[height<=720]"
                )


            # ------------------------------------------------
            # 480p
            # ------------------------------------------------

            elif quality == "480":

                video_format = (
                    "bestvideo[height<=480]+bestaudio/"
                    "best[height<=480]"
                )


            # ------------------------------------------------
            # 360p
            # ------------------------------------------------

            elif quality == "360":

                video_format = (
                    "bestvideo[height<=360]+bestaudio/"
                    "best[height<=360]"
                )


            # ------------------------------------------------
            # BEST
            # ------------------------------------------------

            else:

                video_format = (
                    "bestvideo+bestaudio/"
                    "best"
                )


            options = {

                "format":
                    video_format,

                "outtmpl":
                    output_template,

                "merge_output_format":
                    "mp4",

                "noplaylist":
                    True,

                "quiet":
                    False,

                "no_warnings":
                    False
            }


        # ====================================================
        # YOUTUBE DETECTION
        # ====================================================

        is_youtube = (

            "youtube.com" in url.lower()
            or "youtu.be" in url.lower()

        )


        # ====================================================
        # YOUTUBE + BGUTIL POT
        # ====================================================

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


            # IMPORTANT:
            # BGUTIL is used in BOTH local and Render.
            #
            # Local:
            # http://127.0.0.1:4416
            #
            # Render:
            # https://amdownloader-pot.onrender.com

            options["extractor_args"] = {

                "youtube": {

                    "player_client": [
                        "mweb"
                    ]

                },

                "youtubepot-bgutilhttp": {

                    "base_url":
                        POT_SERVER

                }

            }


            # ------------------------------------------------
            # Additional HTTP settings
            # ------------------------------------------------

            options["socket_timeout"] = 30

            options["retries"] = 2

            options["fragment_retries"] = 2


        # ====================================================
        # LOGGING
        # ====================================================

        print("")
        print("=" * 60)
        print("STARTING DOWNLOAD")
        print("=" * 60)

        print(
            "URL:",
            url
        )

        print(
            "TYPE:",
            media_type
        )

        print(
            "QUALITY:",
            quality
        )

        print(
            "RENDER:",
            IS_RENDER
        )

        print(
            "POT SERVER:",
            POT_SERVER
        )

        print("=" * 60)


        # ====================================================
        # YT-DLP
        # ====================================================

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            downloaded_file = ydl.prepare_filename(
                info
            )


        # ====================================================
        # FIND ACTUAL FILE
        # ====================================================

        if not os.path.exists(downloaded_file):

            possible_files = glob.glob(
                os.path.join(
                    DOWNLOAD_FOLDER,
                    file_id + ".*"
                )
            )

            if possible_files:

                # Prefer mp4
                mp4_files = [
                    f
                    for f in possible_files
                    if f.lower().endswith(".mp4")
                ]


                if mp4_files:

                    downloaded_file = mp4_files[0]

                else:

                    downloaded_file = possible_files[0]


        # ====================================================
        # FILE NOT FOUND
        # ====================================================

        if not os.path.exists(downloaded_file):

            print("")
            print("=" * 60)
            print("FILE NOT FOUND")
            print("=" * 60)

            print(
                "Expected:",
                downloaded_file
            )

            print(
                "Available files:",
                glob.glob(
                    os.path.join(
                        DOWNLOAD_FOLDER,
                        file_id + ".*"
                    )
                )
            )

            print("=" * 60)


            return jsonify({

                "success":
                    False,

                "message":
                    "Downloaded file could not be found."

            }), 500


        # ====================================================
        # FINAL FILE NAME
        # ====================================================

        if media_type == "audio":

            if quality == "mp3":

                filename = (
                    "AMDownloader-Audio.mp3"
                )

            else:

                filename = (
                    "AMDownloader-Audio.m4a"
                )


        else:

            filename = (
                "AMDownloader-Video.mp4"
            )


        # ====================================================
        # SUCCESS LOG
        # ====================================================

        print("")
        print("=" * 60)
        print("DOWNLOAD COMPLETED")
        print("=" * 60)

        print(
            "FILE:",
            downloaded_file
        )

        print("=" * 60)


        # ====================================================
        # SEND FILE
        # ====================================================

        return send_file(

            downloaded_file,

            as_attachment=True,

            download_name=filename

        )


    # ========================================================
    # YT-DLP ERROR
    # ========================================================

    except yt_dlp.utils.DownloadError as e:

        error_text = str(e)


        print("")
        print("=" * 60)
        print("YT-DLP DOWNLOAD ERROR")
        print("=" * 60)

        print(error_text)

        print("=" * 60)


        # ----------------------------------------------------
        # BOT DETECTION
        # ----------------------------------------------------

        bot_error = (

            "Sign in to confirm you're not a bot"
            in error_text

            or

            "Sign in to confirm you’re not a bot"
            in error_text

            or

            "not a bot"
            in error_text.lower()

        )


        if bot_error:

            return jsonify({

                "success":
                    False,

                "message":
                    (
                        "YouTube is currently blocking "
                        "requests from this server. "
                        "Please try another public video later."
                    )

            }), 503


        # ----------------------------------------------------
        # VIDEO UNAVAILABLE
        # ----------------------------------------------------

        if "Video unavailable" in error_text:

            return jsonify({

                "success":
                    False,

                "message":
                    (
                        "This video is unavailable "
                        "or cannot be accessed."
                    )

            }), 404


        # ----------------------------------------------------
        # PRIVATE VIDEO
        # ----------------------------------------------------

        if (
            "Private video"
            in error_text
        ):

            return jsonify({

                "success":
                    False,

                "message":
                    "This video is private."

            }), 403


        # ----------------------------------------------------
        # AGE RESTRICTED
        # ----------------------------------------------------

        if (
            "age-restricted"
            in error_text.lower()
            or
            "age restricted"
            in error_text.lower()
        ):

            return jsonify({

                "success":
                    False,

                "message":
                    (
                        "This video is age restricted "
                        "and cannot be downloaded."
                    )

            }), 403


        # ----------------------------------------------------
        # GENERIC YT-DLP ERROR
        # ----------------------------------------------------

        return jsonify({

            "success":
                False,

            "message":
                (
                    "The media could not be downloaded. "
                    "Please try another public video."
                )

        }), 500


    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as e:

        print("")
        print("=" * 60)
        print("GENERAL DOWNLOAD ERROR")
        print("=" * 60)

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print("=" * 60)


        return jsonify({

            "success":
                False,

            "message":
                (
                    "Unable to download this media. "
                    "Please try again later."
                )

        }), 500


# ============================================================
# RUN SERVER
# ============================================================

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