# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.http import request

from odoo.addons.website_sale.controllers.cart import Cart


class WebsiteSaleCustomCart(Cart):
    def _cart_values(self, **post):
        res = super()._cart_values(**post)
        res['show_wizard_checkout'] = request.website._get_cart_show_wizard_checkout()
        return res
