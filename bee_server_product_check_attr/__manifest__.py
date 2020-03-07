# -*- coding: utf-8 -*-
{
    'name': "Bee Server Product Check Attr",
    'version': '0.1',
    'category': 'Uncategorized',
    'author': "zhe",
    'summary': """产品添加检测值属性""",
    'description': """产品添加检测值属性""",

    'depends': ['product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_attr_views.xml',
        'views/product_views.xml',
        'views/stock_menu_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'application': True,
    'auto_install': False,
}