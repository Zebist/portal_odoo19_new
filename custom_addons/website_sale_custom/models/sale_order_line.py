# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models
from odoo.http import request


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    inquiry_line_note = fields.Text(
        string=_('Quote Line Note'),
        help=_('Note left by the customer for this line (website quote request).'),
    )

    def _get_line_header(self):
        """网站购物车/询价行标题：含 default_code；有变体属性时避免与 _get_combination_name 重复。"""
        if not (request and getattr(request, 'is_frontend', False)):
            return super()._get_line_header()
        if not self.product_id:
            return super()._get_line_header()
        product = self.product_id
        if self.product_template_attribute_value_ids:
            if product.default_code:
                return f'[{product.default_code}] {product.name}'
            return product.name
        return super()._get_line_header()
