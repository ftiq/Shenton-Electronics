{
    'name': 'Fix Arabic Numbers',
    'version': '1.0',
    'summary': 'Force English Numbers in Arabic Language',
    'category': 'Hidden',
    'author': 'RASARD Technology',
    'depends': ['web'],
    'data': [],  # مافي بيانات، مافي ملفات XML
    'assets': {
        'web.assets_backend': [
            'fix_numbers/static/src/js/fix_numbers.js',
        ],
    },
    'installable': True,
    'auto_install': True,
}
