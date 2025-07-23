window.onload = function () {
    // Tabs
    document.querySelectorAll(".tab-button").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-content").forEach((tab) => tab.style.display = "none");
        const tabId = btn.getAttribute("data-tab");
        document.getElementById(tabId).style.display = "block";
      });
    });
  
    // Normalize
    const form = document.getElementById("upload-form");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
  
      const file = document.getElementById("file-input").files[0];
      const lufs = document.getElementById("target-lufs").value;
      const format = document.getElementById("output-format").value;
      const bitrate = document.getElementById("bitrate").value;
      const preset = document.getElementById("preset").value;
  
      const formData = new FormData();
      formData.append("file", file);
      formData.append("target_lufs", lufs);
      formData.append("output_format", format);
      formData.append("bitrate", bitrate);
      formData.append("preset", preset);
  
      const res = await fetch("http://127.0.0.1:8000/normalize/", {
        method: "POST",
        body: formData,
      });
  
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "result.zip";
        a.click();
      } else {
        alert("❌ Normalization failed");
      }
    });
  
    // Load Tags
    const loadBtn = document.querySelector("#tags-form button");
    loadBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      const file = document.getElementById("tags-file").files[0];
      if (!file) return alert("Choose MP3 file first");
  
      const formData = new FormData();
      formData.append("file", file);
  
      const res = await fetch("http://127.0.0.1:8000/tags/", {
        method: "POST",
        body: formData,
      });
  
      if (res.ok) {
        const data = await res.json();
        document.getElementById("tags-fields").style.display = "block";
        document.getElementById("tag-title").value = data.title || "";
        document.getElementById("tag-artist").value = data.artist || "";
        document.getElementById("tag-album").value = data.album || "";
        document.getElementById("tag-date").value = data.date || "";
        document.getElementById("tag-genre").value = data.genre || "";
        document.getElementById("tag-composer").value = data.composer || "";
        document.getElementById("tag-discnumber").value = data.discnumber || "";
        document.getElementById("tag-comment").value = data.comment || "";
        document.getElementById("tag-albumartist").value = data.albumartist || "";
        document.getElementById("tag-publisher").value = data.publisher || "";
        document.getElementById("tag-website").value = data.website || "";
        document.getElementById("tag-tracknumber").value = data.tracknumber || "";
      } else {
        alert("❌ Failed to load tags");
      }
    });
  
    // Save Tags
    document.getElementById("save-tags-btn").addEventListener("click", async () => {
      const file = document.getElementById("tags-file").files[0];
      const status = document.getElementById("tags-status");
      const cover = document.getElementById("tag-cover").files[0];
  
      if (!file) {
        alert("Choose MP3 file first");
        return;
      }
  
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", document.getElementById("tag-title").value);
      formData.append("artist", document.getElementById("tag-artist").value);
      formData.append("album", document.getElementById("tag-album").value);
      formData.append("date", document.getElementById("tag-date").value);
      formData.append("genre", document.getElementById("tag-genre").value);
      formData.append("composer", document.getElementById("tag-composer").value);
      formData.append("discnumber", document.getElementById("tag-discnumber").value);
      formData.append("comment", document.getElementById("tag-comment").value);
      formData.append("albumartist", document.getElementById("tag-albumartist").value);
      formData.append("publisher", document.getElementById("tag-publisher").value);
      formData.append("website", document.getElementById("tag-website").value);
      formData.append("tracknumber", document.getElementById("tag-tracknumber").value);
      if (cover) formData.append("cover", cover);
  
      status.innerText = "⏳ Saving...";
  
      const res = await fetch("http://127.0.0.1:8000/tags/save/", {
        method: "POST",
        body: formData
      });
  
      if (res.ok) {
        status.innerText = "✅ Tags saved!";
        status.style.color = "lightgreen";
      } else {
        status.innerText = "❌ Failed to save tags.";
        status.style.color = "red";
      }
    });
  

    document.getElementById("normalize-this-btn").addEventListener("click", async () => {
        const fileInput = document.getElementById("tags-file");
        const file = fileInput.files[0];
        if (!file) {
          alert("Choose MP3 file first");
          return;
        }
      
        // Можно добавить параметры или спросить пользователя
        const targetLufs = prompt("Target LUFS?", "-14") || "-14";
        const outputFormat = prompt("Output format (mp3/wav/flac)?", "mp3") || "mp3";
        const bitrate = prompt("Bitrate (e.g. 192k)?", "192k") || "192k";
        const preset = ""; // Можно тоже сделать через prompt, если используешь
      
        const formData = new FormData();
        formData.append("filename", file.name);
        formData.append("target_lufs", targetLufs);
        formData.append("output_format", outputFormat);
        formData.append("bitrate", bitrate);
        formData.append("preset", preset);
      
        const res = await fetch("http://127.0.0.1:8000/normalize_cached/", {
          method: "POST",
          body: formData,
        });
      
        if (res.ok) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "result.zip";
          a.click();
        } else {
          alert("❌ Normalization failed");
        }
      });
      
    // Refresh History
    document.getElementById("refresh-history").addEventListener("click", async () => {
      const res = await fetch("http://127.0.0.1:8000/history/");
      const data = await res.json();
  
      const table = document.getElementById("history-table").querySelector("tbody");
      table.innerHTML = "";
  
      data.forEach((entry) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${entry.filename}</td>
          <td>${entry.format}</td>
          <td>${entry.lufs_before}</td>
          <td>${entry.lufs_after}</td>
          <td>${entry.peak}</td>
          <td>${entry.target_lufs}</td>
          <td>${entry.created_at ? new Date(entry.created_at).toLocaleString() : "-"}</td>
          <td>${entry.plot_path ? `<a href="http://127.0.0.1:8000/${entry.plot_path}" target="_blank">View</a>` : "-"}</td>
        `;
        table.appendChild(row);
      });
    });
  };
  