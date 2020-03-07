# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError

_logger = logging.getLogger(__name__)


class BeeServerProductCheckAttr(models.Model):
    _name = 'bee.server.product.check.attr'

    name = fields.Char(string='检测值名称', required=True)

    @api.constrains('name')
    def _name_uniqueness(self):
        attrs = [attr.name for attr in self.search([('id', '!=', self.id)])]
        for attr in self:
            if attr.name in attrs:
                raise UserError('属性 %s 名称已存在, 禁止重复创建!' % attr.name)


class BeeServerProductAttrSetting(models.Model):
    _name = 'bee.server.product.check.attr.setting'

    attr_id = fields.Many2one('bee.server.product.check.attr', string='属性', required=True)
    compute_amount = fields.Boolean(string='是否主属性', default=False)
    product_temp_id = fields.Many2one('product.template')

