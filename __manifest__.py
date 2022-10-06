# -*- coding: utf-8 -*-

{
    'name': 'Farming and Agriculture Management',

    'summary': """
        Farm Management is a step ahead to make upper hand and control all agriculture operations.
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
    'depends': ['base',
                'mail',
                'l10n_eg',
                'account',
                'uom',
                'product',
                'sale',
                'purchase',
                'stock',
                ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_views.xml',
        'data/data_views.xml',
        'data/account_data_views.xml',
        # 'data/settings_views.xml',
        'views/menu.xml',
        'views/project_group_views.xml',
        'views/operations_views.xml',
        'views/materials_views.xml',
        'views/sales_views.xml',
        'views/produce_views.xml',
        'views/equipments_views.xml',
        'views/locations_views.xml',
        'views/projects_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': '55',
    'license': 'LGPL-3',
}