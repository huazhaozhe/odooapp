# -*- coding: utf-8 -*-
{
    'name': "bee_server_excel_paste_setting",
    'version': '0.1',
    'author': "zhe",
    'category': 'Uncategorized',
    'summary': """Excel粘贴配置""",
    'description': """
        Excel粘贴配置
        配置过后直接可以从excel复制粘贴到odoo表单的明细行
        包括了外键关联的字段粘贴
        设置了匹配,则匹配的行会修改,否则新建
    """,

    'depends': ['web'],
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