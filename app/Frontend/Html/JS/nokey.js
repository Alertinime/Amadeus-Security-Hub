// app/Frontend/Html/JS/nokey.js

(function () {
  async function retryDetection() {
    const api = typeof getApi === 'function' ? getApi() : null;
    if (!api || typeof api.reload_usb_check !== 'function') {
      console.warn('API reload_usb_check indisponible.');
      return;
    }

    try {
      const nextPage =
        typeof callApi === 'function'
          ? await callApi('reload_usb_check')
          : await api.reload_usb_check();

      if (typeof goToPage === 'function') {
        goToPage(nextPage);
      } else if (nextPage) {
        window.location.href = nextPage;
      }
    } catch (err) {
      console.error('Erreur lors de la nouvelle détection :', err);
    }
  }

  function quitApp() {
    window.close();
  }

  function start() {
    const retryButton = document.querySelector('[data-retry-detection]');
    if (retryButton) {
      retryButton.addEventListener('click', retryDetection);
    }

    const quitButton = document.querySelector('[data-quit-app]');
    if (quitButton) {
      quitButton.addEventListener('click', quitApp);
    }
  }

  document.addEventListener('DOMContentLoaded', start);
})();
