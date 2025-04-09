# -*- coding: utf-8 -*-
{
    'name': 'Multiple Warehouses in Sale Order Lines',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Set warehouse per sale order line and split delivery orders accordingly.',
    'description': """
        Allows selection of different warehouses per line in a sales order.
        Automatically splits delivery orders based on warehouse.
    """,
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'license': 'AGPL-3',
    'depends': [
        'sale_management',
        'stock',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
