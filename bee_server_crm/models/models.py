# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
from psycopg2 import IntegrityError

_logger = logging.getLogger(__name__)


class BeeServerCrmCustomerType(models.Model):
    _name = 'bee.server.customer.type'
    _description = '客户类型模型'

    name = fields.Char(string='类别名称', required=True)
    parten_type_id = fields.Many2one('bee.server.customer.type', string='父级客户')

    _sql_constraints = [
        ('code_name', 'unique(name)', '客户分类名称不得重复!'),
    ]


class BeeServerCrmContact(models.Model):
    _name = 'bee.server.customer.contact'
    _description = '联系人模型'

    name = fields.Char(string='联系人名称', required=True)
    sex = fields.Selection([
        ('1', '男'),
        ('0', '女'),
    ], string='性别', default='1')
    type_ids = fields.Many2many('bee.server.customer.type', string='联系人分类')
    phone = fields.Char(string='手机号码')
    tel = fields.Char(string='座机')
    email = fields.Char(string='电子邮箱')
    birthday = fields.Char(string='生日')
    job_profile = fields.Text(string='工作简介')
    note = fields.Text(string='备注')
    grade = fields.Selection([
        ('1', '一星'),
        ('2', '二星'),
        ('3', '三星'),
        ('4', '四星'),
        ('5', '五星'),
    ], string='评级', default='1')
    location = fields.Char(string='联系人地址')
    customer_id = fields.Many2one('bee.server.customer', string='关联的客户')


class BeeServerCrmCustomer(models.Model):
    _name = 'bee.server.customer'
    _description = '客户数据模型'

    company_id = fields.Integer(string='所属公司', required=True)
    name = fields.Char(string='客户名称', required=True)
    state = fields.Selection([
        ('1', '启用'),
        ('0', '停用'),
    ], string='状态', default='1')
    first_type_ids = fields.Many2many('bee.server.customer.type', 'rel_first_type', string='一级客户类型', required=True)
    second_type_ids = fields.Many2many('bee.server.customer.type', 'rel_second_type', string='二级客户类型', required=True)
    contact_ids = fields.One2many('bee.server.customer.contact', 'customer_id', string='联系人')
