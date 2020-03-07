# -*- coding: utf-8 -*-
{
    'name': "bee_server_crm",
    'version': '0.1',
    'category': 'Uncategorized',
    'author': "Goldenbee Team",
    'website': "https://www.beesrv.com",
    'summary': """""",
    'description': """""",

    'depends': ['bee_server_erp_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],

    'application': True,
    'auto_install': False,
}