# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.fields import Domain


class WebsiteSnippetFilter(models.Model):
    _inherit = 'website.snippet.filter'

    def _get_products_alternative_products(
        self, website, limit, domain, product_template_id=None, **kwargs,
    ):
        """替代商品：不因「已在购物车」而隐藏，仍排除当前商品自身变体。"""
        products = self.env['product.product']
        current_template = self.env['product.template'].browse(
            product_template_id and int(product_template_id)
        ).exists()
        if current_template:
            excluded_products = current_template.product_variant_ids
            alternative_products = current_template._get_website_alternative_product()
            if self.env.context.get('hide_variants'):
                included_products = alternative_products.product_variant_id
            else:
                included_products = alternative_products.product_variant_ids
            products = included_products - excluded_products
            if products:
                domain = Domain(domain) & Domain('id', 'in', products.ids)
                products = self.env['product.product'].with_context(
                    display_default_code=False,
                ).search(domain, limit=limit)
        return products
