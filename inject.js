(function () {
  const PREFIX = "ENC:";
  const ENABLE_KEY = "sheets_encrypt_enabled"; // lưu flag bật/tắt vào localStorage

  function encodePlaintext(str) {
    try {
      return PREFIX + btoa(unescape(encodeURIComponent(str))); // support unicode
    } catch (e) {
      console.error("encode error", e);
      return PREFIX + btoa(str);
    }
  }
  function decodeCipher(str) {
    try {
      const payload = str.slice(PREFIX.length);
      return decodeURIComponent(escape(atob(payload)));
    } catch (e) {
      console.error("decode error", e);
      return "[DECODE_ERROR]";
    }
  }

  function isSheetsPage() {
    return location.hostname === "docs.google.com" && location.pathname.startsWith("/spreadsheets");
  }

  function isEditorElement(el) {
    if (!el) return false;
    return el.isContentEditable || el.tagName === "TEXTAREA" || el.tagName === "INPUT";
  }

  function isEnabled() {
    try {
      const v = window.localStorage.getItem(ENABLE_KEY);
      return v === "1";
    } catch (e) {
      return true;
    }
  }

  window.SHEETS_ENCRYPT_POC = {
    enable() { window.localStorage.setItem(ENABLE_KEY, "1"); console.log("encrypt enabled"); },
    disable() { window.localStorage.setItem(ENABLE_KEY, "0"); console.log("encrypt disabled"); },
    decode: (s) => decodeCipher(s)
  };

  if (!isSheetsPage()) return;

  document.addEventListener(
    "keydown",
    function (e) {
      console.log(isEnabled)
      console.log(isEditorElement)
      if (!isEnabled()) return;
      if (e.key !== "Enter") return;
      const el = document.activeElement;
      if (!isEditorElement(el)) return;

      const raw = el.innerText ?? el.value ?? "";
      if (!raw) return;
      if (raw.startsWith(PREFIX)) return; // already encoded

      const enc = encodePlaintext(raw);

      if (el.isContentEditable) {
        el.innerText = enc;
      } else {
        el.value = enc;
      }

      el.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
      el.dispatchEvent(new Event("change", { bubbles: true, cancelable: true }));
    },
    true
  );

  document.addEventListener(
    "blur",
    function (e) {
      if (!isEnabled()) return;
      const el = e.target;
      if (!isEditorElement(el)) return;

      const raw = el.innerText ?? el.value ?? "";
      if (!raw) return;
      if (raw.startsWith(PREFIX)) return;

      const enc = encodePlaintext(raw);
      if (el.isContentEditable) el.innerText = enc;
      else el.value = enc;

      el.dispatchEvent(new Event("input", { bubbles: true, cancelable: true }));
      el.dispatchEvent(new Event("change", { bubbles: true, cancelable: true }));
    },
    true
  );

  const observer = new MutationObserver((mutations) => {
    if (!isEnabled()) return;
    for (const m of mutations) {
      const node = m.target;
      try {
        // if node contains text starting with ENC:, set a title attribute with decoded text (preview)
        const txt = node.innerText || node.textContent || "";
        if (typeof txt === "string" && txt.startsWith(PREFIX)) {
          const decoded = decodeCipher(txt);
          // add data-attr for debugging; do not modify cell content
          node.setAttribute("data-enc-preview", decoded);
          node.title = `DECRYPTED PREVIEW: ${decoded}`; // user can hover to see
        }
      } catch (e) { /* ignore */ }
    }
  });

  observer.observe(document.body, { subtree: true, characterData: false, childList: true, attributes: false });

  console.log("[sheets-encrypt-poc] injected, encrypt-on-enter/blur active (base64 demo)");
})();