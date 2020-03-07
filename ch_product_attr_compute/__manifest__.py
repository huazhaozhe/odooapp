# -*- coding: utf-8 -*-
{
    'name': "CH Product Attr Compute",
    'version': '0.1',
    'category': 'Uncategorized',
    'author': "zhe",
    'summary': """销售采购产品检测值加权""",
    'description': """销售采购产品检测值加权""",

    'depends': ['sale', 'purchase', 'account', 'bee_server_product_check_attr'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
        'views/purchase_views.xml',
        'views/sale_views.xml',
        'views/account_invoice_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'application': True,
    'auto_install': False,
}