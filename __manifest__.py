# -*- coding: utf-8 -*-

{
    'name': 'Farming and Agriculture Management',

    'summary': """
        Organize farm and control several kind of agriculture business.
        """,

    'description': """
        start an agriculture business 
    """,

    'author': "Mohamed Sobh",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '15.0.0',

    # any module necessary for this one to work correctly
    'depends': ['stock',
                'base',
                'mail',
                'l10n_eg',
                'account',
                'uom',
                'product',
                'sale',
                'sale_management',
                'purchase',
                'hr_expense',
                'web_kanban_gauge',
                ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/settings_views.xml',
        'data/sequence_views.xml',
        'data/data_company.xml',
        'views/menu.xml',
        'views/project_group_views.xml',
        'views/operations_views.xml',
        'views/materials_views.xml',
        'views/expenses_views.xml',
        'views/sales_views.xml',
        'views/produce_views.xml',
        'views/equipments_views.xml',
        'views/locations_views.xml',
        'views/projects_views.xml',
        'views/control_views.xml',
        'views/inherit_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': '31',
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': {

        },
        'web.assets_qweb': {

        },
    },
}
