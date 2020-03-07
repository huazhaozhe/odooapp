# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _


_logger = logging.getLogger(__name__)


class CHPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    attr_value_weight_ids = fields.One2many('ch.product.check.attr.value.weight', 'purchase_line_id')

    @api.multi
    def action_check_attr(self):
        action_ctx = dict(self.env.context)
        action_ctx['domain'] = [('origin_model', '=', 'purchase.order.line'), ('purchase_line_id', '=', self.id),
                                ('move_id', '=', False)]
        if self.product_id:
            action_ctx['default_product_id'] = self.product_id.id
        action_ctx['default_purchase_line_id'] = self.id,
        if self.order_id:
            action_ctx['default_purchase_id'] = self.order_id.id
        view_id = self.env.ref('ch_product_attr_compute.ch_purchase_product_check_attr_value_compute_from_view').id
        return {
            'name': _('质量'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
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
                        'origin_model': 'purchase.order.line',
                        'attr_id': attr.attr_id.id,
                        'stock_attr_value': 0.0,
                        'account_attr_value': 0.0,
                        'product_id': line.product_id.id,
                        'purchase_id': line.order_id.id,
                        'purchase_line_id': line.id,
                    })

