// app/Frontend/Html/JS/login.js

(function () {
  async function envoyerMdp(event) {
    event.preventDefault();

    const input = document.getElementById('master-password');
    const errorBox = document.getElementById('login-error');
    const submitButton = document.querySelector('.form-block button[type="submit"]');

    if (!input) {
      console.warn('Champ #master-password introuvable.');
      return false;
    }

    if (errorBox) {
      errorBox.textContent = '';
      errorBox.style.display = 'none';
    }

    const value = input.value || '';
    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api || typeof api.login !== 'function') {
      console.warn('API login indisponible.');
      if (errorBox) {
        errorBox.textContent =
          "Impossible d'etablir la connexion avec l'application.";
        errorBox.style.display = 'block';
      }
      return false;
    }

    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      const isAuthenticated =
        typeof callApi === 'function'
          ? await callApi('login', value)
          : await api.login(value);

      if (isAuthenticated === true) {
        if (typeof goToPage === 'function') {
          goToPage('Dashboard.html');
        } else {
          window.location.href = 'Dashboard.html';
        }
        return false;
      }

      if (errorBox) {
        errorBox.textContent = 'Mot de passe incorrect. Veuillez reessayer.';
        errorBox.style.display = 'block';
      }
      input.focus();
      input.select();
    } catch (err) {
      console.error("Erreur lors de l'envoi du mot de passe :", err);
      if (errorBox) {
        errorBox.textContent =
          "Une erreur est survenue pendant la verification du mot de passe.";
        errorBox.style.display = 'block';
      }
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
      }
    }

    return false;
  }

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.form-block');
    if (!form) return;

    form.addEventListener('submit', envoyerMdp);
  });
})();
