// frontend/script.js
window.onload = function () {

  const t = (key, params) => (window.i18n && typeof window.i18n.t === "function")
  ? window.i18n.t(key, params)
  : key;

  // ---------------------- i18n helpers ----------------------
  const I18N = window.i18n || null;

  function getLang() {
    if (I18N && typeof I18N.getLang === "function") return I18N.getLang();
    return document.documentElement.getAttribute("lang") === "ru" ? "ru" : "en";
  }

  // Доп. фразы, которых нет в i18n.js (чтобы не заставлять тебя прямо сейчас расширять i18n.js)
  const EXTRA = {
    en: {
      validate: {
        chooseAudioFirst: "Please choose an audio file first.",
        chooseMp3First: "Please choose an MP3 file first.",
        invalidTarget: "Please enter a target LUFS between -40 and 0 (e.g. -16).",
        loadTagsBeforeNormalize: "Load tags for an MP3 before normalizing."
      },
      alerts: {
        fileTooLarge:
          "File is too large (413). Server limit is around 100 MB. Try a smaller file.",
        requestFailed: "Request failed ({status}).",
        normalizationFailed: "Normalization failed.",
        tagsLoadFailed: "Failed to load tags.",
        tagsSaveFailed: "Failed to save tags.",
        tagsSaved: "Tags saved.",
        historyLoadFailed: "Failed to load history."
      },
      normalize: {
        working: "Uploading and normalizing. This can take a minute.",
        processingBtn: "Processing…",
        done: "Done. Your download should start now.",
        failedTryAgain: "Normalization failed. Please try again."
      },
      tags: {
        loading: "Loading tags...",
        loaded: "Tags loaded. You can edit and save.",
        saving: "Saving tags...",
        normalizeWorking: "Normalizing this MP3. This can take a minute."
      },
      history: {
        view: "View"
      }
    },
    ru: {
      validate: {
        chooseAudioFirst: "Сначала выберите аудиофайл.",
        chooseMp3First: "Сначала выберите MP3 файл.",
        invalidTarget: "Введите корректный Target LUFS от -40 до 0 (например, -16).",
        loadTagsBeforeNormalize: "Сначала загрузите теги MP3, затем нормализуйте."
      },
      alerts: {
        fileTooLarge:
          "Файл слишком большой (413). Лимит сервера около 100 MB. Попробуйте файл меньшего размера.",
        requestFailed: "Ошибка запроса ({status}).",
        normalizationFailed: "Нормализация не удалась.",
        tagsLoadFailed: "Не удалось загрузить теги.",
        tagsSaveFailed: "Не удалось сохранить теги.",
        tagsSaved: "Теги сохранены.",
        historyLoadFailed: "Не удалось загрузить историю."
      },
      normalize: {
        working: "Загрузка и нормализация. Это может занять до минуты.",
        processingBtn: "Обработка…",
        done: "Готово. Загрузка должна начаться автоматически.",
        failedTryAgain: "Нормализация не удалась. Попробуйте ещё раз."
      },
      tags: {
        loading: "Загрузка тегов…",
        loaded: "Теги загружены. Можно редактировать и сохранить.",
        saving: "Сохранение тегов…",
        normalizeWorking: "Нормализация этого MP3. Это может занять до минуты."
      },
      history: {
        view: "Открыть"
      }
    }
  };

  function deepGet(obj, path) {
    return path.split(".").reduce((acc, key) => (acc && acc[key] != null ? acc[key] : undefined), obj);
  }

  function format(str, params) {
    if (!params) return str;
    return str.replace(/\{(\w+)\}/g, (_, k) => (params[k] != null ? String(params[k]) : `{${k}}`));
  }

  // Основной перевод: сначала пытаемся из i18n.js, если ключ не найден — берём из EXTRA.
  function tr(key, params) {
    // 1) i18n.js
    if (I18N && typeof I18N.t === "function") {
      const val = I18N.t(key, params);
      if (val && val !== key) return val;
    }
    // 2) EXTRA (lang)
    const lang = getLang();
    let v = deepGet(EXTRA[lang], key);
    if (typeof v !== "string") v = deepGet(EXTRA.en, key);
    if (typeof v !== "string") return key;
    return format(v, params);
  }

  // ---------------------- Tabs ----------------------
  const tabButtons = document.querySelectorAll(".tab-button");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-content").forEach((tab) => (tab.style.display = "none"));
      tabButtons.forEach((button) => {
        button.classList.remove("is-active");
        button.setAttribute("aria-selected", "false");
      });
      const tabId = btn.getAttribute("data-tab");
      const tabEl = document.getElementById(tabId);
      if (tabEl) tabEl.style.display = "block";
      btn.classList.add("is-active");
      btn.setAttribute("aria-selected", "true");
    });
  });
  const firstTab = tabButtons[0];
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
    let s = String(str)
      .trim()
      .replace(/[\u2212\u2013\u2014]/g, "-") // −,–,— → минус
      .replace(/[\s\u00a0]/g, "") // пробелы и NBSP
      .replace(",", "."); // , → .
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

    function wireFilePicker(inputId, btnId, nameId, emptyKey) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    const name = document.getElementById(nameId);
    if (!input || !btn || !name) return;

    const update = () => {
      const f = input.files && input.files[0];
      name.textContent = f ? f.name : t(emptyKey);
    };

    btn.addEventListener("click", () => input.click());
    input.addEventListener("change", update);

    // чтобы при переключении RU/EN, если файл выбран — показывалось имя, а не "Файл не выбран"
    window.addEventListener("lufs:lang-changed", update);

    update();
  }

  wireFilePicker("file", "file-btn", "file-name", "normalize.noFile");
  wireFilePicker("tags-file", "tags-file-btn", "tags-file-name", "tags.noFile");


  // Приводим поле LUFS к нормальному виду на вводе/вставке
  const targetInput = document.getElementById("lufs");
  const presetButtons = Array.from(document.querySelectorAll(".lufs-preset"));
  function updatePresetState(value) {
    const normalized = normalizeNumberInput(value);
    presetButtons.forEach((btn) => {
      const btnValue = normalizeNumberInput(btn.getAttribute("data-lufs"));
      const isMatch = normalized !== "" && btnValue === normalized;
      btn.classList.toggle("is-selected", isMatch);
      btn.setAttribute("aria-pressed", isMatch ? "true" : "false");
    });
  }
  if (targetInput) {
    ["input", "paste", "change", "blur"].forEach((ev) => {
      targetInput.addEventListener(ev, () => {
        const cur = targetInput.value;
        const clean = normalizeNumberInput(cur);
        if (cur !== clean) targetInput.value = clean;
        updatePresetState(targetInput.value);
      });
    });
  }
  presetButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const value = btn.getAttribute("data-lufs");
      if (targetInput && value) {
        targetInput.value = value;
        targetInput.dispatchEvent(new Event("input", { bubbles: true }));
        updatePresetState(value);
      }
    });
  });
  if (targetInput) updatePresetState(targetInput.value);

  // ---------------------- Общие ошибки ----------------------
  async function safeText(res) {
    try {
      return await res.text();
    } catch {
      return res.statusText || tr("alerts.requestFailed", { status: res.status });
    }
  }

  function showFriendlyError(res, rawText) {
    if (res.status === 413) {
      alert(tr("alerts.fileTooLarge"));
      return;
    }
    alert(`${tr("alerts.requestFailed", { status: res.status })}\n${(rawText || "").slice(0, 400)}`);
  }

  function setStatus(id, message, state) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = message || "";
    if (state) {
      el.setAttribute("data-state", state);
    } else {
      el.removeAttribute("data-state");
    }
  }

  let lastNormalizeUrl = null;
  function setDownloadLink(url) {
    const link = document.getElementById("normalize-download");
    if (!link) return;
    if (url) {
      link.href = url;
      link.style.display = "inline-flex";
      // если в HTML у ссылки стоит data-i18n — не трогаем, но на всякий:
      if (!link.hasAttribute("data-i18n")) link.textContent = tr("normalize.downloadLatest");
    } else {
      link.removeAttribute("href");
      link.style.display = "none";
    }
  }

  // ---------------------- Language switch hook (refresh dynamic texts) ----------------------
  let lastHistoryData = null;

  function renderHistory(data) {
    const tbody = document.querySelector("#history-table tbody");
    if (!tbody) return;

    tbody.innerHTML = "";
    if (!Array.isArray(data) || data.length === 0) {
      const trEl = document.createElement("tr");
      trEl.innerHTML = `<td colspan="8">${escapeHtml(tr("history.empty"))}</td>`;
      tbody.appendChild(trEl);
      return;
    }

    data.forEach((entry) => {
      const plotHref = entry.plot_path ? apiFile(String(entry.plot_path)) : null;
      const trRow = document.createElement("tr");
      trRow.innerHTML = `
        <td>${escapeHtml(entry.filename)}</td>
        <td>${escapeHtml(entry.format)}</td>
        <td>${safeNum(entry.lufs_before)}</td>
        <td>${safeNum(entry.lufs_after)}</td>
        <td>${safeNum(entry.peak)}</td>
        <td>${safeNum(entry.target_lufs)}</td>
        <td>${entry.created_at ? new Date(entry.created_at).toLocaleString() : "-"}</td>
        <td>${plotHref ? `<a href="${plotHref}" target="_blank" rel="noopener">${escapeHtml(tr("history.view"))}</a>` : "-"}</td>
      `;
      tbody.appendChild(trRow);
    });
  }

  function refreshIdleStatusesOnLangChange() {
    // Normalize status: если ничего не делаем и нет явного состояния — поставить "ready"
    const normEl = document.getElementById("normalize-status");
    if (normEl) {
      const state = normEl.getAttribute("data-state");
      if (!state) setStatus("normalize-status", tr("normalize.statusReady"), "");
    }

    // Tags status: если ничего не загружено — дефолт
    const tagsEl = document.getElementById("tags-status");
    if (tagsEl) {
      const state = tagsEl.getAttribute("data-state");
      const fieldsVisible = document.getElementById("tags-fields")?.style?.display !== "none";
      if (!state && !fieldsVisible) setStatus("tags-status", tr("tags.statusIdle"), "");
    }

    // Перерисовать History, если уже грузили
    if (lastHistoryData) renderHistory(lastHistoryData);
  }

  // слушаем клики по кнопкам языка (data-lang)
  document.querySelectorAll("[data-lang]").forEach((btn) => {
    btn.addEventListener("click", () => {
      // i18n.js сам поменяет HTML тексты; мы обновим только динамику
      setTimeout(refreshIdleStatusesOnLangChange, 0);
    });
  });

  // ---------------------- Normalize ----------------------
  const form = document.getElementById("upload-form");
  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const fileInput = document.getElementById("file");
      const file = fileInput?.files?.[0];

      if (!file) {
        setStatus("normalize-status", tr("validate.chooseAudioFirst"), "error");
        return alert(tr("validate.chooseAudioFirst"));
      }

      const target = parseLUFS(document.getElementById("lufs")?.value);
      if (!Number.isFinite(target) || target < -40 || target > 0) {
        setStatus("normalize-status", tr("validate.invalidTarget"), "error");
        return alert(tr("validate.invalidTarget"));
      }

      const format = document.getElementById("format")?.value || "mp3";
      const bitrate = document.getElementById("bitrate")?.value || "";
      const preset = document.getElementById("preset")?.value || "";

      const fd = new FormData();
      fd.append("file", file);
      fd.append("target_lufs", String(target));
      // Совместимость имён полей
      fd.append("output_format", format);
      fd.append("fmt", format);
      if (bitrate) fd.append("bitrate", bitrate);
      if (preset) fd.append("preset", preset);

      const btn = form.querySelector('button[type="submit"]');

      if (lastNormalizeUrl) {
        URL.revokeObjectURL(lastNormalizeUrl);
        lastNormalizeUrl = null;
      }

      setDownloadLink("");
      setStatus("normalize-status", tr("normalize.working"), "working");

      try {
        if (btn) {
          btn.disabled = true;
          btn.textContent = tr("normalize.processingBtn");
        }

        const res = await fetch(api("/normalize/"), { method: "POST", body: fd });
        if (!res.ok) {
          const raw = await safeText(res);
          console.error("Normalize failed:", res.status, raw);
          setStatus("normalize-status", tr("runtime.error"), "error");
          showFriendlyError(res, raw);
          return;
        }

        // Скачивание ZIP
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        lastNormalizeUrl = url;

        const a = document.createElement("a");
        a.href = url;
        a.download = "result.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();

        setDownloadLink(url);
        setStatus("normalize-status", tr("normalize.done"), "success");
      } catch (err) {
        console.error(err);
        setStatus("normalize-status", tr("normalize.failedTryAgain"), "error");
        alert(tr("alerts.normalizationFailed"));
      } finally {
        if (btn) {
          btn.disabled = false;
          // вернём текст кнопки на текущем языке
          btn.textContent = tr("normalize.btnNormalize");
        }
      }
    });
  }

  // ---------------------- Tags: загрузка ----------------------
  let lastLoadedTagsFile = null; // хранить выбранный MP3 (для Normalize This MP3)
  const tagsForm = document.getElementById("tags-form");
  if (tagsForm) {
    tagsForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const file = document.getElementById("file").files[0];
      if (!file) {
        const msg = t("validate.chooseAudioFirst");
        setStatus("normalize-status", msg, "error");
        return alert(msg);
      }


      const fd = new FormData();
      fd.append("file", file);
      setStatus("tags-status", tr("tags.loading"), "working");

      try {
        const res = await fetch(api("/tags/"), { method: "POST", body: fd });
        if (!res.ok) {
          const raw = await safeText(res);
          console.error("Tags load failed:", res.status, raw);
          setStatus("tags-status", tr("tags.loadError"), "error");
          return showFriendlyError(res, raw);
        }

        const data = await res.json();
        // заполнить поля
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

        document.getElementById("tags-fields").style.display = "";
        lastLoadedTagsFile = file;

        setStatus("tags-status", tr("tags.loaded"), "success");
      } catch (err) {
        console.error(err);
        setStatus("tags-status", tr("tags.loadError"), "error");
        alert(tr("alerts.tagsLoadFailed"));
      }
    });
  }

  // ---------------------- Tags: сохранение ----------------------
  const saveTagsBtn = document.getElementById("save-tags-btn");
  if (saveTagsBtn) {
    saveTagsBtn.addEventListener("click", async () => {
      const file = document.getElementById("tags-file")?.files?.[0];
      if (!file) {
        const msg = t("validate.chooseMp3First");
        setStatus("tags-status", msg, "error");
        return alert(msg);
      }



      const cover = document.getElementById("tag-cover")?.files?.[0];

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

      setStatus("tags-status", tr("tags.saving"), "working");

      try {
        const res = await fetch(api("/tags/save/"), { method: "POST", body: fd });
        if (!res.ok) {
          const raw = await safeText(res);
          console.error("Tags save failed:", res.status, raw);
          setStatus("tags-status", tr("tags.saveError"), "error");
          return showFriendlyError(res, raw);
        }

        setStatus("tags-status", tr("tags.saved"), "success");
        alert(tr("alerts.tagsSaved"));
      } catch (err) {
        console.error(err);
        setStatus("tags-status", tr("tags.saveError"), "error");
        alert(tr("alerts.tagsSaveFailed"));
      }
    });
  }

  // ---------------------- Normalize This MP3 (из вкладки Tags) ----------------------
  const normThisBtn = document.getElementById("normalize-this-btn");
  if (normThisBtn) {
    normThisBtn.addEventListener("click", async () => {
      if (!lastLoadedTagsFile) {
        setStatus("tags-status", tr("validate.loadTagsBeforeNormalize"), "error");
        return alert(tr("validate.loadTagsBeforeNormalize"));
      }

      const target = parseLUFS(document.getElementById("lufs")?.value);
      if (!Number.isFinite(target) || target < -40 || target > 0) {
        setStatus("tags-status", tr("validate.invalidTarget"), "error");
        return alert(tr("validate.invalidTarget"));
      }

      const outputFormat = document.getElementById("format")?.value || "mp3";
      const bitrate = document.getElementById("bitrate")?.value || "";
      const preset = document.getElementById("preset")?.value || "";

      const fd = new FormData();
      fd.append("file", lastLoadedTagsFile);
      fd.append("filename", lastLoadedTagsFile.name);
      fd.append("target_lufs", String(target));
      // Совместимость имён полей
      fd.append("output_format", outputFormat);
      fd.append("fmt", outputFormat);
      if (bitrate) fd.append("bitrate", bitrate);
      if (preset) fd.append("preset", preset);

      setStatus("tags-status", tr("tags.normalizeWorking"), "working");

      try {
        const res = await fetch(api("/normalize_cached/"), { method: "POST", body: fd });
        if (!res.ok) {
          const raw = await safeText(res);
          console.error("Normalize cached failed:", res.status, raw);
          setStatus("tags-status", tr("runtime.error"), "error");
          return showFriendlyError(res, raw);
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

        setStatus("tags-status", tr("normalize.done"), "success");
      } catch (err) {
        console.error(err);
        setStatus("tags-status", tr("normalize.failedTryAgain"), "error");
        alert(tr("alerts.normalizationFailed"));
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
          const raw = await safeText(res);
          console.error("History failed:", res.status, raw);
          return showFriendlyError(res, raw);
        }

        const data = await res.json();
        lastHistoryData = data;
        renderHistory(data);
      } catch (err) {
        console.error(err);
        alert(tr("alerts.historyLoadFailed"));
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
    return x === null || x === undefined || Number.isNaN(Number(x)) ? "-" : x;
  }
  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;"
    }[c]));
  }

  // На всякий — привести дефолтные статусы к текущему языку при старте
  refreshIdleStatusesOnLangChange();
};
