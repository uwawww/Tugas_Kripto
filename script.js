(() => {
  "use strict";

  const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const $ = (id) => document.getElementById(id);

  const els = {
    text: $("text"),
    key: $("key"),
    encrypt: $("btn-encrypt"),
    decrypt: $("btn-decrypt"),
    clear: $("btn-clear"),
    copy: $("btn-copy"),
    message: $("message"),
    resultCard: $("result-card"),
    resultLabel: $("result-label"),
    result: $("result"),
    effectiveKey: $("effective-key"),
    processCard: $("process-card"),
    processBody: $("process-body"),
    table: $("vigenere-table"),
  };

  /* ---------- UI helpers ---------- */

  function showMessage(text, type = "error") {
    els.message.textContent = text;
    els.message.className = `message ${type}`;
    els.message.hidden = !text;
  }

  function hideResults() {
    els.resultCard.hidden = true;
    els.processCard.hidden = true;
    els.processBody.textContent = "";
    els.result.textContent = "";
    els.effectiveKey.textContent = "";
  }

  function setLoading(isLoading, mode) {
    [els.encrypt, els.decrypt, els.clear].forEach((b) => (b.disabled = isLoading));
    els.encrypt.textContent = isLoading && mode === "encrypt" ? "PROCESSING..." : "ENCRYPT";
    els.decrypt.textContent = isLoading && mode === "decrypt" ? "PROCESSING..." : "DECRYPT";
  }

  function cell(tag, text, className) {
    const el = document.createElement(tag);
    el.textContent = text;
    if (className) el.className = className;
    return el;
  }

  /* ---------- Render hasil ---------- */

  function operationText(step) {
    let text = `${step.operation} = ${step.raw_value} % 26 = ${step.output_value}`;
    if (step.raw_value < 0) {
      text += `  (${step.raw_value} + 26 = ${step.output_value})`;
    }
    return text;
  }

  function render(data) {
    els.resultLabel.textContent = data.mode === "encrypt" ? "Ciphertext:" : "Plaintext:";
    els.result.textContent = data.result;
    els.effectiveKey.textContent = data.effective_key;

    els.processBody.textContent = "";
    const frag = document.createDocumentFragment();
    data.process.forEach((s) => {
      const tr = document.createElement("tr");
      tr.appendChild(cell("td", s.position));
      tr.appendChild(cell("td", s.input));
      tr.appendChild(cell("td", s.key));
      tr.appendChild(cell("td", s.input_value));
      tr.appendChild(cell("td", s.key_value));
      tr.appendChild(cell("td", operationText(s), "op"));
      tr.appendChild(cell("td", s.output, "out"));
      frag.appendChild(tr);
    });
    els.processBody.appendChild(frag);

    els.resultCard.hidden = false;
    els.processCard.hidden = data.process.length === 0;
    els.resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  /* ---------- Panggil API ---------- */

  async function run(mode) {
    showMessage("");
    const text = els.text.value;
    const key = els.key.value;

    if (!text.trim()) return showMessage("Plaintext / ciphertext tidak boleh kosong.");
    if (!key.trim()) return showMessage("Key tidak boleh kosong.");

    setLoading(true, mode);
    try {
      const res = await fetch(`/api/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, key }),
      });

      let data;
      try {
        data = await res.json();
      } catch {
        throw new Error("Respons server tidak valid.");
      }
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Terjadi kesalahan pada server.");
      }

      render(data);
      if (data.warnings && data.warnings.length) {
        showMessage(data.warnings.join(" "), "warning");
      }
    } catch (err) {
      hideResults();
      showMessage(err.message || "Tidak dapat menghubungi server.");
    } finally {
      setLoading(false);
    }
  }

  /* ---------- Copy & Clear ---------- */

  async function copyResult() {
    const text = els.result.textContent;
    if (!text) return;

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(ta);
        if (!ok) throw new Error("copy failed");
      }
      els.copy.textContent = "COPIED ✓";
      els.copy.classList.add("copied");
    } catch {
      showMessage("Gagal menyalin. Salin hasil secara manual.");
      return;
    }
    setTimeout(() => {
      els.copy.textContent = "COPY RESULT";
      els.copy.classList.remove("copied");
    }, 1500);
  }

  function clearAll() {
    els.text.value = "";
    els.key.value = "";
    showMessage("");
    hideResults();
    els.text.focus();
  }

  /* ---------- Tabel Vigenère 26x26 (dinamis) ---------- */

  function buildVigenereTable() {
    const table = els.table;
    const thead = table.createTHead();
    const headRow = thead.insertRow();
    headRow.appendChild(cell("th", ""));
    for (const letter of ALPHABET) headRow.appendChild(cell("th", letter));

    const tbody = table.createTBody();
    for (let r = 0; r < 26; r++) {
      const row = tbody.insertRow();
      row.appendChild(cell("th", ALPHABET[r]));
      for (let c = 0; c < 26; c++) {
        row.appendChild(cell("td", ALPHABET[(r + c) % 26]));
      }
    }

    // Sorot baris & kolom saat hover
    const clearHighlight = () =>
      table.querySelectorAll(".hl, .hl-main").forEach((el) => el.classList.remove("hl", "hl-main"));

    table.addEventListener("mouseover", (e) => {
      const td = e.target.closest("td");
      if (!td) return;
      clearHighlight();
      const colIndex = td.cellIndex;
      const rowIndex = td.parentElement.rowIndex;
      for (let j = 1; j <= colIndex; j++) table.rows[rowIndex].cells[j].classList.add("hl");
      for (let i = 1; i <= rowIndex; i++) table.rows[i].cells[colIndex].classList.add("hl");
      td.classList.remove("hl");
      td.classList.add("hl-main");
    });
    table.addEventListener("mouseleave", clearHighlight);
  }

  /* ---------- Event listener ---------- */

  els.encrypt.addEventListener("click", () => run("encrypt"));
  els.decrypt.addEventListener("click", () => run("decrypt"));
  els.clear.addEventListener("click", clearAll);
  els.copy.addEventListener("click", copyResult);

  buildVigenereTable();
})();