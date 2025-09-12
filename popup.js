document.getElementById("enable").addEventListener("click", () => {
  chrome.storage.local.set({ sheets_encrypt_enabled: true }, () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      tabs.forEach(tab => {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => localStorage.setItem('sheets_encrypt_enabled', '1')
        });
      });
    });
    window.close();
  });
});
document.getElementById("disable").addEventListener("click", () => {
  chrome.storage.local.set({ sheets_encrypt_enabled: false }, () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      tabs.forEach(tab => {
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => localStorage.setItem('sheets_encrypt_enabled', '0')
        });
      });
    });
    window.close();
  });
});
