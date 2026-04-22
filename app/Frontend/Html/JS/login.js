// app/Frontend/Html/JS/login.js

(function () {
  async function envoyerMdp(event) {
    event.preventDefault();

    const input = document.getElementById('master-password');
    if (!input) {
      console.warn('Champ #master-password introuvable.');
      return false;
    }

    const value = input.value || '';

    // Appel Python via pywebview (méthode "login" comme dans ta version actuelle)
    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api || typeof api.login !== 'function') {
      console.warn('API login indisponible.');
      return false;
    }

    try {
      if (typeof callApi === 'function') {
        await callApi('login', value);
      } else {
        await api.login(value);
      }
    } catch (err) {
      console.error('Erreur lors de l’envoi du mot de passe :', err);
    }

    return false;
  }

  document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.form-block');
    if (!form) return;

    form.addEventListener('submit', envoyerMdp);
  });
})();
