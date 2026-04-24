# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website: Popper namespace shim for Bootstrap dropdowns',
    'version': '19.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'Maps global Popper to @popperjs/core before Bootstrap dropdown.js loads',
    'depends': ['web'],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'assets': {
        # `web.assets_frontend_lazy` 会 include 本 bundle；只改一处即可。
        'web.assets_frontend': [
            (
                'before',
                'web/static/lib/bootstrap/js/dist/dropdown.js',
                'website_frontend_popper_shim/static/src/js/global_popper_alias.js',
            ),
        ],
    },
}
