(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const HEADER_BYTES = 9;

  const els = {
    tabEmbed: $("st-tab-embed"),
    tabExtract: $("st-tab-extract"),
    panelEmbed: $("st-panel-embed"),
    panelExtract: $("st-panel-extract"),
    message: $("st-message"),

    eFile: $("st-e-file"),
    eCapacity: $("st-e-capacity"),
    eText: $("st-e-text"),
    eKey: $("st-e-key"),
    eBtn: $("st-e-btn"),
    eResult: $("st-e-result"),
    eImg: $("st-e-img"),
    eStats: $("st-e-stats"),
    eCipher: $("st-e-cipher"),
    eDownload: $("st-e-download"),

    xFile: $("st-x-file"),
    xKey: $("st-x-key"),
    xBtn: $("st-x-btn"),
    xResult: $("st-x-result"),
    xRaw: $("st-x-raw"),
    xPlain: $("st-x-plain"),
    xPlainLabel: $("st-x-plain-label"),
  };

  function showMessage(text, type = "error") {
    els.message.textContent = text;
    els.message.className = `message ${type}`;
    els.message.hidden = !text;
  }

  function selectTab(name) {
    const embed = name === "embed";
    els.tabEmbed.classList.toggle("active", embed);
    els.tabExtract.classList.toggle("active", !embed);
    els.tabEmbed.setAttribute("aria-selected", String(embed));
    els.tabExtract.setAttribute("aria-selected", String(!embed));
    els.panelEmbed.hidden = !embed;
    els.panelExtract.hidden = embed;
    showMessage("");
  }

  function formatBytes(n) {
    return n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} byte`;
  }

  /* Tampilkan kapasitas gambar begitu file dipilih */
  function showCapacity(file) {
    els.eCapacity.textContent = "";
    if (!file) return;
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const cap = Math.max(0, Math.floor((img.naturalWidth * img.naturalHeight * 3) / 8) - HEADER_BYTES);
      els.eCapacity.textContent =
        `Ukuran ${img.naturalWidth}×${img.naturalHeight} px · kapasitas maksimal ${formatBytes(cap)} pesan.`;
      URL.revokeObjectURL(url);
    };
    img.onerror = () => URL.revokeObjectURL(url);
    img.src = url;
  }

  async function post(url, form) {
    const res = await fetch(url, { method: "POST", body: form });
    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error("Respons server tidak valid.");
    }
    if (!res.ok || !data.success) throw new Error(data.error || "Terjadi kesalahan pada server.");
    return data;
  }

  async function doEmbed() {
    showMessage("");
    els.eResult.hidden = true;
    const file = els.eFile.files[0];
    if (!file) return showMessage("Pilih gambar cover terlebih dahulu.");
    if (!els.eText.value.trim()) return showMessage("Pesan rahasia tidak boleh kosong.");

    const form = new FormData();
    form.append("image", file);
    form.append("text", els.eText.value);
    form.append("key", els.eKey.value);

    els.eBtn.disabled = true;
    els.eBtn.textContent = "PROCESSING...";
    try {
      const data = await post("/api/stego/embed", form);
      els.eImg.src = data.image;
      els.eDownload.href = data.image;
      els.eDownload.download = "stego-image.png";
      els.eStats.textContent =
        `${data.width}×${data.height} px · pesan ${formatBytes(data.payload_bytes)} dari kapasitas ${formatBytes(data.capacity_bytes)}` +
        (data.encrypted ? " · dienkripsi Vigenère" : " · tanpa enkripsi");
      els.eCipher.textContent = data.ciphertext;
      els.eResult.hidden = false;
      els.eResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
      if (data.warnings.length) showMessage(data.warnings.join(" "), "warning");
    } catch (err) {
      showMessage(err.message || "Tidak dapat menghubungi server.");
    } finally {
      els.eBtn.disabled = false;
      els.eBtn.textContent = "HIDE MESSAGE";
    }
  }

  async function doExtract() {
    showMessage("");
    els.xResult.hidden = true;
    const file = els.xFile.files[0];
    if (!file) return showMessage("Pilih gambar stego terlebih dahulu.");

    const form = new FormData();
    form.append("image", file);
    form.append("key", els.xKey.value);

    els.xBtn.disabled = true;
    els.xBtn.textContent = "PROCESSING...";
    try {
      const data = await post("/api/stego/extract", form);
      els.xRaw.textContent = data.extracted;
      els.xPlain.textContent = data.plaintext;
      els.xPlainLabel.textContent = data.encrypted ? "Plaintext (setelah dekripsi Vigenère):" : "Pesan:";
      els.xResult.hidden = false;
      els.xResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
      if (data.warnings.length) showMessage(data.warnings.join(" "), "warning");
    } catch (err) {
      showMessage(err.message || "Tidak dapat menghubungi server.");
    } finally {
      els.xBtn.disabled = false;
      els.xBtn.textContent = "EXTRACT MESSAGE";
    }
  }

  els.tabEmbed.addEventListener("click", () => selectTab("embed"));
  els.tabExtract.addEventListener("click", () => selectTab("extract"));
  els.eFile.addEventListener("change", () => showCapacity(els.eFile.files[0]));
  els.eBtn.addEventListener("click", doEmbed);
  els.xBtn.addEventListener("click", doExtract);
})();
