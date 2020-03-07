# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class BeeSaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'sale',
            'confirmation_date': fields.Datetime.now()
        })
        for line in self.order_line:
            self.env['bee.server.transport.contract'].create({
                'name': self.name + '-TC' + str(list(self.order_line).index(line) + 1),
                'company_id': self.company_id.id,
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty,
                'origin': self.name,
                'type': '销售',
                'sale_id': self.id,
            })
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
        return True