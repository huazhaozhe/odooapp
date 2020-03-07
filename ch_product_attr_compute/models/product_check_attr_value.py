#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/3/11 11:45
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : product_check_attr_value.py
# @Software: PyCharm

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class CHProductCheckAttrValue(models.Model):
    _name = 'ch.product.check.attr.value'

    origin_model = fields.Char(string='关联的源模型')
    attr_id = fields.Many2one('bee.server.product.check.attr', string='属性')
    attr_value = fields.Float(string='检测值')
    product_id = fields.Many2one('product.product')
    weight_id = fields.Many2one('ch.product.check.attr.value.weight')

    move_id = fields.Many2one('stock.move')
    purchase_id = fields.Many2one('purchase.order')
    purchase_line_id = fields.Many2one('purchase.order.line')
    sale_id = fields.Many2one('sale.order')
    sale_line_id = fields.Many2one('sale.order.line')
    invoice_id = fields.Many2one('account.invoice')
    invoice_line_id = fields.Many2one('account.invoice.line')

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s: %s' % (rec.attr_id.display_name, rec.attr_value)))
        return result


class CHProductCheckAttrValueWeight(models.Model):
    _name = 'ch.product.check.attr.value.weight'

    origin_model = fields.Char(string='关联的源模型')
    attr_id = fields.Many2one('bee.server.product.check.attr', string='属性')
    attr_value_ids = fields.One2many('ch.product.check.attr.value', 'weight_id')
    stock_attr_value = fields.Float(string='出入库加权计算值', compute='_cpmpute_attr_value', store=True)
    account_attr_value = fields.Float(string='结算加权计算值', compute='_cpmpute_attr_value', store=True)
    difference_attr_value = fields.Float(string='加权差', compute='_get_difference_attr_value', store=True)
    product_id = fields.Many2one('product.product')

    purchase_id = fields.Many2one('purchase.order')
    purchase_line_id = fields.Many2one('purchase.order.line')
    sale_id = fields.Many2one('sale.order')
    sale_line_id = fields.Many2one('sale.order.line')

    # 加权计算
    @api.depends('attr_value_ids.attr_value', 'attr_value_ids.move_id.state', 'attr_value_ids.invoice_line_id.invoice_id.state')
    def _cpmpute_attr_value(self):
        for weight in self:
            # 出入库加权
            quantity_done = 0.0
            weight_value = 0.0
            for value in weight.attr_value_ids.filtered(lambda x: x.move_id != False and x.move_id.state == 'done'):
                quantity_done += value.move_id.quantity_done
                weight_value += value.attr_value * value.move_id.quantity_done
            weight.stock_attr_value = weight_value / quantity_done if quantity_done != 0 else 0
            # 结算加权
            quantity = 0.0
            weight_value = 0.0
            for value in weight.attr_value_ids.filtered(
                lambda x: x.invoice_line_id != False and x.invoice_line_id.invoice_id.state not in ('draft', 'cancel')):
                quantity += value.invoice_line_id.quantity
                weight_value += value.attr_value * value.invoice_line_id.quantity
            weight.account_attr_value = weight_value / quantity if quantity != 0 else 0

    # 出入库与结算的差
    @api.depends('stock_attr_value', 'account_attr_value')
    def _get_difference_attr_value(self):
        for weight in self:
            if weight.stock_attr_value > 0 and weight.account_attr_value > 0:
                weight.difference_attr_value = weight.stock_attr_value - weight.account_attr_value
