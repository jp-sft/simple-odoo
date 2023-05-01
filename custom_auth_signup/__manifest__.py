{
    'name': 'Custom 2FA Auth Signup',
    'summary': 'This Module implement two-factor authentication using a token sent by email.',
    'description': "For more information, please see the documentation "
                   "https://github.com/jp-sft/simple-odoo/blob/13.0/README.md",
    'version': '1.0',
    'author': 'Simple',
    'category': 'Tools',
    'depends': ['auth_signup'],
    'data': ["templates/two_factor_auth.xml"],
    'installable': True,
    'url': 'https://github.com/jp-sft/simple-odoo/blob/13.0/README.md',
}
