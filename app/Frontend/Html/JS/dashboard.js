// app/Frontend/Html/JS/dashboard.js

(function () {
  const PASSWORD_LENGTH = 20;
  const CHARSETS = {
    lower: "abcdefghijklmnopqrstuvwxyz",
    upper: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    numbers: "0123456789",
    symbols: "!@#$%^&*()-_=+[]{};:,.?/"
  };

  const state = {
    sites: [],
  };
  let actionsReady = false;
  let modalReady = false;
  let started = false;

  function createSiteId() {
    return `site-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  }

  function normalizeSite(rawSite) {
    if (rawSite && typeof rawSite === 'object' && !Array.isArray(rawSite)) {
      const url =
        rawSite.url ??
        rawSite.domaine ??
        rawSite.site ??
        rawSite.website ??
        rawSite.domain ??
        rawSite.name ??
        '';
      const password =
        rawSite.password ??
        rawSite.secret ??
        rawSite.pass ??
        rawSite.value ??
        '';

      return {
        id: String(rawSite.id || rawSite.url || rawSite.domaine || rawSite.site || createSiteId()),
        url: String(url || ''),
        password: String(password || ''),
        passwordVisible: false,
      };
    }

    return {
      id: createSiteId(),
      url: String(rawSite || ''),
      password: '',
      passwordVisible: false,
    };
  }

  function updateHeader(message) {
    const statusText = document.getElementById('sites-status-text');
    const count = document.getElementById('site-count');

    if (statusText) {
      statusText.textContent = message;
    }

    if (count) {
      count.textContent = String(state.sites.length);
    }
  }

  function setEmptyState(message) {
    const tbody = document.getElementById('sites-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    const row = document.createElement('tr');
    row.className = 'empty-row';

    const cell = document.createElement('td');
    cell.colSpan = 2;
    cell.textContent = message;

    row.appendChild(cell);
    tbody.appendChild(row);
  }

  function getDomainValue(site) {
    return site.url || site.domaine || site.domain || '';
  }

  async function callDashboardApi(method, ...args) {
    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api || typeof api[method] !== 'function') {
      return undefined;
    }

    return typeof callApi === 'function'
      ? await callApi(method, ...args)
      : await api[method](...args);
  }

  async function copyPasswordToClipboard(site) {
    if (!site.password) {
      updateHeader("Aucun mot de passe a copier.");
      return;
    }

    try {
      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        await navigator.clipboard.writeText(site.password);
      } else {
        const input = document.createElement('textarea');
        input.value = site.password;
        input.setAttribute('readonly', '');
        input.style.position = 'fixed';
        input.style.opacity = '0';
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
      }

      updateHeader('Mot de passe copie.');
    } catch (err) {
      console.error('Erreur lors de la copie du mot de passe :', err);
      updateHeader("Impossible de copier le mot de passe.");
    }
  }

  async function togglePasswordVisibility(site, viewButton, copyButton) {
    const domaine = getDomainValue(site);

    if (site.passwordVisible) {
      site.passwordVisible = false;
      viewButton.textContent = 'Voir';
      copyButton.hidden = true;
      return;
    }

    if (!domaine) {
      updateHeader("Domaine invalide.");
      return;
    }

    viewButton.disabled = true;
    viewButton.textContent = 'Chargement...';
    copyButton.hidden = true;

    try {
      const password = await callDashboardApi('get_password_by_domain', domaine);

      if (!password) {
        site.password = '';
        site.passwordVisible = false;
        viewButton.textContent = 'Voir';
        copyButton.hidden = true;
        updateHeader("Aucun mot de passe trouve pour ce domaine.");
        return;
      }

      site.password = String(password);
      site.passwordVisible = true;
      viewButton.textContent = site.password;
      copyButton.hidden = false;
      updateHeader('Mot de passe charge.');
    } catch (err) {
      console.error('Erreur lors de la recuperation du mot de passe :', err);
      site.passwordVisible = false;
      viewButton.textContent = 'Voir';
      copyButton.hidden = true;
      updateHeader("Impossible de recuperer le mot de passe.");
    } finally {
      viewButton.disabled = false;
    }
  }

  async function regeneratePassword(site, button) {
    const domaine = getDomainValue(site);

    if (!domaine) {
      updateHeader("Domaine invalide.");
      return;
    }

    const password = generatePassword(PASSWORD_LENGTH);
    const confirmed = window.confirm(
      `Nouveau mot de passe genere pour ${domaine} :\n\n${password}\n\nConfirmer le remplacement ?`
    );

    if (!confirmed) {
      return;
    }

    button.disabled = true;
    button.textContent = 'Generation...';

    try {
      const result = await callDashboardApi('modifie_target_password', domaine, password);

      if (!result) {
        updateHeader("Le mot de passe n'a pas pu etre remplace.");
        return;
      }

      site.password = password;
      site.passwordVisible = false;
      updateHeader('Mot de passe regenere et enregistre.');
      renderSites();
    } catch (err) {
      console.error('Erreur lors de la regeneration du mot de passe :', err);
      updateHeader("Impossible de regenerer le mot de passe.");
    } finally {
      button.disabled = false;
      button.textContent = 'Regenerer';
    }
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

  function createSiteRow(site) {
    const row = document.createElement('tr');
    row.dataset.siteId = site.id;

    const urlCell = document.createElement('td');
    const domainText = document.createElement('span');
    domainText.className = 'domain-value';
    domainText.textContent = getDomainValue(site);
    urlCell.appendChild(domainText);

    const actionCell = document.createElement('td');
    const actionGroup = document.createElement('div');
    actionGroup.className = 'password-actions';

    const viewButton = document.createElement('button');
    viewButton.type = 'button';
    viewButton.className = 'btn btn-ghost password-action password-view-action';
    viewButton.textContent = site.passwordVisible && site.password ? site.password : 'Voir';

    const copyButton = document.createElement('button');
    copyButton.type = 'button';
    copyButton.className = 'btn btn-ghost password-copy-action';
    copyButton.textContent = 'Copy';
    copyButton.hidden = !(site.passwordVisible && site.password);
    copyButton.addEventListener('click', () => {
      copyPasswordToClipboard(site);
    });

    viewButton.addEventListener('click', () => {
      togglePasswordVisibility(site, viewButton, copyButton);
    });

    const regenerateButton = document.createElement('button');
    regenerateButton.type = 'button';
    regenerateButton.className = 'btn btn-primary password-action';
    regenerateButton.textContent = 'Regenerer';
    regenerateButton.addEventListener('click', () => {
      regeneratePassword(site, regenerateButton);
    });

    actionGroup.appendChild(viewButton);
    actionGroup.appendChild(copyButton);
    actionGroup.appendChild(regenerateButton);
    actionCell.appendChild(actionGroup);

    row.appendChild(urlCell);
    row.appendChild(actionCell);

    return row;
  }

  function renderSites() {
    const tbody = document.getElementById('sites-table-body');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (state.sites.length === 0) {
      setEmptyState('Aucun site enregistre pour le moment.');
      return;
    }

    state.sites.forEach((site) => {
      tbody.appendChild(createSiteRow(site));
    });
  }

  async function loadSites() {
    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api) {
      updateHeader("Connexion a l'API en cours...");
      setTimeout(loadSites, 200);
      return;
    }

    if (typeof api.get_pswtable_data !== 'function') {
      state.sites = [];
      updateHeader("L'API de lecture est indisponible.");
      renderSites();
      return;
    }

    try {
      const result =
        typeof callApi === 'function'
          ? await callApi('get_pswtable_data')
          : await api.get_pswtable_data();

      state.sites = Array.isArray(result) ? result.map(normalizeSite) : [];

      if (state.sites.length === 0) {
        updateHeader("Aucun site enregistre pour le moment.");
      } else {
        updateHeader('Les donnees sont chargees et pretes a etre consultees.');
      }

      renderSites();
    } catch (err) {
      console.error('Erreur lors du chargement des sites :', err);
      state.sites = [];
      updateHeader("Impossible de charger les sites pour l'instant.");
      renderSites();
    }
  }

  function openAddModal() {
    const backdrop = document.getElementById('site-modal-backdrop');
    const errorBox = document.getElementById('site-form-error');
    const urlInput = document.getElementById('site-url-input');
    const passwordInput = document.getElementById('site-password-input');

    if (!backdrop) return;

    if (errorBox) {
      errorBox.textContent = '';
      errorBox.style.display = 'none';
    }

    if (urlInput) urlInput.value = '';
    if (passwordInput) passwordInput.value = '';

    backdrop.hidden = false;
    backdrop.setAttribute('aria-hidden', 'false');

    if (urlInput) {
      urlInput.focus();
    }
  }

  function closeAddModal() {
    const backdrop = document.getElementById('site-modal-backdrop');
    if (!backdrop) return;

    backdrop.hidden = true;
    backdrop.setAttribute('aria-hidden', 'true');
  }

  async function handleAddSite(event) {
    event.preventDefault();

    const api = typeof getApi === 'function' ? getApi() : null;
    const urlInput = document.getElementById('site-url-input');
    const passwordInput = document.getElementById('site-password-input');
    const errorBox = document.getElementById('site-form-error');
    const submitButton = event.submitter;

    const url = urlInput ? urlInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value.trim() : '';

    function showError(message) {
      if (errorBox) {
        errorBox.textContent = message;
        errorBox.style.display = 'block';
      }
    }

    if (!url || !password) {
      showError('Veuillez renseigner une URL et un mot de passe.');
      return false;
    }

    if (!api || typeof api.update_password_data !== 'function') {
      showError("L'API d'enregistrement est indisponible.");
      return false;
    }

    if (errorBox) {
      errorBox.textContent = '';
      errorBox.style.display = 'none';
    }

    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      const payload = {
        sites: [
          {
            domaine: url,
            password,
          },
        ],
      };
      const result =
        typeof callApi === 'function'
          ? await callApi('update_password_data', payload)
          : await api.update_password_data(payload);

      if (!Array.isArray(result)) {
        showError("Le site n'a pas pu etre enregistre.");
        return false;
      }

      state.sites = result.map(normalizeSite);
      updateHeader('Site enregistre dans le fichier.');
      renderSites();
      closeAddModal();
    } catch (err) {
      console.error("Erreur lors de l'enregistrement du site :", err);
      showError("Impossible d'enregistrer le site pour l'instant.");
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }

    return false;
  }

  function setupModal() {
    if (modalReady) {
      return;
    }

    const backdrop = document.getElementById('site-modal-backdrop');
    const form = document.getElementById('site-form');
    const closeButtons = document.querySelectorAll('[data-close-site-modal]');

    if (form) {
      form.addEventListener('submit', handleAddSite);
    }

    closeButtons.forEach((button) => {
      button.addEventListener('click', closeAddModal);
    });

    if (backdrop) {
      backdrop.addEventListener('click', (event) => {
        if (event.target === backdrop) {
          closeAddModal();
        }
      });
    }

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        closeAddModal();
      }
    });

    modalReady = true;
  }

  function setupActions() {
    if (actionsReady) {
      return;
    }

    const settingsButton = document.getElementById('settings-button');
    const addSiteButton = document.getElementById('add-site-button');

    if (settingsButton) {
      settingsButton.addEventListener('click', () => {
        if (typeof goToPage === 'function') {
          goToPage('Settings.html');
        } else {
          window.location.href = 'Settings.html';
        }
      });
    }

    if (addSiteButton) {
      addSiteButton.addEventListener('click', openAddModal);
    }

    actionsReady = true;
  }

  function start() {
    if (started) {
      return;
    }

    started = true;
    setupActions();
    setupModal();
    loadSites();
  }

  window.addEventListener('pywebviewready', start);

  document.addEventListener('DOMContentLoaded', () => {
    const api = typeof getApi === 'function' ? getApi() : null;
    if (api) {
      start();
      return;
    }

    setupActions();
    setupModal();
    updateHeader("Interface prete. En attente de l'API locale.");
    renderSites();
  });
})();
