#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/3/7 11:05
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : product.py
# @Software: PyCharm

import logging
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError

_logger = logging.getLogger(__name__)

class BeeServerProductTemplate(models.Model):
    _inherit = 'product.template'

    product_check_attr_setting_ids = fields.One2many('bee.server.product.check.attr.setting', 'product_temp_id')

    @api.constrains('product_check_attr_setting_ids')
    def _product_check_attr_setting_ids_uniqueness(self):
        if len(self.product_check_attr_setting_ids.mapped('attr_id')) != len(self.product_check_attr_setting_ids.ids):
            raise UserError('选择的属性已经被选中 !')
