/** @odoo-module **/

import { ComboConfiguratorDialog } from '@sale/js/combo_configurator_dialog/combo_configurator_dialog';
import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';

function readCustomSaleFlagsFromDom() {
    const d = document.documentElement.dataset;
    return {
        customSaleEnableCheckout:
            d.customSaleEnableCheckout === undefined
                ? true
                : d.customSaleEnableCheckout === '1',
        customSaleEnableInquiry: d.customSaleEnableInquiry === '1',
    };
}

patch(ComboConfiguratorDialog.prototype, {
    setup() {
        super.setup(...arguments);
        const flags = readCustomSaleFlagsFromDom();
        this.customSaleEnableCheckout = flags.customSaleEnableCheckout;
        this.customSaleEnableInquiry = flags.customSaleEnableInquiry;
        this.customSaleInquiryLinkLabel = _t('Request a quote');
    },

    /**
     * Add combo to cart (same as Add to Cart), then open the quote request page.
     */
    confirmThenInquiry() {
        return this.confirm({ goToCart: false, redirectToInquiry: true });
    },
});
