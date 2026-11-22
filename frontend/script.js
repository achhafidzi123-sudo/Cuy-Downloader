// CUY DOWNLOADER - frontend logic
// Kabbhi tab ngangguy backend endpoint se padha (/api/info, /api/download)
// sabab yt-dlp otomatis mendeteksi platform dari URL se èkèrem.

const API_BASE = ""; // kosong = same-origin (backend & frontend dilajâni backend Flask se padha)

const pills = document.querySelectorAll(".pill");
const panels = document.querySelectorAll(".console-body");
const resultSection = document.getElementById("result");
const statusSection = document.getElementById("status");
const resThumbImg = document.getElementById("result-thumb-img");
const resThumbPlaceholder = document.getElementById("result-thumb-placeholder");
const resTitle = document.getElementById("result-title");
const resUploader = document.getElementById("result-uploader");
const resDuration = document.getElementById("result-duration");
const resolutionsWrap = document.getElementById("resolutions");
const toast = document.getElementById("toast");

// --- Gili' tab ---
pills.forEach((btn) => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;

    pills.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    panels.forEach((p) => p.classList.add("hidden"));
    document.getElementById(`panel-${tab}`).classList.remove("hidden");

    hideResult();
    hideStatus();
  });
});

// --- Tombhol Pareksa video ---
document.querySelectorAll(".check-btn").forEach((btn) => {
  btn.addEventListener("click", () => handleCheck(btn));
});

// Benne' tèkanan Enter e kolom input
document.querySelectorAll(".url-input").forEach((input) => {
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const platform = input.dataset.platform;
      const btn = document.querySelector(`.check-btn[data-platform="${platform}"]`);
      if (btn) handleCheck(btn);
    }
  });
});

async function handleCheck(btn) {
  const platform = btn.dataset.platform;
  const input = document.querySelector(`.url-input[data-platform="${platform}"]`);
  const url = input.value.trim();

  hideResult();

  if (!url) {
    showStatus("Sabe' link video gallu.", true);
    return;
  }

  setLoading(btn, true);
  showStatus("Gi' ngala' info video...", false);

  try {
    const res = await fetch(`${API_BASE}/api/info`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Gâghâl ngala' info video.");
    }

    renderResult(data, url);
    hideStatus();
  } catch (err) {
    showStatus(err.message || "Badha kasala'an.", true);
  } finally {
    setLoading(btn, false);
  }
}

function renderResult(data, originalUrl) {
  if (data.thumbnail) {
    resThumbImg.src = data.thumbnail;
    resThumbImg.classList.remove("hidden");
    resThumbPlaceholder.classList.add("hidden");
  } else {
    resThumbImg.classList.add("hidden");
    resThumbPlaceholder.classList.remove("hidden");
  }

  resTitle.textContent = data.title || "Video";
  resUploader.textContent = data.uploader || "-";
  resDuration.textContent = data.duration ? formatDuration(data.duration) : "-";

  resolutionsWrap.innerHTML = "";
  (data.resolutions || []).forEach((r) => {
    const b = document.createElement("button");
    b.className = "res-btn" + (r.exact_match ? " exact" : "");
    b.innerHTML = `${r.label}<span class="tag">${r.exact_match ? "Badha" : "Kera-kera"}</span>`;
    b.addEventListener("click", () => startDownload(originalUrl, r.height));
    resolutionsWrap.appendChild(b);
  });

  resultSection.classList.remove("hidden");
}

function startDownload(url, height) {
  const params = new URLSearchParams({ url, height });
  showToast(`Ngala' e ${height}p...`);
  window.location.href = `${API_BASE}/api/download?${params.toString()}`;
}

function formatDuration(seconds) {
  const s = Math.floor(seconds % 60);
  const m = Math.floor((seconds / 60) % 60);
  const h = Math.floor(seconds / 3600);
  const pad = (n) => String(n).padStart(2, "0");
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.innerHTML = loading ? '<span class="spinner"></span>Gi\' pareksa...' : "Pareksa video";
}

function showStatus(message, isError) {
  statusSection.textContent = message;
  statusSection.classList.remove("hidden");
  statusSection.classList.toggle("error", !!isError);
}

function hideStatus() {
  statusSection.classList.add("hidden");
}

function hideResult() {
  resultSection.classList.add("hidden");
}

let toastTimer = null;
function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}
