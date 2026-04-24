# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from markupsafe import Markup, escape
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request
from odoo.tools.float_utils import float_round
from odoo.tools.mail import email_normalize
from odoo.tools.misc import consteq

_logger = logging.getLogger(__name__)


def _parse_float(val, precision_digits=2):
    if val is None or val == '':
        return 0.0
    try:
        f = float(val)
    except (ValueError, TypeError):
        return 0.0
    return float_round(f, precision_digits=precision_digits)


def _inquiry_order_note_to_html(raw):
    """整单备注：转义后写入 sale.order.note（Html）。"""
    text = (raw or '').strip()
    if not text:
        return False
    parts = escape(text).split('\n')
    inner = Markup('<br/>').join(parts)
    return Markup('<div class="o_website_inquiry_order_note"><p>') + inner + Markup('</p></div>')


class WebsiteSaleInquiry(http.Controller):
    def _get_custom_config(self):
        return request.env['website.custom.sale.config'].sudo().search(
            [('website_id', '=', request.website.id)],
            limit=1,
        )

    @http.route('/shop/inquiry', type='http', auth='public', website=True, sitemap=False)
    def shop_inquiry(self, product_id=None, add_qty=1, error=None, **kw):
        cfg = self._get_custom_config()
        if not cfg or not cfg.enable_inquiry:
            return request.redirect('/shop/cart')

        order = request.cart
        if not order:
            order = request.website._create_cart()

        if product_id:
            try:
                pid = int(product_id)
                qty = _parse_float(add_qty, precision_digits=3) or 1.0
            except (ValueError, TypeError):
                pid, qty = None, 1.0

            if pid:
                product = request.env['product.product'].sudo().browse(pid)
                if product.exists() and product._is_add_to_cart_allowed():
                    order._cart_add(pid, quantity=qty)

        order = request.cart
        if not order or not order.order_line:
            return request.redirect('/shop/cart')

        return request.render('website_sale_custom.inquiry_form', {
            'website_sale_order': order.sudo(),
            'error': error,
        })

    @http.route(
        '/shop/inquiry/line/remove/<int:line_id>',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def shop_inquiry_line_remove(self, line_id, **post):
        """从当前会话购物车中删除一行（询价页「Remove」）。

        POST 带 ``ajax=1`` 时返回 JSON ``{ok, redirect?}``，供前端无刷新删行并保留表单已填内容。
        """
        want_json = post.get('ajax') in ('1', 'true', 'True')

        def json_ok(**payload):
            return request.make_json_response({'ok': True, **payload})

        def json_err(message, code=400):
            return request.make_json_response({'ok': False, 'error': message}, status=code)

        cfg = self._get_custom_config()
        if not cfg or not cfg.enable_inquiry:
            if want_json:
                return json_err('disabled', 404)
            raise NotFound()

        order = request.cart
        if not order:
            if want_json:
                return json_ok(redirect='/shop/cart')
            return request.redirect('/shop/cart')

        order_sudo = order.sudo()
        if not order_sudo.order_line.filtered(lambda l: l.id == line_id):
            if want_json:
                return json_ok()  # 这里不存在，有可能是用户删除了关联商品，产品会一起删除，所以说正常的，需要返回 ok
            return request.redirect('/shop/inquiry')

        order_sudo._cart_update_line_quantity(line_id=line_id, quantity=0.0)

        order = request.cart
        if not order or not order.order_line:
            if want_json:
                return json_ok(redirect='/shop/cart')
            return request.redirect('/shop/cart')
        if want_json:
            return json_ok()
        return request.redirect('/shop/inquiry')

    @http.route(
        '/shop/inquiry/table_fragment',
        type='http',
        auth='public',
        website=True,
        methods=['GET'],
        sitemap=False,
    )
    def shop_inquiry_table_fragment(self, **kw):
        """返回当前会话购物车询价明细表 HTML（与询价页一致），供 Remove 后无刷新重渲染。"""
        cfg = self._get_custom_config()
        if not cfg or not cfg.enable_inquiry:
            raise NotFound()

        order = request.cart
        if not order or not order.order_line:
            return request.make_json_response({'ok': False, 'error': 'empty'}, status=400)

        html = request.env['ir.ui.view'].sudo()._render_template(
            'website_sale_custom.inquiry_form_table_block',
            {'website_sale_order': order.sudo()},
        )
        return request.make_json_response({'ok': True, 'html': str(html)})

    @http.route(
        '/shop/inquiry/submit',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=True,
    )
    def shop_inquiry_submit(self, **post):
        cfg = self._get_custom_config()
        if not cfg or not cfg.enable_inquiry:
            raise NotFound()

        order = request.cart
        if not order or not order.order_line:
            return request.redirect('/shop/cart')

        email = email_normalize(post.get('inquiry_email') or '', strict=False)
        if not email:
            return request.redirect('/shop/inquiry?error=email_required')

        order_sudo = order.sudo()
        # 可选公司名称：写入报价单；提交后由 sale.order._sync_inquiry_company_to_partner 同步到客户
        company_name = (post.get('inquiry_company_name') or '').strip()

        Partner = request.env['res.partner'].sudo().with_company(order_sudo.company_id)
        partner = Partner.search(
            [
                ('email', '=', email),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', order_sudo.company_id.id),
            ],
            limit=1,
        )
        if not partner:
            create_vals = {
                'name': (post.get('contact_name') or '').strip() or email.split('@')[0],
                'email': email,
                'company_id': order_sudo.company_id.id,
            }
            partner = Partner.create(create_vals)

        currency = order_sudo.currency_id
        prec = currency.decimal_places

        # 询价页上每行数量来自表单字段 line_qty_<订单行ID>（用户可改数量再提交）。
        # raw_qty 为 POST 原始字符串：有值则解析为本次提交数量；缺失或空串则沿用行上已有
        # product_uom_qty，避免异常/不完整请求把数量误清空。
        for line in list(order_sudo.order_line):
            raw_qty = post.get('line_qty_%s' % line.id)
            if raw_qty is None or raw_qty == '':
                qty = line.product_uom_qty
            else:
                qty = _parse_float(raw_qty, precision_digits=3)

            if qty <= 0:
                line.unlink()
                continue
            order_sudo._cart_update_line_quantity(line_id=line.id, quantity=qty)

        order_sudo = request.cart.sudo()
        if not order_sudo or not order_sudo.order_line:
            return request.redirect('/shop/cart')

        for line in order_sudo.order_line:
            exp = _parse_float(post.get('line_expected_%s' % line.id), precision_digits=prec)
            note = (post.get('line_note_%s' % line.id) or '').strip()
            line.write({
                'price_unit': exp if exp else False,
                'inquiry_line_note': note or False,
            })

        order_sudo.write({
            'is_website_inquiry': True,
            'inquiry_contact_email': email,
            'inquiry_company_name': company_name or False,
        })
        order_sudo._update_address(
            partner.id,
            ['partner_id', 'partner_invoice_id', 'partner_shipping_id'],
        )
        order_sudo._sync_inquiry_company_to_partner()

        # note 在 _update_address 之后写入：避免 partner_id 触发的 _compute_note 覆盖客户备注
        order_sudo.write({'note': _inquiry_order_note_to_html(post.get('inquiry_order_note'))})

        if cfg.notify_email:
            try:
                order_sudo._send_website_inquiry_notification(cfg)
            except Exception:
                _logger.exception('Failed to send website inquiry notification email')

        access_token = order_sudo._portal_ensure_token()
        oid = order_sudo.id
        request.website.sale_reset()
        return request.redirect(
            '/shop/inquiry/done?order_id=%s&access_token=%s' % (oid, access_token)
        )

    @http.route('/shop/inquiry/done', type='http', auth='public', website=True, sitemap=False)
    def shop_inquiry_done(self, order_id=None, access_token=None, **kw):
        if not order_id or not access_token:
            return request.redirect('/shop')
        try:
            oid = int(order_id)
        except (ValueError, TypeError):
            return request.redirect('/shop')
        order = request.env['sale.order'].sudo().browse(oid)
        if not order.exists():
            return request.redirect('/shop')
        if not consteq(order.access_token, access_token):
            return request.redirect('/shop')
        if not order.is_website_inquiry:
            return request.redirect('/shop')
        return request.render('website_sale_custom.inquiry_thanks', {
            'order': order,
        })
