// app/Frontend/Html/JS/dashboard.js

(function () {
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
      };
    }

    return {
      id: createSiteId(),
      url: String(rawSite || ''),
      password: '',
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
    cell.colSpan = 3;
    cell.textContent = message;

    row.appendChild(cell);
    tbody.appendChild(row);
  }

  function syncRowMode(row, urlInput, passwordInput, button, isEditing) {
    row.classList.toggle('is-editing', isEditing);
    urlInput.readOnly = !isEditing;
    passwordInput.readOnly = !isEditing;
    button.textContent = isEditing ? 'Valider' : 'Modifier';
  }

  function createSiteRow(site) {
    const row = document.createElement('tr');
    row.dataset.siteId = site.id;

    const urlCell = document.createElement('td');
    const urlInput = document.createElement('input');
    urlInput.type = 'text';
    urlInput.className = 'site-field';
    urlInput.value = site.url;
    urlInput.readOnly = true;
    urlInput.setAttribute('aria-label', 'URL du site');
    urlInput.addEventListener('input', () => {
      site.url = urlInput.value;
    });
    urlCell.appendChild(urlInput);

    const passwordCell = document.createElement('td');
    const passwordInput = document.createElement('input');
    passwordInput.type = 'text';
    passwordInput.className = 'site-field site-password';
    passwordInput.value = site.password;
    passwordInput.readOnly = true;
    passwordInput.setAttribute('aria-label', 'Mot de passe associe');
    passwordInput.addEventListener('input', () => {
      site.password = passwordInput.value;
    });
    passwordCell.appendChild(passwordInput);

    const actionCell = document.createElement('td');
    const actionButton = document.createElement('button');
    actionButton.type = 'button';
    actionButton.className = 'btn btn-ghost row-action';
    actionButton.addEventListener('click', () => {
      const nextMode = actionButton.textContent !== 'Valider';
      syncRowMode(row, urlInput, passwordInput, actionButton, nextMode);

      if (nextMode) {
        urlInput.focus();
        urlInput.select();
      }
    });
    syncRowMode(row, urlInput, passwordInput, actionButton, false);
    actionCell.appendChild(actionButton);

    row.appendChild(urlCell);
    row.appendChild(passwordCell);
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
