# -*- coding: utf-8 -*-
{
    'name': "Track User Location",
    'summary': "Track User Location",
    'description': "Track User Location",
    'author': "Majed Hameed",
    'website': "https://ajabaa.com",
    'license': "LGPL-3",  # ✅ Added license key to remove warning
    'category': 'Tools',  # ✅ Updated category to a more relevant one
    'version': '18.0.1.0.0',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/location_session.xml',
        'data/ir_sequence_data.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'mj_track_location/static/src/js/track_user_location.js',
            'mj_track_location/static/src/js/get_location.js',
        ],
    },
    'installable': True,  # ✅ Ensures module is installable
    'application': True,  # ✅ Makes it appear in Odoo apps menu
    'auto_install': False,  # ✅ Prevents automatic installation
}
