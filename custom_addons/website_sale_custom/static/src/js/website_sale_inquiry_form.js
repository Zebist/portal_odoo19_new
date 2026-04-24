/** 询价表：根据数量与期望单价在前端计算行小计与订单合计（不写后端）。 */
(function () {
    'use strict';

    /**
     * @param {string} raw
     * @returns {number}
     */
    function parseAmount(raw) {
        if (raw == null || raw === '') {
            return 0;
        }
        const s = String(raw).trim().replace(/\s/g, '').replace(/,/g, '');
        const n = parseFloat(s);
        return Number.isFinite(n) ? n : 0;
    }

    /**
     * @param {HTMLFormElement} form
     */
    function updateTotals(form) {
        const dp = parseInt(form.dataset.decimalPlaces || '2', 10);
        const symbol = form.dataset.currencySymbol || '';
        const position = form.dataset.currencyPosition || 'before';

        let sum = 0;
        const rows = form.querySelectorAll('tr.o_ws_inquiry_line_row');
        rows.forEach((row) => {
            const qtyInput = row.querySelector('input[name^="line_qty_"]');
            const unitInput = row.querySelector('input[name^="line_expected_"]');
            const subEl = row.querySelector('.o_ws_inquiry_line_subtotal');
            const qty = parseAmount(qtyInput && qtyInput.value);
            const unit = parseAmount(unitInput && unitInput.value);
            const sub = qty * unit;
            sum += sub;
            if (subEl) {
                subEl.textContent = formatMoney(sub, symbol, position, dp);
            }
        });

        const totalEl = form.querySelector('.o_ws_inquiry_order_total');
        if (totalEl) {
            totalEl.textContent = formatMoney(sum, symbol, position, dp);
        }
    }

    /**
     * @param {number} amount
     * @param {string} symbol
     * @param {string} position
     * @param {number} dp
     */
    function formatMoney(amount, symbol, position, dp) {
        const safeDp = Number.isFinite(dp) && dp >= 0 ? dp : 2;
        const s = amount.toFixed(safeDp);
        if (!symbol) {
            return s;
        }
        if (position === 'after') {
            return s + '\u00a0' + symbol;
        }
        return symbol + s;
    }

    /**
     * 从服务端拉取最新订单行并替换明细表（组合/关联行由 Odoo 购物车逻辑更新）。
     * @param {HTMLFormElement} form
     * @returns {Promise<void>}
     */
    function refreshInquiryTable(form) {
        const wrap = form.querySelector('.o_ws_inquiry_table_wrap');
        if (!wrap) {
            return Promise.reject(new Error('missing table wrap'));
        }
        return fetch('/shop/inquiry/table_fragment', {credentials: 'same-origin'})
            .then((res) => res.json().then((data) => ({ res, data })))
            .then(({ res, data }) => {
                if (!res.ok || !data || !data.ok || typeof data.html !== 'string') {
                    throw new Error('fragment');
                }
                wrap.innerHTML = data.html;
                updateTotals(form);
            });
    }

    function bindForm(form) {
        if (!form || form.dataset.wsInquiryBound) {
            return;
        }
        form.dataset.wsInquiryBound = '1';
        const handler = () => updateTotals(form);
        form.addEventListener('input', handler);
        form.addEventListener('change', handler);
        handler();

        // Remove 行逻辑已暂时关闭（与模板一致）：删除后整表 fragment 重载会导致用户已改的数量/单价等未提交修改丢失。
        // form.addEventListener('click', (ev) => {
        //     const btn = ev.target.closest('.o_ws_inquiry_line_remove');
        //     ...
        // });
    }

    document.querySelectorAll('form.o_website_sale_inquiry_form').forEach(bindForm);
})();
