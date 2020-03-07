# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BeePurchaseOorder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step' \
                    or (order.company_id.po_double_validation == 'two_step' \
                        and order.amount_total < self.env.user.company_id.currency_id._convert(
                        order.company_id.po_double_validation_amount, order.currency_id, order.company_id,
                        order.date_order or fields.Date.today())) \
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
                for line in order.order_line:
                    self.env['bee.server.transport.contract'].create({
                        'name': order.name + '-TC' + str(list(order.order_line).index(line) + 1),
                        'company_id': order.company_id.id,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'origin': order.name,
                        'type': '采购',
                        'purchase_id': order.id,
                    })
            else:
                order.write({'state': 'to approve'})
        return True
