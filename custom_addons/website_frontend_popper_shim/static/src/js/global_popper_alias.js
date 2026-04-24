/** @odoo-module **/

/**
 * Bootstrap 5 `dropdown.js` (UMD) expects `globalThis["@popperjs/core"]`.
 * Odoo ships `web/static/lib/popper/popper.js` which publishes the API on `globalThis.Popper`.
 * Some asset merges leave the AMD name unset, which yields
 * `Popper__namespace.createPopper is not a function` when opening dropdowns (e.g. language switcher).
 *
 * This file is injected immediately before `dropdown.js` via `web.assets_frontend_lazy`.
 */
(function ensurePopperNamespace() {
    const root = typeof globalThis !== 'undefined' ? globalThis : window;
    if (!root) {
        return;
    }
    const popper = root.Popper;
    if (!popper || typeof popper.createPopper !== 'function') {
        return;
    }
    const existing = root['@popperjs/core'];
    if (!existing || typeof existing.createPopper !== 'function') {
        root['@popperjs/core'] = popper;
    }
})();
