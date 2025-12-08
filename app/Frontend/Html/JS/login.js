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

    // Appel Python via pywebview (méthode "log" comme dans ta version actuelle)
    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api || typeof api.log !== 'function') {
      console.warn('API log indisponible.');
      return false;
    }

    try {
      if (typeof callApi === 'function') {
        await callApi('log', value);
      } else {
        await api.log(value);
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
