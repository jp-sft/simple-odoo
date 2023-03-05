# -*- coding: utf-8 -*-
{
    'name': "payroll_wizards",

    'summary': """
        Augmentation des fonctionnalités de création des bulletins de paie""",

    'description': """
        Les lots de paie permettent de générer les bulletins de paie de plusieurs employés en une seule opération.
        
    """,
    'author': "Jessy Pango & Hakim Hamdi",
    'website': "https://github.com/jp-sft/simple-odoo",
    'category': 'Uncategorized',
    'version': '0.3',
    'depends': ['om_hr_payroll_account'],

    'data': [
        "views/views.xml",
        "views/payroll_wizards_static.xml",
        "views/email_template_payslip.xml",
    ],
    'demo': [
    ],
    'post_init_hook': '_auto_create_payslip_and_send',
}
