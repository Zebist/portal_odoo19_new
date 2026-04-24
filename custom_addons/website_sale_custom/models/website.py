# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _get_website_custom_sale_public_flags(self):
        """Flags for storefront templates (QWeb). Uses sudo; safe values only."""
        self.ensure_one()
        cfg = self.env['website.custom.sale.config'].sudo().search(
            [('website_id', '=', self.id)],
            limit=1,
        )
        return {
            'custom_sale_enable_checkout': cfg.enable_checkout if cfg else True,
            'custom_sale_enable_inquiry': cfg.enable_inquiry if cfg else False,
        }

    def _get_cart_show_wizard_checkout(self):
        """Whether to show wizard_checkout on /shop/cart (QWeb `show_wizard_checkout`)."""
        self.ensure_one()
        cfg = self.env['website.custom.sale.config'].sudo().search(
            [('website_id', '=', self.id)],
            limit=1,
        )
        return bool(cfg and cfg.show_cart_checkout_wizard)

    def _get_checkout_step_values(self):
        res = super()._get_checkout_step_values()
        res.update(self._get_website_custom_sale_public_flags())
        return res
