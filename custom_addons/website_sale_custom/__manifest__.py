# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Custom Sale',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Per-website eCommerce behavior and inquiry settings',
    'depends': ['website_sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/sale_order_views.xml',
        'views/website_custom_sale_config_views.xml',
        'views/website_sale_inquiry_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_frontend': [
            'website_sale_custom/static/src/js/website_sale_inquiry_form.js',
            'website_sale_custom/static/src/js/cart_service_inquiry_redirect.js',
            'website_sale_custom/static/src/js/product_configurator_dialog/product_configurator_dialog.js',
            'website_sale_custom/static/src/js/product_configurator_dialog/product_configurator_dialog.xml',
            'website_sale_custom/static/src/js/combo_configurator_dialog/combo_configurator_dialog.js',
            'website_sale_custom/static/src/js/combo_configurator_dialog/combo_configurator_dialog.xml',
        ],
    },
}
