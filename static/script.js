document.addEventListener("DOMContentLoaded", () => {

    const platformButtons = document.querySelectorAll(".platform");
    const typeButtons = document.querySelectorAll(".type-btn");

    const urlInput = document.getElementById("urlInput");
    const downloadBtn = document.getElementById("downloadBtn");

    const videoQuality = document.getElementById("videoQuality");
    const audioQuality = document.getElementById("audioQuality");

    const videoQualitySelect =
        document.getElementById("videoQualitySelect");

    const audioQualitySelect =
        document.getElementById("audioQualitySelect");

    const status = document.getElementById("status");


    /* =========================
       CURRENT SETTINGS
    ========================= */

    let currentPlatform = "instagram";
    let currentType = "video";


    /* =========================
       STATUS MESSAGE
    ========================= */

    function showStatus(message, type = "error") {

        if (!status) {
            return;
        }

        status.textContent = message;

        status.className = "status show " + type;
    }


    function hideStatus() {

        if (!status) {
            return;
        }

        status.textContent = "";

        status.className = "status";
    }


    /* =========================
       URL PLACEHOLDER
    ========================= */

    function updatePlaceholder() {

        if (!urlInput) {
            return;
        }

        if (currentPlatform === "instagram") {

            urlInput.placeholder =
                "Paste your Instagram URL here...";

        } else if (currentPlatform === "facebook") {

            urlInput.placeholder =
                "Paste your Facebook URL here...";

        } else {

            urlInput.placeholder =
                "Paste your media URL here...";
        }
    }


    /* =========================
       PLATFORM BUTTONS
    ========================= */

    platformButtons.forEach((button) => {

        const platform =
            button.dataset.platform;

        /* Hide YouTube completely */

        if (platform === "youtube") {

            button.style.display = "none";

            return;
        }


        button.addEventListener("click", () => {

            currentPlatform = platform;


            /* Active button */

            platformButtons.forEach((item) => {

                item.classList.remove("active");

            });

            button.classList.add("active");


            /* Update placeholder */

            updatePlaceholder();


            /* Clear old status */

            hideStatus();


            /* Clear URL */

            if (urlInput) {

                urlInput.value = "";

                urlInput.focus();

            }

        });

    });


    /* =========================
       VIDEO / AUDIO BUTTONS
    ========================= */

    typeButtons.forEach((button) => {

        button.addEventListener("click", () => {

            currentType =
                button.dataset.type;


            /* Active button */

            typeButtons.forEach((item) => {

                item.classList.remove("active");

            });

            button.classList.add("active");


            /* Show video quality */

            if (currentType === "video") {

                if (videoQuality) {

                    videoQuality.style.display =
                        "flex";

                }

                if (audioQuality) {

                    audioQuality.style.display =
                        "none";

                }

            }


            /* Show audio quality */

            else {

                if (videoQuality) {

                    videoQuality.style.display =
                        "none";

                }

                if (audioQuality) {

                    audioQuality.style.display =
                        "flex";

                }

            }


            hideStatus();

        });

    });


    /* =========================
       URL VALIDATION
    ========================= */

    function isValidUrl(url) {

        try {

            new URL(url);

            return true;

        } catch {

            return false;

        }

    }


    function validatePlatformUrl(url) {

        const lowerUrl =
            url.toLowerCase();


        if (currentPlatform === "instagram") {

            return lowerUrl.includes(
                "instagram.com"
            );

        }


        if (currentPlatform === "facebook") {

            return (
                lowerUrl.includes("facebook.com") ||
                lowerUrl.includes("fb.watch")
            );

        }


        return false;

    }


    /* =========================
       DOWNLOAD
    ========================= */

    if (downloadBtn) {

        downloadBtn.addEventListener("click", async () => {

            hideStatus();


            const url =
                urlInput.value.trim();


            /* Empty URL */

            if (!url) {

                showStatus(
                    "Please paste an Instagram or Facebook URL."
                );

                return;

            }


            /* URL format */

            if (!isValidUrl(url)) {

                showStatus(
                    "Please enter a valid URL."
                );

                return;

            }


            /* Platform check */

            if (!validatePlatformUrl(url)) {

                if (currentPlatform === "instagram") {

                    showStatus(
                        "Please enter a valid Instagram URL."
                    );

                } else {

                    showStatus(
                        "Please enter a valid Facebook URL."
                    );

                }

                return;

            }


            /* =========================
               GET QUALITY
            ========================= */

            let quality = "best";


            if (currentType === "video") {

                quality =
                    videoQualitySelect
                        ? videoQualitySelect.value
                        : "best";

            } else {

                quality =
                    audioQualitySelect
                        ? audioQualitySelect.value
                        : "best";

            }


            /* =========================
               BUTTON LOADING
            ========================= */

            const originalText =
                downloadBtn.textContent;


            downloadBtn.disabled = true;

            downloadBtn.textContent =
                "Processing...";


            try {

                console.log(
                    "Starting download..."
                );

                console.log(
                    "Platform:",
                    currentPlatform
                );

                console.log(
                    "Type:",
                    currentType
                );

                console.log(
                    "Quality:",
                    quality
                );


                /* =========================
                   SEND REQUEST
                ========================= */

                const response =
                    await fetch("/download", {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            url: url,

                            type: currentType,

                            quality: quality

                        })

                    });


                /* =========================
                   CHECK RESPONSE
                ========================= */

                const contentType =
                    response.headers.get(
                        "content-type"
                    ) || "";


                /* Server returned JSON error */

                if (
                    contentType.includes(
                        "application/json"
                    )
                ) {

                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.message ||
                            "Download failed."
                        );

                    }


                    if (
                        data.success === false
                    ) {

                        throw new Error(
                            data.message ||
                            "Download failed."
                        );

                    }

                }


                /* Server error */

                if (!response.ok) {

                    throw new Error(
                        "Server error " +
                        response.status
                    );

                }


                /* =========================
                   GET FILE
                ========================= */

                const blob =
                    await response.blob();


                if (!blob || blob.size === 0) {

                    throw new Error(
                        "Downloaded file is empty."
                    );

                }


                /* =========================
                   FILE NAME
                ========================= */

                let filename =
                    "AMDownloader-Video.mp4";


                if (currentType === "audio") {

                    if (quality === "mp3") {

                        filename =
                            "AMDownloader-Audio.mp3";

                    } else {

                        filename =
                            "AMDownloader-Audio.m4a";

                    }

                }


                /* =========================
                   DOWNLOAD FILE
                ========================= */

                const blobUrl =
                    window.URL.createObjectURL(
                        blob
                    );


                const link =
                    document.createElement("a");


                link.href = blobUrl;

                link.download = filename;

                document.body.appendChild(link);

                link.click();

                link.remove();


                window.URL.revokeObjectURL(
                    blobUrl
                );


                /* =========================
                   SUCCESS
                ========================= */

                showStatus(
                    "Download completed successfully.",
                    "success"
                );


            } catch (error) {

                console.error(
                    "Download error:",
                    error
                );


                showStatus(
                    error.message ||
                    "Unable to download this media. Please try again."
                );


            } finally {

                downloadBtn.disabled =
                    false;

                downloadBtn.textContent =
                    originalText;

            }

        });

    }


    /* =========================
       INITIAL SETTINGS
    ========================= */

    currentPlatform = "instagram";

    currentType = "video";


    /* Make Instagram active */

    platformButtons.forEach((button) => {

        if (
            button.dataset.platform ===
            "instagram"
        ) {

            button.classList.add("active");

        }

        if (
            button.dataset.platform ===
            "youtube"
        ) {

            button.style.display = "none";

            button.classList.remove(
                "active"
            );

        }

    });


    /* Make Video active */

    typeButtons.forEach((button) => {

        if (
            button.dataset.type ===
            "video"
        ) {

            button.classList.add("active");

        }

    });


    /* Show video quality */

    if (videoQuality) {

        videoQuality.style.display =
            "flex";

    }


    if (audioQuality) {

        audioQuality.style.display =
            "none";

    }


    /* Set correct placeholder */

    updatePlaceholder();

});