// frontend/script.js
window.onload = function () {
  // ---------------------- Tabs ----------------------
  document.querySelectorAll(".tab-button").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-content").forEach((tab) => (tab.style.display = "none"));
      const tabId = btn.getAttribute("data-tab");
      document.getElementById(tabId).style.display = "block";
    });
  });
  // показать первую вкладку по умолчанию
  const firstTab = document.querySelector(".tab-button");
  if (firstTab) firstTab.click();

  // ---------------------- API base ----------------------
  // Локально UI обычно открыт на 127.0.0.1:3000 (или localhost:3000) → API = 127.0.0.1:8211
  // На сервере UI открыт на домене → API тот же origin через Nginx (пустая строка).
  const API_BASE = (() => {
    const { hostname } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      const devPort = window.localStorage.getItem("DEV_API_PORT") || "8211"; // сменить на "8212" при желании
      return `http://127.0.0.1:${devPort}`;
    }
    return ""; // прод: тот же домен
  })();
  const api = (path) => `${API_BASE}${path}`;

  // ---------------------- Normalize ----------------------
  const form = document.getElementById("upload-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const file = document.getElementById("file-input").files[0];
      if (!file) return alert("Choose file first");

      const lufs = document.getElementById("target-lufs").value;
      const format = document.getElementById("output-format").value;
      const bitrate = document.getElementById("bitrate").value;
      const preset = document.getElementById("preset").value;

      const fd = new FormData();
      fd.append("file", file);
      if (lufs !== "") fd.append("target_lufs", lufs);
      fd.append("output_format", format);
      fd.append("bitrate", bitrate);
      if (preset) fd.append("preset", preset);

      try {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) { btn.disabled = true; btn.textContent = "Processing…"; }

        const res = await fetch(api("/normalize/"), { method: "POST", body: fd });
        if (!res.ok) throw new Error(await safeText(res));

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "result.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error(err);
        alert("❌ Normalization failed");
      } finally {
        const btn = form.querySelector('button[type="submit"]');
        if (btn) { btn.disabled = false; btn.textContent = "🎚️ Normalize"; }
      }
    });
  }

  // ---------------------- Load Tags ----------------------
  const tagsForm = document.getElementById("tags-form");
  if (tagsForm) {
    tagsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const file = document.getElementById("tags-file").files[0];
      if (!file) return alert("Choose MP3 file first");

      const fd = new FormData();
      fd.append("file", file);

      try {
        const res = await fetch(api("/tags/"), { method: "POST", body: fd }); // если у тебя на бэке /tags/extract — поменяй здесь
        if (!res.ok) throw new Error(await safeText(res));
        const data = await res.json();

        document.getElementById("tags-fields").style.display = "block";
        setValue("tag-title", data.title);
        setValue("tag-artist", data.artist);
        setValue("tag-album", data.album);
        setValue("tag-date", data.date);
        setValue("tag-genre", data.genre);
        setValue("tag-composer", data.composer);
        setValue("tag-discnumber", data.discnumber);
        setValue("tag-comment", data.comment);
        setValue("tag-albumartist", data.albumartist);
        setValue("tag-publisher", data.publisher);
        setValue("tag-website", data.website);
        setValue("tag-tracknumber", data.tracknumber);
      } catch (err) {
        console.error(err);
        alert("❌ Failed to load tags");
      }
    });
  }

  // ---------------------- Save Tags ----------------------
  const saveBtn = document.getElementById("save-tags-btn");
  if (saveBtn) {
    saveBtn.addEventListener("click", async () => {
      const file = document.getElementById("tags-file").files[0];
      const status = document.getElementById("tags-status");
      const cover = document.getElementById("tag-cover").files[0];
      if (!file) return alert("Choose MP3 file first");

      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", getValue("tag-title"));
      fd.append("artist", getValue("tag-artist"));
      fd.append("album", getValue("tag-album"));
      fd.append("date", getValue("tag-date"));
      fd.append("genre", getValue("tag-genre"));
      fd.append("composer", getValue("tag-composer"));
      fd.append("discnumber", getValue("tag-discnumber"));
      fd.append("comment", getValue("tag-comment"));
      fd.append("albumartist", getValue("tag-albumartist"));
      fd.append("publisher", getValue("tag-publisher"));
      fd.append("website", getValue("tag-website"));
      fd.append("tracknumber", getValue("tag-tracknumber"));
      if (cover) fd.append("cover", cover);

      status.textContent = "⏳ Saving...";
      status.style.color = "";

      try {
        const res = await fetch(api("/tags/save/"), { method: "POST", body: fd }); // если у тебя /tags/update — поменяй здесь
        if (!res.ok) throw new Error(await safeText(res));
        const data = await res.json();
        status.textContent = data.message || "✅ Tags saved!";
        status.style.color = "lightgreen";
      } catch (err) {
        console.error(err);
        status.textContent = "❌ Failed to save tags.";
        status.style.color = "red";
      }
    });
  }

  // ---------------------- Normalize cached ----------------------
  const normThisBtn = document.getElementById("normalize-this-btn");
  if (normThisBtn) {
    normThisBtn.addEventListener("click", async () => {
      const file = document.getElementById("tags-file").files[0];
      if (!file) return alert("Choose MP3 file first");

      const targetLufs = prompt("Target LUFS?", "-14") || "-14";
      const outputFormat = prompt("Output format (mp3/wav/flac)?", "mp3") || "mp3";
      const bitrate = prompt("Bitrate (e.g. 192k)?", "192k") || "192k";
      const preset = "";

      const fd = new FormData();
      fd.append("filename", file.name);
      fd.append("target_lufs", targetLufs);
      fd.append("output_format", outputFormat);
      fd.append("bitrate", bitrate);
      fd.append("preset", preset);

      try {
        const res = await fetch(api("/normalize_cached/"), { method: "POST", body: fd });
        if (!res.ok) throw new Error(await safeText(res));

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "result.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error(err);
        alert("❌ Normalization failed");
      }
    });
  }

  // ---------------------- History ----------------------
  const refreshBtn = document.getElementById("refresh-history");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", async () => {
      try {
        const res = await fetch(api("/history/"));
        if (!res.ok) throw new Error(await safeText(res));
        const data = await res.json();

        const tbody = document.querySelector("#history-table tbody");
        tbody.innerHTML = "";
        data.forEach((entry) => {
          const plotHref = entry.plot_path
            ? `${API_BASE}/${String(entry.plot_path).replace(/^\//, "")}`
            : null;

          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>${escapeHtml(entry.filename)}</td>
            <td>${escapeHtml(entry.format)}</td>
            <td>${safeNum(entry.lufs_before)}</td>
            <td>${safeNum(entry.lufs_after)}</td>
            <td>${safeNum(entry.peak)}</td>
            <td>${safeNum(entry.target_lufs)}</td>
            <td>${entry.created_at ? new Date(entry.created_at).toLocaleString() : "-"}</td>
            <td>${plotHref ? `<a href="${plotHref}" target="_blank" rel="noopener">View</a>` : "-"}</td>
          `;
          tbody.appendChild(tr);
        });
      } catch (err) {
        console.error(err);
        alert("❌ Failed to load history");
      }
    });
  }

  // ---------------------- Helpers ----------------------
  function setValue(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val || "";
  }
  function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
  }
  async function safeText(res) {
    try { return await res.text(); } catch { return res.statusText || "Request failed"; }
  }
  function safeNum(x) {
    return (x === null || x === undefined || Number.isNaN(Number(x))) ? "-" : x;
  }
  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }
};
