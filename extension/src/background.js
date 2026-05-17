"use strict";

const NATIVE_HOST_NAME = "com.amadeus.security_hub";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "native_ask") {
    return false;
  }

  chrome.runtime.sendNativeMessage(
    NATIVE_HOST_NAME,
    {
      type: "Ask",
      cible: message.cible,
      source: "extension",
      tabId: sender.tab ? sender.tab.id : null
    },
    (response) => {
      if (chrome.runtime.lastError) {
        sendResponse({
          ok: false,
          error: chrome.runtime.lastError.message
        });
        return;
      }

      sendResponse({
        ok: true,
        response
      });
    }
  );

  return true;
});
