# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.http import request


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('name', 'default_code', 'product_tmpl_id')
    @api.depends_context(
        'display_default_code',
        'seller_id',
        'company_id',
        'partner_id',
        'formatted_display_name',
    )
    def _compute_display_name(self):
        # 网站前端：与后台一致展示 [default_code] + name。
        # display_name 依赖 context，ORM 按 context 分缓存；不能只在 with_context(True) 的 env 上 super，
        # 否则值写在另一分区，当前 self.env 仍缺 display_name → ValueError: Compute method failed to assign。
        if request and getattr(request, 'is_frontend', False):
            forced = self.with_context(display_default_code=True)
            super(ProductProduct, forced)._compute_display_name()
            for rec, rec_forced in zip(self, forced):
                rec.display_name = rec_forced.display_name
            return
        return super()._compute_display_name()
