#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/3/11 12:55
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : sale.py
# @Software: PyCharm

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class CHSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    attr_value_weight_ids = fields.One2many('ch.product.check.attr.value.weight', 'sale_line_id')

    @api.multi
    def action_check_attr(self):
        action_ctx = dict(self.env.context)
        action_ctx['domain'] = [('origin_model', '=', 'sale.order.line'), ('sale_line_id', '=', self.id),
                                ('move_id', '=', False)]
        if self.product_id:
            action_ctx['default_product_id'] = self.product_id.id
        action_ctx['default_sale_line_id'] = self.id,
        if self.order_id:
            action_ctx['default_sale_id'] = self.order_id.id
        view_id = self.env.ref('ch_product_attr_compute.ch_sale_product_check_attr_value_compute_from_view').id
        return {
            'name': _('质量'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }

    @api.constrains('product_id')
    def _get_product_attr(self):
        for line in self:
            exist_attrs = [ex_attr.attr_id.id for ex_attr in line.attr_value_weight_ids]
            for attr in line.product_id.product_check_attr_setting_ids:
                if attr.attr_id.id not in exist_attrs:
                    self.sudo().env['ch.product.check.attr.value.weight'].create({
                        'origin_model': 'sale.order.line',
                        'attr_id': attr.attr_id.id,
                        'stock_attr_value': 0.0,
                        'account_attr_value': 0.0,
                        'product_id': line.product_id.id,
                        'sale_id': line.order_id.id,
                        'sale_line_id': line.id,
                    })
