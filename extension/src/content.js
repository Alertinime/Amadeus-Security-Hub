(function () {
  "use strict";

  const PANEL_CLASS = "ash-password-panel";
  const BUTTON_CLASS = "ash-password-button";
  const PASSWORD_LENGTH = 20;
  const CHARSETS = {
    lower: "abcdefghijklmnopqrstuvwxyz",
    upper: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    numbers: "0123456789",
    symbols: "!@#$%^&*()-_=+[]{};:,.?/"
  };

  let activeInput = null;
  let panel = null;
  let generateButton = null;
  let fillButton = null;
  let confirmButton = null;
  let askSequence = 0;
  let pendingAskInput = null;
  let storedPassword = null;
  let generatedPassword = null;

  function isPasswordInput(element) {
    return element instanceof HTMLInputElement && element.type === "password";
  }

  function isConnected(element) {
    return Boolean(element && element.isConnected);
  }

  function findPasswordInputFromEvent(event) {
    const path = typeof event.composedPath === "function" ? event.composedPath() : [];
    const inputFromPath = path.find(isPasswordInput);

    if (inputFromPath) {
      return inputFromPath;
    }

    return isPasswordInput(event.target) ? event.target : null;
  }

  function createPanelButton(label, ariaLabel) {
    const nextButton = document.createElement("button");
    nextButton.type = "button";
    nextButton.className = BUTTON_CLASS;
    nextButton.textContent = label;
    nextButton.setAttribute("aria-label", ariaLabel);

    return nextButton;
  }

  function createPanel() {
    const nextPanel = document.createElement("div");
    nextPanel.className = PANEL_CLASS;
    nextPanel.hidden = true;

    nextPanel.addEventListener("mousedown", (event) => {
      event.preventDefault();
    });

    generateButton = createPanelButton("Generer", "Generer un mot de passe");
    generateButton.addEventListener("click", () => {
      if (!activeInput || !isConnected(activeInput)) {
        hidePanel();
        return;
      }

      generatedPassword = generatePassword(PASSWORD_LENGTH);
      setInputValue(activeInput, generatedPassword);
      activeInput.focus();
      showPanelFor(activeInput);

      const shouldSave = window.confirm("Enregistrer ce mot de passe dans Amadeus Security Hub ?");

      if (!shouldSave) {
        return;
      }

      savePasswordForSite(generatedPassword, (ok) => {
        if (!ok) {
          console.warn("Amadeus Security Hub: impossible d'enregistrer le mot de passe.");
        }
      });
    });

    fillButton = createPanelButton("Remplir", "Remplir le mot de passe enregistre");
    fillButton.hidden = true;
    fillButton.addEventListener("click", () => {
      if (!activeInput || !isConnected(activeInput) || !storedPassword) {
        hidePanel();
        return;
      }

      setInputValue(activeInput, storedPassword);
      activeInput.focus();
    });

    confirmButton = createPanelButton("Confirmer", "Remplir avec le dernier mot de passe genere");
    confirmButton.hidden = true;
    confirmButton.addEventListener("click", () => {
      if (!activeInput || !isConnected(activeInput) || !generatedPassword) {
        hidePanel();
        return;
      }

      setInputValue(activeInput, generatedPassword);
      activeInput.focus();
    });

    nextPanel.appendChild(generateButton);
    nextPanel.appendChild(fillButton);
    nextPanel.appendChild(confirmButton);
    document.documentElement.appendChild(nextPanel);
    return nextPanel;
  }

  function getPanel() {
    if (!panel || !document.contains(panel)) {
      panel = createPanel();
    }

    return panel;
  }

  function getCurrentDomain() {
    return window.location.hostname || window.location.origin;
  }

  function requestPasswordForSite(callback) {
    const domaine = getCurrentDomain();

    chrome.runtime.sendMessage({ type: "native_ask", domaine }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("Native Messaging error:", chrome.runtime.lastError.message);
        callback(null);
        return;
      }

      if (!response || !response.ok || !response.response || response.response.ok === false) {
        callback(null);
        return;
      }

      callback(response.response.value || null);
    });
  }

  function savePasswordForSite(password, callback) {
    const domaine = getCurrentDomain();

    chrome.runtime.sendMessage({ type: "native_add", domaine, password }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("Native Messaging error:", chrome.runtime.lastError.message);
        callback(false);
        return;
      }

      callback(Boolean(response && response.ok && response.response && response.response.ok !== false));
    });
  }

  function showPanelFor(input) {
    activeInput = input;
    const currentPanel = getPanel();

    const hasVisibleAction = updatePanelButtons();
    if (!hasVisibleAction) {
      currentPanel.hidden = true;
      return;
    }

    currentPanel.hidden = false;
    currentPanel.style.visibility = "hidden";

    const rect = input.getBoundingClientRect();
    const panelWidth = currentPanel.offsetWidth;
    const top = window.scrollY + rect.bottom + 6;
    const viewportRight = window.scrollX + document.documentElement.clientWidth;
    const preferredLeft = window.scrollX + rect.left;
    const maxLeft = viewportRight - panelWidth - 8;
    const left = Math.max(window.scrollX + 8, Math.min(preferredLeft, maxLeft));

    currentPanel.style.top = `${top}px`;
    currentPanel.style.left = `${left}px`;
    currentPanel.style.visibility = "visible";
  }

  function updatePanelButtons() {
    if (generateButton) {
      generateButton.hidden = false;
    }

    if (fillButton) {
      fillButton.hidden = !storedPassword;
    }

    if (confirmButton) {
      confirmButton.hidden = !generatedPassword;
    }

    return Boolean(
      (generateButton && !generateButton.hidden) ||
        (fillButton && !fillButton.hidden) ||
        (confirmButton && !confirmButton.hidden)
    );
  }

  function requestAndShowPanelFor(input) {
    if (pendingAskInput === input) {
      return;
    }

    hidePanel();
    pendingAskInput = input;
    const currentAskSequence = askSequence;
    showPanelFor(input);

    requestPasswordForSite((password) => {
      if (pendingAskInput === input && currentAskSequence === askSequence) {
        pendingAskInput = null;
        storedPassword = password || null;

        if (isConnected(input)) {
          showPanelFor(input);
        }
      }
    });
  }

  function hidePanel() {
    askSequence += 1;
    pendingAskInput = null;
    storedPassword = null;

    if (panel) {
      panel.hidden = true;
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
      const passwordInput = findPasswordInputFromEvent(event);

      if (passwordInput) {
        requestAndShowPanelFor(passwordInput);
        return;
      }

      if (panel && panel.contains(event.target)) {
        return;
      }

      hidePanel();
    },
    true
  );

  document.addEventListener(
    "focusin",
    (event) => {
      const passwordInput = findPasswordInputFromEvent(event);

      if (passwordInput) {
        requestAndShowPanelFor(passwordInput);
      }
    },
    true
  );

  window.addEventListener("scroll", () => {
    if (activeInput) {
      showPanelFor(activeInput);
    }
  });

  window.addEventListener("resize", () => {
    if (activeInput) {
      showPanelFor(activeInput);
    }
  });
})();
