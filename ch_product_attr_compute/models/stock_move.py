#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/3/6 13:58
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : stock_move.py
# @Software: PyCharm

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class CHStockMove(models.Model):
    _inherit = 'stock.move'

    sale_compute_attr_ids = fields.Many2many('ch.product.check.attr.value', string='出库品位', compute='_compute_attr_ids')
    purchsae_compute_attr_ids = fields.Many2many('ch.product.check.attr.value', string='入库品位',
                                                 compute='_compute_attr_ids')
    product_check_attr_value_ids = fields.One2many('ch.product.check.attr.value', 'move_id')

    @api.multi
    def action_check_attr(self):
        action_ctx = dict(self.env.context)
        action_ctx['domain'] = [('move_id', '=', self.id), ('origin_model', '=', 'stock.move')]
        if self.product_id:
            action_ctx['default_product_id'] = self.product_id.id
        if self.purchase_line_id:
            action_ctx['default_purchase_id'] = self.purchase_line_id.order_id.id
            action_ctx['default_purchase_line_id'] = self.purchase_line_id.id
        elif self.sale_line_id:
            action_ctx['default_sale_id'] = self.sale_line_id.order_id.id
            action_ctx['default_sale_line_id'] = self.sale_line_id.id
        view_id = self.env.ref('ch_product_attr_compute.ch_stock_move_product_check_attr_value_from_view').id
        return {
            'name': _('质量'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }

    @api.constrains('product_id')
    def _get_product_attr(self):
        for move in self:
            exist_attrs = [ex_attr.attr_id.id for ex_attr in move.product_check_attr_value_ids]
            for attr in move.product_id.product_check_attr_setting_ids:
                if attr.attr_id.id not in exist_attrs:
                    if move.sale_line_id:
                        weight = move.sale_line_id.attr_value_weight_ids.filtered(
                            lambda x: x.attr_id.id == attr.attr_id.id)
                        if len(weight) == 1:
                            self.sudo().env['ch.product.check.attr.value'].create({
                                'origin_model': 'stock.move',
                                'attr_id': attr.attr_id.id,
                                'attr_value': 0.0,
                                'move_id': move.id,
                                'product_id': move.product_id.id,
                                'sale_id': move.sale_line_id.order_id.id,
                                'weight_id': weight.id,
                                # 'sale_line_id': move.sale_line_id.id,
                            })
                    elif move.purchase_line_id:
                        weight = move.sale_line_id.attr_value_weight_ids.filtered(
                            lambda x: x.attr_id.id == attr.attr_id.id)
                        if len(weight) == 1:
                            self.sudo().env['ch.product.check.attr.value'].create({
                                'origin_model': 'stock.move',
                                'attr_id': attr.attr_id.id,
                                'attr_value': 0.0,
                                'move_id': move.id,
                                'product_id': move.product_id.id,
                                'purchase_id': move.purchase_line_id.order_id.id,
                                'weight_id': weight.id,
                                # 'purchase_line_id': move.purchase_line_id.id,
                            })
                    else:
                        self.sudo().env['ch.product.check.attr.value'].create({
                            'origin_model': 'stock.move',
                            'attr_id': attr.attr_id.id,
                            'attr_value': 0.0,
                            'move_id': move.id,
                            'product_id': move.product_id.id,
                        })

    def _compute_attr_ids(self):
        for move in self:
            compute_attr = [attr.attr_id.id for attr in
                            move.product_id.product_check_attr_setting_ids.filtered(lambda x: x.compute_amount == True)]
            attrs = []
            for attr in move.product_check_attr_value_ids:
                if attr.attr_id.id in compute_attr:
                    attrs.append(attr.id)
            if move.picking_id.picking_type_code == 'outgoing':
                move.update({'sale_compute_attr_ids': [(6, 0, attrs)]})
            if move.picking_id.picking_type_code == 'incoming':
                move.update({'purchsae_compute_attr_ids': [(6, 0, attrs)]})

    @api.multi
    def action_copy(self):
        if self.quantity_done > 0 \
                and self.picking_id.state not in ['done', 'cancel'] \
                and self.quantity_done != self.product_uom_qty:
            line = self.copy()
            line.product_uom_qty = self.product_uom_qty - self.quantity_done
            self.product_uom_qty = self.quantity_done
            self.quantity_done = self.product_uom_qty
            line.quantity_done = 0
