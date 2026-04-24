/** @odoo-module **/

import { ProductConfiguratorDialog } from '@sale/js/product_configurator_dialog/product_configurator_dialog';
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

patch(ProductConfiguratorDialog.prototype, {
    setup() {
        super.setup(...arguments);
        const flags = readCustomSaleFlagsFromDom();
        this.customSaleEnableCheckout = flags.customSaleEnableCheckout;
        this.customSaleEnableInquiry = flags.customSaleEnableInquiry;
        this.customSaleInquiryLinkLabel = _t('Request a quote');
    },

    /**
     * Add configured lines to cart (same as Add to cart), then open the quote request page.
     */
    async onConfirmThenInquiry() {
        await this.onConfirm({ goToCart: false, redirectToInquiry: true });
    },
});
