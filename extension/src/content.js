(function () {
  "use strict";

  const BUTTON_CLASS = "ash-password-button";
  const PASSWORD_LENGTH = 20;
  const CHARSETS = {
    lower: "abcdefghijklmnopqrstuvwxyz",
    upper: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    numbers: "0123456789",
    symbols: "!@#$%^&*()-_=+[]{};:,.?/"
  };

  let activeInput = null;
  let button = null;
  let askSequence = 0;
  let pendingAskInput = null;

  function isPasswordInput(element) {
    return element instanceof HTMLInputElement && element.type === "password";
  }

  function createButton() {
    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.className = BUTTON_CLASS;
    nextButton.textContent = "Generer";
    nextButton.setAttribute("aria-label", "Generer un mot de passe");
    nextButton.hidden = true;

    nextButton.addEventListener("mousedown", (event) => {
      event.preventDefault();
    });

    nextButton.addEventListener("click", () => {
      if (!activeInput || !document.contains(activeInput)) {
        hideButton();
        return;
      }

      setInputValue(activeInput, generatePassword(PASSWORD_LENGTH));
      activeInput.focus();
    });

    document.documentElement.appendChild(nextButton);
    return nextButton;
  }

  function getButton() {
    if (!button || !document.contains(button)) {
      button = createButton();
    }

    return button;
  }

  function requestNativeForSite(callback) {
    const cible = window.location.hostname || window.location.origin;

    chrome.runtime.sendMessage({ type: "native_ask", cible }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("Native Messaging error:", chrome.runtime.lastError.message);
        callback(false);
        return;
      }

      callback(Boolean(response && response.ok && response.response && response.response.ok));
    });
  }

  function showButtonFor(input) {
    activeInput = input;
    const currentButton = getButton();

    currentButton.hidden = false;
    currentButton.style.visibility = "hidden";

    const rect = input.getBoundingClientRect();
    const buttonWidth = currentButton.offsetWidth;
    const top = window.scrollY + rect.bottom + 6;
    const viewportRight = window.scrollX + document.documentElement.clientWidth;
    const preferredLeft = window.scrollX + rect.left;
    const maxLeft = viewportRight - buttonWidth - 8;
    const left = Math.max(window.scrollX + 8, Math.min(preferredLeft, maxLeft));

    currentButton.style.top = `${top}px`;
    currentButton.style.left = `${left}px`;
    currentButton.style.visibility = "visible";
  }

  function requestAndShowButtonFor(input) {
    if (pendingAskInput === input) {
      return;
    }

    hideButton();
    pendingAskInput = input;
    showButtonFor(input);

    requestNativeForSite(() => {
      if (pendingAskInput === input) {
        pendingAskInput = null;
      }
    });
  }

  function hideButton() {
    askSequence += 1;
    pendingAskInput = null;

    if (button) {
      button.hidden = true;
    }

    activeInput = null;
  }

  function setInputValue(input, value) {
    const prototype = Object.getPrototypeOf(input);
    const descriptor = Object.getOwnPropertyDescriptor(prototype, "value");

    if (descriptor && typeof descriptor.set === "function") {
      descriptor.set.call(input, value);
    } else {
      input.value = value;
    }

    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function generatePassword(length) {
    const requiredCharacters = Object.values(CHARSETS).map((charset) => randomCharacter(charset));
    const allCharacters = Object.values(CHARSETS).join("");
    const remainingCharacters = Array.from({ length: length - requiredCharacters.length }, () =>
      randomCharacter(allCharacters)
    );

    return shuffle(requiredCharacters.concat(remainingCharacters)).join("");
  }

  function randomCharacter(charset) {
    const bytes = new Uint32Array(1);
    crypto.getRandomValues(bytes);
    return charset[bytes[0] % charset.length];
  }

  function shuffle(characters) {
    const shuffled = characters.slice();

    for (let index = shuffled.length - 1; index > 0; index -= 1) {
      const bytes = new Uint32Array(1);
      crypto.getRandomValues(bytes);
      const swapIndex = bytes[0] % (index + 1);
      const current = shuffled[index];
      shuffled[index] = shuffled[swapIndex];
      shuffled[swapIndex] = current;
    }

    return shuffled;
  }

  document.addEventListener(
    "click",
    (event) => {
      if (isPasswordInput(event.target)) {
        requestAndShowButtonFor(event.target);
        return;
      }

      if (button && event.target === button) {
        return;
      }

      hideButton();
    },
    true
  );

  window.addEventListener("scroll", () => {
    if (activeInput) {
      showButtonFor(activeInput);
    }
  });

  window.addEventListener("resize", () => {
    if (activeInput) {
      showButtonFor(activeInput);
    }
  });
})();
