/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { serializeDateTime } from '@web/core/l10n/dates';
import { redirect } from '@web/core/utils/urls';
import { CartService } from '@website_sale/js/cart_service';
import { ComboConfiguratorDialog } from '@sale/js/combo_configurator_dialog/combo_configurator_dialog';
import { ProductConfiguratorDialog } from '@sale/js/product_configurator_dialog/product_configurator_dialog';

const { DateTime } = luxon;

patch(CartService.prototype, {
    async _openProductConfigurator(
        productTemplateId,
        quantity,
        uomId,
        combination,
        productCustomAttributeValues,
        options,
        additionalData
    ) {
        return await new Promise((resolve) => {
            this.dialog.add(ProductConfiguratorDialog, {
                productTemplateId: productTemplateId,
                ptavIds: combination,
                customPtavs: productCustomAttributeValues.map((customPtav) => ({
                    id: customPtav.custom_product_template_attribute_value_id,
                    value: customPtav.custom_value,
                })),
                quantity: quantity,
                productUOMId: uomId,
                soDate: serializeDateTime(DateTime.now()),
                edit: false,
                isFrontend: true,
                selectedComboItems: [],
                options,
                ...additionalData,
                save: async (mainProduct, optionalProducts, confirmOptions) => {
                    const product = this._serializeProduct(mainProduct);
                    const redirectToInquiry = confirmOptions.redirectToInquiry;
                    const qty = await this._makeRequest({
                        productTemplateId: product.product_template_id,
                        productId: product.product_id,
                        quantity: product.quantity,
                        uom_id: product.uom_id,
                        productCustomAttributeValues: product.product_custom_attribute_values,
                        noVariantAttributeValues: product.no_variant_attribute_value_ids,
                        linked_products: optionalProducts.map(this._serializeProduct),
                        shouldRedirectToCart: confirmOptions.goToCart,
                        ...additionalData,
                    });
                    if (redirectToInquiry) {
                        redirect('/shop/inquiry');
                    }
                    resolve(qty);
                },
                discard: () => resolve(0),
            });
        });
    },

    async _openComboConfigurator(
        productTemplateId,
        productId,
        combos,
        remainingData,
        options,
        additionalData
    ) {
        return await new Promise((resolve) => {
            this.dialog.add(ComboConfiguratorDialog, {
                combos: combos,
                ...remainingData,
                date: serializeDateTime(DateTime.now()),
                edit: false,
                isFrontend: true,
                options,
                ...additionalData,
                save: async (comboProductData, selectedComboItems, confirmOptions) => {
                    const redirectToInquiry = confirmOptions.redirectToInquiry;
                    const qty = await this._makeRequest({
                        productTemplateId: productTemplateId,
                        productId: productId,
                        quantity: comboProductData.quantity,
                        linked_products: selectedComboItems.map((comboItem) =>
                            this._serializeComboItem(
                                comboItem,
                                productTemplateId,
                                comboProductData.quantity
                            )
                        ),
                        shouldRedirectToCart: confirmOptions.goToCart,
                        ...additionalData,
                    });
                    if (redirectToInquiry) {
                        redirect('/shop/inquiry');
                    }
                    resolve(qty);
                },
                discard: () => resolve(0),
            });
        });
    },
});
