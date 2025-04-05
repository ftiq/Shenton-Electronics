{
    'name': 'Arabic Western Numerals Fix',
    'version': '1.0.0',
    'summary': 'Force Western numerals in Arabic UI (v18)',
    'category': 'Localization',
    'author': 'RASARD Teknoloji',
    'website': 'https://rasard.com',
    'depends': ['web'],
    'assets': {
        'web._assets_backend_helpers': [
            'arabic_western_numerals_fix/static/src/js/fix_arabic_numbers.js',
        ],
    },
    'installable': True,
    'application': False,
}
