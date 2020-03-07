# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BeeTransportLocation(models.Model):
    _name = 'bee.server.transport.location'

    name = fields.Char(string='地点', required=True)
    company_id = fields.Many2one('res.company', string='所属公司')
    purchase_andsingle = fields.Integer(string='采购优先级')
    purchase_destination = fields.Boolean('是否采购终点', default=False)
    sale_andsingle = fields.Integer(string='销售优先级')
    sale_destination = fields.Boolean('是否销售终点', default=False)

    _sql_constraints = [
        ('location_uniqu', 'unique(location, company_id)', '每个公司的地点不允许重复！'),
    ]


class BeeTransportMethod(models.Model):
    _name = 'bee.server.transport.method'

    name = fields.Char(string='运输方式')
    company_id = fields.Many2one('res.company', string='承运公司')
