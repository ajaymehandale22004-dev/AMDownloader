const platformButtons = document.querySelectorAll(".platform");
const typeButtons = document.querySelectorAll(".type-btn");

const urlInput = document.getElementById("urlInput");
const downloadBtn = document.getElementById("downloadBtn");
const statusBox = document.getElementById("status");

const videoQuality = document.getElementById("videoQuality");
const audioQuality = document.getElementById("audioQuality");

const videoQualitySelect =
    document.getElementById("videoQualitySelect");

const audioQualitySelect =
    document.getElementById("audioQualitySelect");

let selectedPlatform = "youtube";
let selectedType = "video";


/* Platform selection */

platformButtons.forEach((button) => {

    button.addEventListener("click", () => {

        platformButtons.forEach((btn) => {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        selectedPlatform = button.dataset.platform;

        const names = {
            youtube: "YouTube",
            instagram: "Instagram",
            facebook: "Facebook"
        };

        urlInput.placeholder =
            `Paste your ${names[selectedPlatform]} URL here...`;

        clearStatus();
    });

});


/* Video / Audio selection */

typeButtons.forEach((button) => {

    button.addEventListener("click", () => {

        typeButtons.forEach((btn) => {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        selectedType = button.dataset.type;

        if (selectedType === "video") {

            videoQuality.style.display = "flex";
            audioQuality.style.display = "none";

        } else {

            videoQuality.style.display = "none";
            audioQuality.style.display = "flex";

        }

        clearStatus();
    });

});


/* Download */

downloadBtn.addEventListener("click", async () => {

    const url = urlInput.value.trim();

    if (!url) {

        showStatus(
            "Please paste a video URL first.",
            "error"
        );

        return;
    }


    let quality = "best";

    if (selectedType === "video") {

        quality = videoQualitySelect.value;

    } else {

        quality = audioQualitySelect.value;

    }


    downloadBtn.disabled = true;
    downloadBtn.textContent = "Processing...";

    clearStatus();


    try {

        const response = await fetch("/download", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                url: url,

                platform: selectedPlatform,

                type: selectedType,

                quality: quality

            })

        });


        const contentType =
            response.headers.get("content-type");


        if (!response.ok) {

            let message =
                "Unable to download this media.";

            if (
                contentType &&
                contentType.includes("application/json")
            ) {

                const data = await response.json();

                if (data.message) {
                    message = data.message;
                }

            }

            showStatus(message, "error");

            return;
        }


        if (
            contentType &&
            contentType.includes("application/json")
        ) {

            const data = await response.json();

            showStatus(
                data.message || "Download failed.",
                "error"
            );

            return;
        }


        const blob = await response.blob();

        const downloadUrl =
            window.URL.createObjectURL(blob);

        const link =
            document.createElement("a");

        link.href = downloadUrl;

        if (selectedType === "audio") {

            link.download =
                `AMDownloader-audio.${quality === "mp3" ? "mp3" : "m4a"}`;

        } else {

            link.download =
                "AMDownloader-video.mp4";

        }

        document.body.appendChild(link);

        link.click();

        link.remove();

        window.URL.revokeObjectURL(downloadUrl);


        showStatus(
            "Download started successfully.",
            "success"
        );


    } catch (error) {

        console.error(error);

        showStatus(
            "Server connection failed. Please try again.",
            "error"
        );

    } finally {

        downloadBtn.disabled = false;
        downloadBtn.textContent = "Download";

    }

});


/* Status */

function showStatus(message, type) {

    statusBox.textContent = message;

    statusBox.className =
        `status show ${type}`;

}


function clearStatus() {

    statusBox.textContent = "";

    statusBox.className = "status";

}