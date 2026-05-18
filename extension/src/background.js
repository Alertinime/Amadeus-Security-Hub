"use strict";

const NATIVE_HOST_NAME = "com.amadeus.security_hub";
const MESSAGE_TYPES = {
  native_ask: "Ask",
  native_add: "AddEntry"
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !MESSAGE_TYPES[message.type]) {
    return false;
  }

  const nativeMessage = {
    type: MESSAGE_TYPES[message.type],
    domaine: message.domaine,
    cible: message.domaine,
    source: "extension",
    tabId: sender.tab ? sender.tab.id : null
  };

  if (typeof message.password === "string") {
    nativeMessage.password = message.password;
  }

  chrome.runtime.sendNativeMessage(
    NATIVE_HOST_NAME,
    nativeMessage,
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
