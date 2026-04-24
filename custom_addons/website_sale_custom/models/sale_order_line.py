# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    inquiry_line_note = fields.Text(
        string=_('Quote Line Note'),
        help=_('Note left by the customer for this line (website quote request).'),
    )
