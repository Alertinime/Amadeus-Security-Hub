// app/Frontend/Html/JS/create_key.js

(function () {
  let selectedDevice = null;

  // Regex de mot de passe :
  // - >= 12 caractères
  // - au moins 1 minuscule
  // - au moins 1 majuscule
  // - au moins 1 chiffre
  // - au moins 1 symbole (non alphanumérique)
  const PASSWORD_REGEX =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])(?=.{12,}).*$/;

  function normalizeUsbDevice(rawDevice) {
    if (rawDevice && typeof rawDevice === 'object' && !Array.isArray(rawDevice)) {
      const deviceId = String(rawDevice.id || rawDevice.name || '');
      const deviceName = String(rawDevice.name || rawDevice.id || '');
      return { id: deviceId, name: deviceName };
    }

    const value = String(rawDevice);
    return { id: value, name: value };
  }

  function openPasswordModal(deviceName, deviceId) {
    selectedDevice = deviceId || deviceName;

    const modal = document.querySelector('.password-modal-backdrop');
    if (!modal) return;

    const deviceLabel = modal.querySelector('.password-device-label');
    if (deviceLabel) {
      deviceLabel.textContent = deviceName;
    }

    const pwdInput = modal.querySelector('#usb-master-password');
    const confirmInput = modal.querySelector('#usb-master-password-confirm');
    const errorBox = modal.querySelector('#usb-password-error');

    if (pwdInput) pwdInput.value = '';
    if (confirmInput) confirmInput.value = '';
    if (errorBox) {
      errorBox.textContent = '';
      errorBox.style.display = 'none';
    }

    modal.hidden = false;
    modal.setAttribute('aria-hidden', 'false');

    if (pwdInput) {
      pwdInput.focus();
    }
  }

  function closePasswordModal() {
    const modal = document.querySelector('.password-modal-backdrop');
    if (!modal) return;

    modal.hidden = true;
    modal.setAttribute('aria-hidden', 'true');
    selectedDevice = null;
  }

  function validatePassword(password, confirmPassword) {
    const errors = [];

    if (!PASSWORD_REGEX.test(password)) {
      errors.push(
        'Le mot de passe doit contenir au moins 12 caractères, avec au moins une minuscule, ' +
          'une majuscule, un chiffre et un symbole.'
      );
    }

    if (password !== confirmPassword) {
      errors.push('Les deux mots de passe ne correspondent pas.');
    }

    return errors;
  }

  async function handlePasswordSubmit(event) {
    event.preventDefault();

    const modal = document.querySelector('.password-modal-backdrop');
    if (!modal) return false;

    const pwdInput = modal.querySelector('#usb-master-password');
    const confirmInput = modal.querySelector('#usb-master-password-confirm');
    const errorBox = modal.querySelector('#usb-password-error');

    const password = pwdInput ? pwdInput.value || '' : '';
    const confirmPassword = confirmInput ? confirmInput.value || '' : '';

    const errors = validatePassword(password, confirmPassword);

    if (errorBox) {
      if (errors.length > 0) {
        errorBox.textContent = errors.join(' ');
        errorBox.style.display = 'block';
      } else {
        errorBox.textContent = '';
        errorBox.style.display = 'none';
      }
    }

    if (errors.length > 0) {
      if (pwdInput) {
        pwdInput.focus();
      }
      return false;
    }

    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api || !selectedDevice) {
      console.warn('API pywebview ou périphérique non disponible.');
      return false;
    }

    try {
      if (typeof api.init_usb === 'function') {
        if (typeof callApi === 'function') {
          await callApi('init_usb', selectedDevice, password);
        } else {
          await api.init_usb(selectedDevice, password);
        }
      } else {
        console.warn(
          'Aucune méthode init_usb_with_password ou init_usb trouvée sur l’API.'
        );
      }
    } catch (err) {
      console.error('Erreur lors de l’initialisation de la clé :', err);
      if (errorBox) {
        errorBox.textContent =
          'Erreur lors de l’initialisation de la clé. Veuillez réessayer.';
        errorBox.style.display = 'block';
      }
      return false;
    }

    closePasswordModal();
    return false;
  }

  function setupPasswordModal() {
    const modal = document.querySelector('.password-modal-backdrop');
    if (!modal) return;

    const form = modal.querySelector('#usb-password-form');
    if (form) {
      form.addEventListener('submit', handlePasswordSubmit);
    }

    const cancelBtn = modal.querySelector('[data-modal-cancel]');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', (e) => {
        e.preventDefault();
        closePasswordModal();
      });
    }

    // Click sur le backdrop pour fermer
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closePasswordModal();
      }
    });

    // ESC pour fermer
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closePasswordModal();
      }
    });
  }

  function createUsbButton(rawDevice) {
    const device = normalizeUsbDevice(rawDevice);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'menu-item';

    const spanOuter = document.createElement('span');

    const label = document.createElement('span');
    label.className = 'label';
    label.textContent = device.name;

    const meta = document.createElement('span');
    meta.className = 'meta';
    meta.textContent = 'Support USB détecté';

    spanOuter.appendChild(label);
    spanOuter.appendChild(meta);

    const chevron = document.createElement('span');
    chevron.className = 'chevron';
    chevron.textContent = '➝';

    button.appendChild(spanOuter);
    button.appendChild(chevron);

    // Au clic : ouverture de la popup mot de passe
    button.addEventListener('click', () =>
      openPasswordModal(device.name, device.id)
    );

    return button;
  }

  async function loadUsbList() {
    const menuList = document.querySelector('.menu-list');
    if (!menuList) return;

    menuList.innerHTML = '';

    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api) {
      // Bridge pas encore prêt : on retente plus tard
      setTimeout(loadUsbList, 200);
      return;
    }

    if (typeof api.usb_list !== 'function') {
      const msg = document.createElement('div');
      msg.className = 'no-usb';
      msg.textContent = 'API USB indisponible.';
      menuList.appendChild(msg);
      console.warn('api.usb_list non trouvée sur l’API pywebview.');
      return;
    }

    try {
      const list =
        typeof callApi === 'function'
          ? await callApi('usb_list')
          : await api.usb_list();

      if (!Array.isArray(list) || list.length === 0) {
        const msg = document.createElement('div');
        msg.className = 'no-usb';
        msg.textContent = 'Aucun support USB détecté.';
        menuList.appendChild(msg);
        return;
      }

      list.forEach((rawDevice) => {
        const btn = createUsbButton(rawDevice);
        menuList.appendChild(btn);
      });
    } catch (err) {
      console.error('Erreur lors de usb_list :', err);
      const msg = document.createElement('div');
      msg.className = 'no-usb';
      msg.textContent = 'Erreur lors de la détection des supports USB.';
      menuList.appendChild(msg);
    }
  }

  function setupBackButton() {
    const backBtn = document.querySelector('.btn-back');
    if (!backBtn) return;

    backBtn.addEventListener('click', async () => {
      const api = typeof getApi === 'function' ? getApi() : null;
      if (!api) {
        console.warn('API pywebview indisponible pour le retour.');
        return;
      }

      try {
        if (typeof api.reload_usb_check === 'function') {
          if (typeof callApi === 'function') {
            await callApi('reload_usb_check');
          } else {
            await api.reload_usb_check();
          }
        } else if (typeof api.go_back === 'function') {
          if (typeof callApi === 'function') {
            await callApi('go_back');
          } else {
            await api.go_back();
          }
        } else {
          console.warn(
            'Aucune méthode de retour trouvée (reload_usb_check / go_back).'
          );
        }
      } catch (err) {
        console.error('Erreur lors du retour :', err);
      }
    });
  }

  function start() {
    setupBackButton();
    setupPasswordModal();
    loadUsbList();
  }

  // pywebview signale que le bridge est prêt
  window.addEventListener('pywebviewready', start);

  // Fallback : si on est en mode navigateur / bridge déjà prêt
  document.addEventListener('DOMContentLoaded', () => {
    const api = typeof getApi === 'function' ? getApi() : null;
    if (api) {
      start();
    }
  });
})();
