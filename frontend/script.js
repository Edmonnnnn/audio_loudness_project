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
  const firstTab = document.querySelector(".tab-button");
  if (firstTab) firstTab.click();

  // ---------------------- API base & helpers ----------------------
  // DEV: UI на localhost:3000 → API на 127.0.0.1:8211 (или порт из localStorage.DEV_API_PORT)
  // PROD: UI на домене → API тот же origin с префиксом /lufs/api
  const isDevHost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const DEV_API_PORT = window.localStorage.getItem("DEV_API_PORT") || "8211";
  const DEV_API_BASE = `http://127.0.0.1:${DEV_API_PORT}`;
  const PROD_API_PREFIX = "/lufs/api"; // <— nginx проксирует сюда

  function joinUrl(a, b) {
    if (!a) return b || "";
    if (!b) return a || "";
    return `${a.replace(/\/+$/, "")}/${b.replace(/^\/+/, "")}`;
  }
  function api(path) {
    return isDevHost ? joinUrl(DEV_API_BASE, path) : joinUrl(PROD_API_PREFIX, path);
  }
  // Файлы/графики, что бэк отдаёт по относительному пути (plot_path и т.п.)
  function apiFile(pathFromApi) {
    return isDevHost ? joinUrl(DEV_API_BASE, pathFromApi) : joinUrl(PROD_API_PREFIX, pathFromApi);
  }

  // ---------------------- LUFS sanitizers ----------------------
  function normalizeNumberInput(str) {
    if (str == null) return "";
    let s = String(str).trim()
      .replace(/[\u2212\u2013\u2014]/g, "-") // −,–,— → минус
      .replace(/[\s\u00a0]/g, "")            // пробелы и NBSP
      .replace(",", ".");                    // , → .
    // один минус только в начале
    s = s.replace(/(?!^)-/g, "");
    // одна точка
    const parts = s.split(".");
    if (parts.length > 2) s = parts.shift() + "." + parts.join("");
    return s;
  }
  function parseLUFS(str) {
    const s = normalizeNumberInput(str);
    const n = Number(s);
    return Number.isFinite(n) ? n : NaN;
  }

  // Приводим поле LUFS к нормальному виду на вводе/вставке
  const targetInput = document.getElementById("target-lufs");
  if (targetInput) {
    ["input", "paste", "change", "blur"].forEach((ev) => {
      targetInput.addEventListener(ev, () => {
        const cur = targetInput.value;
        const clean = normalizeNumberInput(cur);
        if (cur !== clean) targetInput.value = clean;
      });
    });
  }

  // ---------------------- Общие ошибки ----------------------
  async function safeText(res) {
    try { return await res.text(); } catch { return res.statusText || "Request failed"; }
  }
  function showFriendlyError(res, rawText) {
    if (res.status === 413) {
      alert("❌ Файл слишком большой (413). Лимит сервера около 100 MB. Попробуйте файл меньшего размера.");
      return;
    }
    alert(`❌ Ошибка запроса (${res.status}).\n${(rawText || "").slice(0, 400)}`);
  }

  // ---------------------- Normalize ----------------------
  const form = document.getElementById("upload-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const file = document.getElementById("file-input").files[0];
      if (!file) return alert("Выберите аудиофайл");

      const target = parseLUFS(document.getElementById("target-lufs")?.value);
      if (!Number.isFinite(target) || target < -40 || target > 0) {
        return alert("Введите корректный Target LUFS от -40 до 0, например -16");
      }

      const format  = document.getElementById("output-format")?.value || "mp3";
      const bitrate = document.getElementById("bitrate")?.value || "";
      const preset  = document.getElementById("preset")?.value || "";

      const fd = new FormData();
      fd.append("file", file);
      fd.append("target_lufs", String(target));
      // Совместимость имён полей
      fd.append("output_format", format);
      fd.append("fmt", format);
      if (bitrate) fd.append("bitrate", bitrate);
      if (preset)  fd.append("preset", preset);

      const btn = form.querySelector('button[type="submit"]');
      try {
        if (btn) { btn.disabled = true; btn.textContent = "Processing…"; }
        const res = await fetch(api("/normalize/"), { method: "POST", body: fd });
        if (!res.ok) {
          const t = await safeText(res);
          console.error("Normalize failed:", res.status, t);
          return showFriendlyError(res, t);
        }
        // Скачивание ZIP
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
        if (btn) { btn.disabled = false; btn.textContent = " Normalize"; }
      }
    });
  }

  // ---------------------- Tags: загрузка ----------------------
  let lastLoadedTagsFile = null; // хранить выбранный MP3 (для Normalize This MP3)
  const tagsForm = document.getElementById("tags-form");
  if (tagsForm) {
    tagsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const file = document.getElementById("tags-file")?.files?.[0];
      if (!file) return alert("Выберите MP3 для чтения тегов");

      const fd = new FormData();
      fd.append("file", file);

      try {
        const res = await fetch(api("/tags/"), { method: "POST", body: fd }); // сервер может называть /tags/extract — у нас прокси на этот эндпоинт
        if (!res.ok) {
          const t = await safeText(res);
          console.error("Tags load failed:", res.status, t);
          return showFriendlyError(res, t);
        }
        const data = await res.json();
        // заполнить поля
        setValue("tag-title",       data.title);
        setValue("tag-artist",      data.artist);
        setValue("tag-album",       data.album);
        setValue("tag-date",        data.date);
        setValue("tag-genre",       data.genre);
        setValue("tag-composer",    data.composer);
        setValue("tag-discnumber",  data.discnumber);
        setValue("tag-comment",     data.comment);
        setValue("tag-albumartist", data.albumartist);
        setValue("tag-publisher",   data.publisher);
        setValue("tag-website",     data.website);
        setValue("tag-tracknumber", data.tracknumber);

        document.getElementById("tags-fields").style.display = "";
        lastLoadedTagsFile = file;
      } catch (err) {
        console.error(err);
        alert("❌ Failed to load tags");
      }
    });
  }

  // ---------------------- Tags: сохранение ----------------------
  const saveTagsBtn = document.getElementById("save-tags-btn");
  if (saveTagsBtn) {
    saveTagsBtn.addEventListener("click", async () => {
      const file = document.getElementById("tags-file")?.files?.[0];
      if (!file) return alert("Выберите MP3 для сохранения тегов");

      const cover = document.getElementById("tag-cover")?.files?.[0];

      const fd = new FormData();
      fd.append("file", file);
      fd.append("title",       getValue("tag-title"));
      fd.append("artist",      getValue("tag-artist"));
      fd.append("album",       getValue("tag-album"));
      fd.append("date",        getValue("tag-date"));
      fd.append("genre",       getValue("tag-genre"));
      fd.append("composer",    getValue("tag-composer"));
      fd.append("discnumber",  getValue("tag-discnumber"));
      fd.append("comment",     getValue("tag-comment"));
      fd.append("albumartist", getValue("tag-albumartist"));
      fd.append("publisher",   getValue("tag-publisher"));
      fd.append("website",     getValue("tag-website"));
      fd.append("tracknumber", getValue("tag-tracknumber"));
      if (cover) fd.append("cover", cover);

      try {
        const res = await fetch(api("/tags/save/"), { method: "POST", body: fd });
        if (!res.ok) {
          const t = await safeText(res);
          console.error("Tags save failed:", res.status, t);
          return showFriendlyError(res, t);
        }
        alert("✅ Tags saved");
      } catch (err) {
        console.error(err);
        alert("❌ Failed to save tags");
      }
    });
  }

  // ---------------------- Normalize This MP3 (из вкладки Tags) ----------------------
  const normThisBtn = document.getElementById("normalize-this-btn");
  if (normThisBtn) {
    normThisBtn.addEventListener("click", async () => {
      if (!lastLoadedTagsFile) return alert("Сначала загрузите MP3 на вкладке Tags");

      const target = parseLUFS(document.getElementById("target-lufs")?.value);
      if (!Number.isFinite(target) || target < -40 || target > 0) {
        return alert("Введите корректный Target LUFS от -40 до 0, например -16");
      }
      const outputFormat = document.getElementById("output-format")?.value || "mp3";
      const bitrate = document.getElementById("bitrate")?.value || "";
      const preset  = document.getElementById("preset")?.value || "";

      const fd = new FormData();
      // Некоторые реализации /normalize_cached/ берут имя файла/ключ; на всякий — положим и сам файл
      fd.append("file", lastLoadedTagsFile);
      fd.append("filename", lastLoadedTagsFile.name);
      fd.append("target_lufs", String(target));
      // Совместимость имён полей
      fd.append("output_format", outputFormat);
      fd.append("fmt", outputFormat);
      if (bitrate) fd.append("bitrate", bitrate);
      if (preset)  fd.append("preset", preset);

      try {
        const res = await fetch(api("/normalize_cached/"), { method: "POST", body: fd });
        if (!res.ok) {
          const t = await safeText(res);
          console.error("Normalize cached failed:", res.status, t);
          return showFriendlyError(res, t);
        }

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
        if (!res.ok) {
          const t = await safeText(res);
          console.error("History failed:", res.status, t);
          return showFriendlyError(res, t);
        }
        const data = await res.json();

        const tbody = document.querySelector("#history-table tbody");
        tbody.innerHTML = "";
        data.forEach((entry) => {
          const plotHref = entry.plot_path ? apiFile(String(entry.plot_path)) : null;
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
    if (el) el.value = val ?? "";
  }
  function getValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
  }
  function safeNum(x) {
    return (x === null || x === undefined || Number.isNaN(Number(x))) ? "-" : x;
  }
  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[c]);
  }
};
