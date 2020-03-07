#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/3/11 11:43
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : account_invoice.py
# @Software: PyCharm

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class CHAccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    compute_attr_ids = fields.Many2many('ch.product.check.attr.value', string='检测值', compute='_compute_attr_ids')
    product_check_attr_value_ids = fields.One2many('ch.product.check.attr.value', 'invoice_line_id')

    @api.multi
    def action_check_attr(self):
        action_ctx = dict(self.env.context)
        action_ctx['domain'] = [('invoice_line_id', '=', self.id), ('origin_model', '=', 'account.invoice.line')]
        if self.product_id:
            action_ctx['default_product_id'] = self.product_id.id
        view_id = self.env.ref('ch_product_attr_compute.ch_invoice_product_check_attr_value_from_view').id
        return {
            'name': _('质量'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }

    @api.constrains('product_id')
    def _get_product_attr(self):
        for line in self:
            exist_attrs = [ex_attr.attr_id.id for ex_attr in line.product_check_attr_value_ids]
            for attr in line.product_id.product_check_attr_setting_ids:
                if attr.attr_id.id not in exist_attrs:
                    if len(line.sale_line_ids) == 1:
                        weight = line.sale_line_ids[0].attr_value_weight_ids.filtered(
                            lambda x: x.attr_id.id == attr.attr_id.id)
                        if len(weight) == 1:
                            self.sudo().env['ch.product.check.attr.value'].create({
                                'origin_model': 'account.invoice.line',
                                'attr_id': attr.attr_id.id,
                                'attr_value': 0.0,
                                'product_id': line.product_id.id,
                                'invoice_id': line.invoice_id.id,
                                'invoice_line_id': line.id,
                                'weight_id': weight.id,
                            })
                    elif line.purchase_line_id:
                        weight = line.purchase_line_id.attr_value_weight_ids.filtered(
                            lambda x: x.attr_id.id == attr.attr_id.id)
                        if len(weight) == 1:
                            self.sudo().env['ch.product.check.attr.value'].create({
                                'origin_model': 'account.invoice.line',
                                'attr_id': attr.attr_id.id,
                                'attr_value': 0.0,
                                'product_id': line.product_id.id,
                                'invoice_id': line.invoice_id.id,
                                'invoice_line_id': line.id,
                                'weight_id': weight.id,
                                # 'purchase_line_id': move.purchase_line_id.id,
                            })
                    else:
                        self.sudo().env['ch.product.check.attr.value'].create({
                            'origin_model': 'account.invoice.line',
                            'attr_id': attr.attr_id.id,
                            'attr_value': 0.0,
                            'product_id': line.product_id.id,
                            'invoice_id': line.invoice_id.id,
                            'invoice_line_id': line.id,
                            # 'purchase_line_id': move.purchase_line_id.id,
                        })

    def _compute_attr_ids(self):
        for line in self:
            compute_attr = [attr.attr_id.id for attr in
                            line.product_id.product_check_attr_setting_ids.filtered(lambda x: x.compute_amount == True)]
            attrs = []
            for attr in line.product_check_attr_value_ids:
                if attr.attr_id.id in compute_attr:
                    attrs.append(attr.id)
            line.update({'compute_attr_ids': [(6, 0, attrs)]})
