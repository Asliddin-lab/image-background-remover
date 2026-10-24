// State
let originalFile = null;
let originalUrl = null;
let resultBlob = null;
let resultUrl = null;
let currentBgColor = "transparent";
let isDraggingSlider = false;

// DOM Elements
const uploadZone = document.getElementById("upload-zone");
const workspaceStage = document.getElementById("workspace-stage");
const fileInput = document.getElementById("file-input");
const btnBrowse = document.getElementById("btn-browse");
const btnUploadAnother = document.getElementById("btn-upload-another");

const imgOriginal = document.getElementById("img-original");
const imgResult = document.getElementById("img-result");
const originalWrapper = document.getElementById("original-wrapper");
const sliderHandle = document.getElementById("slider-handle");
const comparisonBox = document.getElementById("comparison-box");

const selectModel = document.getElementById("select-model");
const colorkeySettings = document.getElementById("colorkey-settings");
const keyColorPicker = document.getElementById("key-color-picker");
const keyColorText = document.getElementById("key-color-text");

const checkMatting = document.getElementById("check-matting");
const checkCrop = document.getElementById("check-crop");
const btnReprocess = document.getElementById("btn-reprocess");
const reprocessSpinner = document.getElementById("reprocess-spinner");
const reprocessText = document.getElementById("reprocess-text");
const btnDownload = document.getElementById("btn-download");

const loadingOverlay = document.getElementById("loading-overlay");
const loadingMessage = document.getElementById("loading-message");

const tabSlider = document.getElementById("tab-slider");
const tabResult = document.getElementById("tab-result");
const tabOriginal = document.getElementById("tab-original");

// File Upload Handlers
btnBrowse.addEventListener("click", () => fileInput.click());
uploadZone.addEventListener("click", (e) => {
  if (e.target !== btnBrowse) fileInput.click();
});

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleFileSelected(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files && e.target.files[0]) {
    handleFileSelected(e.target.files[0]);
  }
});

btnUploadAnother.addEventListener("click", () => {
  fileInput.value = "";
  uploadZone.style.display = "block";
  workspaceStage.style.display = "none";
  if (originalUrl) URL.revokeObjectURL(originalUrl);
  if (resultUrl) URL.revokeObjectURL(resultUrl);
  originalFile = null;
  originalUrl = null;
  resultBlob = null;
  resultUrl = null;
});

function handleFileSelected(file) {
  if (!file.type.startsWith("image/")) {
    alert("Please select a valid image file.");
    return;
  }
  originalFile = file;
  if (originalUrl) URL.revokeObjectURL(originalUrl);
  originalUrl = URL.createObjectURL(file);

  imgOriginal.src = originalUrl;
  uploadZone.style.display = "none";
  workspaceStage.style.display = "grid";

  setSliderPosition(50);
  switchTab("slider");
  processImage();
}

// Model Selection handler
selectModel.addEventListener("change", () => {
  if (selectModel.value === "colorkey") {
    colorkeySettings.style.display = "block";
  } else {
    colorkeySettings.style.display = "none";
  }
});

// Color Key sync
keyColorPicker.addEventListener("input", (e) => {
  keyColorText.value = e.target.value.toUpperCase();
});
keyColorText.addEventListener("input", (e) => {
  if (/^#[0-9A-F]{6}$/i.test(e.target.value)) {
    keyColorPicker.value = e.target.value;
  }
});

// Background Swatches
document.querySelectorAll(".color-swatch").forEach((swatch) => {
  swatch.addEventListener("click", () => {
    document.querySelectorAll(".color-swatch").forEach((s) => s.classList.remove("active"));
    swatch.classList.add("active");
    currentBgColor = swatch.getAttribute("data-color");
    applyBackgroundFill(currentBgColor);
  });
});

const customBgPicker = document.getElementById("custom-bg-color");
customBgPicker.addEventListener("input", (e) => {
  document.querySelectorAll(".color-swatch").forEach((s) => s.classList.remove("active"));
  currentBgColor = e.target.value;
  applyBackgroundFill(currentBgColor);
});

function applyBackgroundFill(color) {
  const resultWrapper = document.getElementById("result-wrapper");
  if (color === "transparent") {
    resultWrapper.style.backgroundColor = "transparent";
    resultWrapper.style.backgroundImage = "";
  } else {
    resultWrapper.style.backgroundColor = color;
    resultWrapper.style.backgroundImage = "none";
  }
}

// Processing
btnReprocess.addEventListener("click", () => {
  processImage();
});

async function processImage() {
  if (!originalFile) return;

  showLoading(true, "Removing background with " + selectModel.options[selectModel.selectedIndex].text + "...");
  btnReprocess.disabled = true;
  reprocessSpinner.style.display = "inline-block";
  reprocessText.textContent = "Processing...";

  const formData = new FormData();
  formData.append("image", originalFile);

  const modelChoice = selectModel.value;
  if (modelChoice === "colorkey") {
    formData.append("method", "colorkey");
    formData.append("key_color", keyColorText.value);
  } else {
    formData.append("method", "ai");
    formData.append("model", modelChoice);
    formData.append("alpha_matting", checkMatting.checked ? "true" : "false");
  }

  formData.append("crop", checkCrop.checked ? "true" : "false");
  if (currentBgColor !== "transparent") {
    formData.append("color", currentBgColor);
  }

  try {
    const response = await fetch("/api/remove", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.error || "Background removal failed");
    }

    resultBlob = await response.blob();
    if (resultUrl) URL.revokeObjectURL(resultUrl);
    resultUrl = URL.createObjectURL(resultBlob);

    imgResult.src = resultUrl;
    btnDownload.href = resultUrl;
    btnDownload.download = originalFile.name.replace(/\.[^/.]+$/, "") + "_nobg.png";

    // Synchronize widths after load
    imgResult.onload = () => {
      syncImageLayers();
    };
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    showLoading(false);
    btnReprocess.disabled = false;
    reprocessSpinner.style.display = "none";
    reprocessText.textContent = "Apply Changes";
  }
}

function showLoading(show, message = "Processing...") {
  loadingMessage.textContent = message;
  loadingOverlay.style.display = show ? "flex" : "none";
}

// Before / After Slider Logic
function setSliderPosition(percentage) {
  percentage = Math.max(0, Math.min(100, percentage));
  sliderHandle.style.left = percentage + "%";
  originalWrapper.style.width = percentage + "%";
}

function onSliderMove(e) {
  if (!isDraggingSlider) return;
  const rect = comparisonBox.getBoundingClientRect();
  const clientX = e.touches ? e.touches[0].clientX : e.clientX;
  const offset = clientX - rect.left;
  const pct = (offset / rect.width) * 100;
  setSliderPosition(pct);
}

sliderHandle.addEventListener("mousedown", () => (isDraggingSlider = true));
sliderHandle.addEventListener("touchstart", () => (isDraggingSlider = true));

window.addEventListener("mousemove", onSliderMove);
window.addEventListener("touchmove", onSliderMove);

window.addEventListener("mouseup", () => (isDraggingSlider = false));
window.addEventListener("touchend", () => (isDraggingSlider = false));

// Clicking inside comparison box also moves the slider
comparisonBox.addEventListener("click", (e) => {
  if (e.target === sliderHandle || sliderHandle.contains(e.target)) return;
  const rect = comparisonBox.getBoundingClientRect();
  const pct = ((e.clientX - rect.left) / rect.width) * 100;
  setSliderPosition(pct);
});

// View Tabs
tabSlider.addEventListener("click", () => switchTab("slider"));
tabResult.addEventListener("click", () => switchTab("result"));
tabOriginal.addEventListener("click", () => switchTab("original"));

function switchTab(mode) {
  [tabSlider, tabResult, tabOriginal].forEach((t) => t.classList.remove("active"));
  if (mode === "slider") {
    tabSlider.classList.add("active");
    sliderHandle.style.display = "block";
    setSliderPosition(50);
  } else if (mode === "result") {
    tabResult.classList.add("active");
    sliderHandle.style.display = "none";
    originalWrapper.style.width = "0%";
  } else if (mode === "original") {
    tabOriginal.classList.add("active");
    sliderHandle.style.display = "none";
    originalWrapper.style.width = "100%";
  }
}

function syncImageLayers() {
  // Ensure original image width matches container width for perfect split clipping
  const boxRect = comparisonBox.getBoundingClientRect();
  imgOriginal.style.width = boxRect.width + "px";
  imgOriginal.style.height = boxRect.height + "px";
}

window.addEventListener("resize", syncImageLayers);
