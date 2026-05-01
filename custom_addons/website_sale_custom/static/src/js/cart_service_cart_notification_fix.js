/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { CartService } from '@website_sale/js/cart_service';

/**
 * CartNotification 的 Owl props 要求 refresh / freeze（函数）及 className；
 * 标准 _showCartNotification 未传入时会在加入购物车后校验失败。
 * 此处补默认值，与 web Notification 上同名方法语义对齐（无计时条时可空操作）。
 */
patch(CartService.prototype, {
    _showCartNotification(props, options = {}) {
        const notificationOptions = {
            ...options,
            className: options.className ?? '',
            refresh: typeof options.refresh === 'function' ? options.refresh : () => {},
            freeze: typeof options.freeze === 'function' ? options.freeze : () => {},
        };
        if (props.lines) {
            this.cartNotificationService.add('', {
                lines: props.lines,
                currency_id: props.currency_id,
                ...notificationOptions,
            });
        }
        if (props.warning) {
            this.cartNotificationService.add('', {
                warning: props.warning,
                ...notificationOptions,
            });
        }
    },
});
