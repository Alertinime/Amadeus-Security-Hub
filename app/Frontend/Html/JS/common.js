// app/Frontend/Html/JS/common.js

(function (global) {
  /**
   * Récupère l'API exposée par pywebview (ou fallback window.api).
   */
  function getApi() {
    if (global.pywebview && global.pywebview.api) {
      return global.pywebview.api;
    }
    if (global.api) {
      return global.api;
    }
    return null;
  }

  /**
   * Appelle une méthode de l'API pywebview en gérant les erreurs de base.
   * @param {string} method
   * @param  {...any} args
   * @returns {Promise<unknown>}
   */
  async function callApi(method, ...args) {
    const api = getApi();
    if (!api) {
      console.warn('API pywebview indisponible pour', method);
      return;
    }

    const fn = api[method];
    if (typeof fn !== 'function') {
      console.warn(`Méthode "${method}" absente de l’API pywebview.`);
      return;
    }

    try {
      return await fn(...args);
    } catch (err) {
      console.error(`Erreur lors de l’appel API "${method}" :`, err);
      throw err;
    }
  }

  /**
   * Navigation simple entre les pages HTML chargees par pywebview.
   * @param {string} page
   */
  function goToPage(page) {
    if (!page || typeof page !== 'string') {
      return;
    }

    global.location.href = page;
  }

  global.getApi = getApi;
  global.callApi = callApi;
  global.goToPage = goToPage;
})(window);
