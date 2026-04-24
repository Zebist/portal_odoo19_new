# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, fields, models


class WebsiteCustomSaleConfig(models.Model):
    _name = 'website.custom.sale.config'
    _description = _('Website Custom eCommerce & Inquiry Settings')
    _rec_name = 'website_id'

    website_id = fields.Many2one(
        'website',
        string=_('Website'),
        required=True,
        ondelete='cascade',
        index=True,
    )
    company_id = fields.Many2one(
        related='website_id.company_id',
        string=_('Company'),
        store=True,
        readonly=True,
    )
    enable_checkout = fields.Boolean(
        string=_('Enable Checkout'),
        default=False,
        help=_('When enabled, customers can proceed to the standard checkout and place orders.'),
    )
    enable_inquiry = fields.Boolean(
        string=_('Enable Request Quote'),
        default=True,
        help=_('When enabled, customers can submit quote requests from the shop.'),
    )
    show_cart_checkout_wizard = fields.Boolean(
        string=_('Show Checkout Steps on Cart'),
        default=False,
        help=_(
            'When enabled, the Order / Address / Payment progress bar is shown at the top of '
            'the shopping cart page (/shop/cart).'
        ),
    )
    notify_email = fields.Char(
        string=_('Inquiry Notification Email'),
        help=_('Email address that receives notifications when a customer submits a quote request.'),
        required=True,
    )
    notify_email_from = fields.Char(
        string=_('Inquiry Notification From'),
        help=_(
            'Optional sender address for inquiry notification emails. Examples: sales@example.com '
            'or "My Shop" <sales@example.com>. Leave empty to use the mail template default '
            '(company or system user).'
        ),
        required=True,
    )

    _website_id_unique = models.Constraint(
        'unique (website_id)',
        _('Only one configuration record is allowed per website.'),
    )
