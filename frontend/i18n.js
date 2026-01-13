(() => {
  const STORAGE_KEY = "lufs_lang";

  const MESSAGES = {
    en: {
      lang: { en: "EN", ru: "RU" },

      hero: {
        eyebrow: "LUFS tool",
        title: "Audio Loudness Normalizer",
        subtitle:
          "LUFS Normalizer is an online tool that sets your audio to a target loudness (LUFS) so videos, podcasts, and recordings sound consistent across platforms.",
        note:
          "Upload an MP3/WAV, choose a target (YouTube −14 LUFS, Podcast −16 LUFS, Broadcast −23 LUFS) or enter your own, set format/bitrate if needed, then click “Normalize”. Download the result and optionally keep it in History and tag it.",
        commonTargetsTitle: "Common targets",
        helper: "Use the preset buttons below to fill these instantly."
      },

      tabs: {
        normalize: "Normalize",
        history: "History",
        tags: "Tags"
      },

      normalize: {
        title: "Normalize Audio",
        subtitle: "Choose your settings and normalize in one click.",
        presetTargets: "Preset targets",
        presetHelp: "Click a preset or enter your own target below.",
        audioFile: "Audio file",
        audioHelp: "Upload an MP3 or WAV file to normalize.",
        targetLufs: "Target LUFS",
        targetHelp: "Lower is quieter, higher is louder.",
        outputFormat: "Output format",
        outputHelp: "WAV for editing, MP3 for sharing, FLAC for lossless.",
        mp3Bitrate: "MP3 bitrate",
        mp3BitratePlaceholder: "Bitrate (e.g. 192k)",
        mp3BitrateHelp: "Only used for MP3. Common: 128k / 192k / 320k.",
        presetName: "Preset name or tag (optional)",
        presetPlaceholder: "Preset (optional)",
        presetHelp2: "Optional label to find this job later.",
        btnNormalize: "Normalize",
        noteZip: "Creates a ZIP download with your normalized audio.",
        statusReady: "Ready to normalize.",
        downloadLatest: "Download latest result"
      },

      sample: {
        title: "Try a sample in 10 seconds",
        subtitle: "Download → Upload → Click Normalize.",
        download: "Download sample MP3",
        hint404: "If the link is 404: add sample.mp3 into frontend/."
      },

      how: {
        title: "How it works",
        s1: "Upload an MP3 or WAV file.",
        s2: "Pick a target LUFS (or use a preset).",
        s3: "Select output format and bitrate if MP3.",
        s4: "Add an optional label for History.",
        s5: "Click Normalize and download the ZIP."
      },

      history: {
        title: "History",
        refresh: "Refresh",
        subtitle: "Recent jobs appear here after you click Refresh.",
        thFile: "File",
        thFormat: "Format",
        thBefore: "LUFS Before",
        thAfter: "LUFS After",
        thPeak: "Peak",
        thTarget: "Target",
        thTime: "Time",
        thPlot: "Plot",
        empty: "No history yet.",
        loadError: "Failed to load history."
      },

      tags: {
        title: "Edit MP3 Tags",
        subtitle: "Load an MP3 to view and update its metadata.",
        mp3File: "MP3 file",
        mp3Help: "Select an MP3 file to edit tags.",
        btnLoad: "Load Tags",
        statusIdle: "Load an MP3 to edit tags.",
        titleField: "Title",
        artist: "Artist",
        album: "Album",
        date: "Date",
        genre: "Genre",
        composer: "Composer",
        disc: "Disc Number",
        comments: "Comments",
        albumArtist: "Album Artist",
        publisher: "Publisher",
        albumUrl: "Album URL",
        track: "Track Number",
        cover: "Cover Image (jpg/png)",
        coverHelp: "Optional artwork for the MP3 file.",
        btnSave: "Save Tags",
        btnNormalizeThis: "Normalize This MP3"
      },

      runtime: {
        uploading: "Uploading…",
        processing: "Normalizing…",
        done: "Done.",
        error: "Error.",
        errorWithDetails: "Error: {msg}"
      }
    },

    ru: {
      lang: { en: "EN", ru: "RU" },

      hero: {
        eyebrow: "Инструмент LUFS",
        title: "Нормализатор громкости звука",
        subtitle:
          "LUFS-нормализатор — онлайн-инструмент, который приводит громкость вашего аудио к заданному уровню (LUFS), чтобы ролики, подкасты и записи звучали ровно и предсказуемо на разных платформах.",
        note:
          "Загрузите MP3/WAV, выберите цель (YouTube −14 LUFS, Подкаст −16 LUFS, Трансляция −23 LUFS) или задайте своё значение, при необходимости укажите формат/битрейт и нажмите «Нормализировать». После обработки скачайте готовый файл и при желании сохраните результат в Историю и пометьте тегами.",
        commonTargetsTitle: "Общие цели",
        helper: "Используйте кнопки пресетов ниже, чтобы заполнить значения мгновенно."
      },

      tabs: {
        normalize: "Нормализация",
        history: "История",
        tags: "Теги"
      },

      normalize: {
        title: "Нормализация звука",
        subtitle: "Выберите настройки и выполните нормализацию одним кликом.",
        presetTargets: "Предустановленные цели",
        presetHelp: "Нажмите пресет или введите своё значение ниже.",
        audioFile: "Аудиофайл",
        audioHelp: "Загрузите MP3 или WAV для нормализации.",
        targetLufs: "Целевая LUFS",
        targetHelp: "Чем ниже — тише, чем выше — громче.",
        outputFormat: "Формат вывода",
        outputHelp: "WAV — для монтажа, MP3 — для публикации, FLAC — без потерь.",
        mp3Bitrate: "Битрейт MP3",
        mp3BitratePlaceholder: "Битрейт (например, 192k)",
        mp3BitrateHelp: "Используется только для MP3. Часто: 128k / 192k / 320k.",
        presetName: "Название пресета или тег (опционально)",
        presetPlaceholder: "Пресет (опционально)",
        presetHelp2: "Метка, чтобы потом быстро найти задачу в Истории.",
        btnNormalize: "Нормализировать",
        noteZip: "Скачивание будет ZIP-архивом с результатом.",
        statusReady: "Готово к нормализации.",
        downloadLatest: "Скачать последний результат"
      },

      sample: {
        title: "Попробуйте пример за 10 секунд",
        subtitle: "Скачать → Загрузить → Нажать «Нормализировать».",
        download: "Скачать пример MP3",
        hint404: "Если ссылка 404: добавьте sample.mp3 в папку frontend/."
      },

      how: {
        title: "Как это работает",
        s1: "Загрузите MP3 или WAV.",
        s2: "Выберите целевую LUFS (или нажмите пресет).",
        s3: "Укажите формат вывода и битрейт (если MP3).",
        s4: "Добавьте метку для Истории (по желанию).",
        s5: "Нажмите «Нормализировать» и скачайте ZIP."
      },

      history: {
        title: "История",
        refresh: "Обновить",
        subtitle: "Последние задачи появятся после нажатия «Обновить».",
        thFile: "Файл",
        thFormat: "Формат",
        thBefore: "LUFS до",
        thAfter: "LUFS после",
        thPeak: "Пик",
        thTarget: "Цель",
        thTime: "Время",
        thPlot: "График",
        empty: "История пока пустая.",
        loadError: "Не удалось загрузить историю."
      },

      tags: {
        title: "Редактор тегов MP3",
        subtitle: "Загрузите MP3, чтобы посмотреть и обновить метаданные.",
        mp3File: "Файл MP3",
        mp3Help: "Выберите MP3, чтобы редактировать теги.",
        btnLoad: "Загрузить теги",
        statusIdle: "Загрузите MP3 для редактирования тегов.",
        titleField: "Название",
        artist: "Исполнитель",
        album: "Альбом",
        date: "Дата",
        genre: "Жанр",
        composer: "Композитор",
        disc: "Номер диска",
        comments: "Комментарий",
        albumArtist: "Исполнитель альбома",
        publisher: "Издатель",
        albumUrl: "Ссылка на альбом",
        track: "Номер трека",
        cover: "Обложка (jpg/png)",
        coverHelp: "Опциональная обложка для MP3.",
        btnSave: "Сохранить теги",
        btnNormalizeThis: "Нормализировать этот MP3"
      },

      runtime: {
        uploading: "Загрузка…",
        processing: "Нормализация…",
        done: "Готово.",
        error: "Ошибка.",
        errorWithDetails: "Ошибка: {msg}"
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

  function detectInitialLang() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "ru" || saved === "en") return saved;

    const nav = (navigator.language || "").toLowerCase();
    return nav.startsWith("ru") ? "ru" : "en";
  }

  function getLang() {
    const current = document.documentElement.getAttribute("lang");
    return current === "ru" ? "ru" : "en";
  }

  function t(key, params) {
    const lang = getLang();
    const val = deepGet(MESSAGES[lang], key) ?? deepGet(MESSAGES.en, key);
    if (typeof val !== "string") return key;
    return format(val, params);
  }

  function applyTranslations(lang = getLang()) {
    // textContent
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      el.textContent = t(key);
    });

    // innerHTML (use carefully)
    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const key = el.getAttribute("data-i18n-html");
      el.innerHTML = t(key);
    });

    // placeholders
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      el.setAttribute("placeholder", t(key));
    });

    // aria-label
    document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria-label");
      el.setAttribute("aria-label", t(key));
    });

    // titles (tooltip)
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      el.setAttribute("title", t(key));
    });

    // keep <html lang=...> consistent
    document.documentElement.setAttribute("lang", lang);

    // mark active lang buttons if present
    document.querySelectorAll("[data-lang]").forEach((btn) => {
      const isActive = btn.getAttribute("data-lang") === lang;
      btn.classList.toggle("is-active", isActive);
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  function setLang(lang) {
    const normalized = lang === "ru" ? "ru" : "en";
    localStorage.setItem(STORAGE_KEY, normalized);
    document.documentElement.setAttribute("lang", normalized);
    applyTranslations(normalized);
  }

  function init() {
    const initial = detectInitialLang();
    document.documentElement.setAttribute("lang", initial);

    // wire language buttons
    document.querySelectorAll("[data-lang]").forEach((btn) => {
      btn.addEventListener("click", () => setLang(btn.getAttribute("data-lang")));
    });

    applyTranslations(initial);
  }

  window.i18n = { t, setLang, getLang, applyTranslations, init };

  document.addEventListener("DOMContentLoaded", init);
})();
