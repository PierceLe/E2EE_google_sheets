(function () {
  try {
    const script = document.createElement("script");
    script.src = chrome.runtime.getURL("inject.js");
    script.type = "module";
    (document.head || document.documentElement).appendChild(script);
    script.onload = () => {
      script.remove();
      console.log("[sheets-encrypt-poc] inject.js loaded");
    };
  } catch (err) {
    console.error("[sheets-encrypt-poc] inject error", err);
  }
})();