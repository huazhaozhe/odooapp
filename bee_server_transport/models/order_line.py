# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError


class BeeTransportOrderLine(models.Model):
    _name = 'bee.server.transport.order.line'

    name = fields.Char(compute='_compute_name', store=True)
    order_id = fields.Many2one('bee.server.transport.order', string='运输单号', track_visibility='onchange')
    contract_id = fields.Many2one('bee.server.transport.contract', string='运输合同单', track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='产品', track_visibility='onchange')
    start_wet_weight = fields.Float(string='起始湿重', digits=(16, 2), track_visibility='onchange')
    arrive_wet_weight = fields.Float(string='到达湿重', digits=(16, 2), track_visibility='onchange')
    start_quality = fields.Float(string='起始质量', track_visibility='onchange')
    arrive_quality = fields.Float(string='到达质量', track_visibility='onchange')
    start_water_content = fields.Float(string='起始水份', track_visibility='onchange')
    arrive_water_content = fields.Float(string='到达水份', track_visibility='onchange')
    start_dry_weight = fields.Float(string='起始干重', compute='_get_start_dry_weight', store=True)
    arrive_dry_weight = fields.Float(string='到达干重', compute='_get_arrive_dry_weight', store=True)
    location_now = fields.Char(string='当前位置', related='order_id.location_now', track_visibility='onchange', store=True)
    summary_price = fields.Float(string='金额', track_visibility='onchange', compute='_get_summary_price', store=True)
    merge_qty = fields.Float('当前数量', digits=(16, 2), track_visibility='onchange')
    merge_from = fields.Many2one('bee.server.transport.order.line', string='并单源', track_visibility='onchange')
    company_id = fields.Many2one(related='contract_id.company_id')
    state = fields.Selection(related='order_id.state')
    bill = fields.Char(string='提单号')
    loading_date = fields.Date(string='装车时间')
    start_date = fields.Date(string='开始时间')
    arrive_date = fields.Date(string='到达时间')
    loss_type = fields.Selection([('0', '物流公司'), ('1', '我方')], string='损耗类型')

    @api.depends('start_water_content', 'start_wet_weight')
    def _get_start_dry_weight(self):
        for line in self:
            line.update({'start_dry_weight': line.start_wet_weight * (100 - line.start_water_content) / 100})

    @api.depends('arrive_water_content', 'arrive_wet_weight')
    def _get_arrive_dry_weight(self):
        for line in self:
            line.update({'arrive_dry_weight': line.arrive_wet_weight * (100 - line.arrive_water_content) / 100})

    @api.depends('order_id')
    def _compute_name(self):
        for line in self:
            if line.order_id:
                res = self.env['bee.server.transport.order.line'].search([('order_id', 'in', line.order_id.ids)])
                res = [r.id for r in res]
                line.update({'name': line.order_id.name + '-' + str(res.index(line.id) + 1)})

    @api.constrains('start_wet_weight')
    def _constrains_all_merge(self):
        if self.merge_from:
            res = self.env['bee.server.transport.order.line'].search(
                [('merge_from', '=', self.merge_from.id), ('order_id', '!=', False), ('contract_id', '!=', False)])
            if res:
                could_merge = abs(
                    self.merge_from.arrive_wet_weight - sum(r.start_wet_weight for r in res if r.id != self.id))
                if self.start_wet_weight > could_merge * 1.05:
                    raise ValidationError(_('大于可并单数量的1.05倍: %s!' % could_merge * 1.05))
                has_done = sum(r.start_wet_weight for r in res)
                if has_done > self.merge_from.arrive_wet_weight * 0.95:
                    self.merge_from.update({'merge_qty': 0})
                else:
                    self.merge_from.update({'merge_qty': self.merge_from.arrive_wet_weight - has_done})
        else:
            res = self.env['bee.server.transport.order.line'].search(
                [('merge_from', '=', False), ('order_id', '!=', False), ('contract_id', '=', self.contract_id.id)])
            if res:
                could_merge = abs(self.contract_id.product_qty - sum(r.start_wet_weight for r in res if r.id != self.id))
                if self.start_wet_weight > could_merge * 1.05:
                    raise ValidationError(_('大于可并单数量的1.05倍: %s!' % could_merge * 1.05))
        self.update({'merge_qty': self.start_wet_weight})

    @api.depends('order_id.total_money')
    def _get_summary_price(self):
        for line in self:
            all_lines = self.env['bee.server.transport.order.line'].search([('order_id', '=', line.order_id.id)])
            total_start_wet_weight = sum(all_line.start_wet_weight for all_line in all_lines)
            if total_start_wet_weight > 0:
                line.update({'summary_price': line.order_id.total_money * line.start_wet_weight / total_start_wet_weight})

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError((_('运输单非起点位置不能删除!')))
            if line.merge_from:
                res = self.sudo().env['bee.server.transport.order.line'].search([('merge_from', '=', line.merge_from.id)])
                line.merge_from.update({'merge_qty': line.merge_from.arrive_wet_weight - sum(r.start_wet_weight for r in res if r.id != line.id)})
        return super(BeeTransportOrderLine, self).unlink()

    @api.onchange('arrive_date')
    def _check_arrive_date(self):
        for line in self:
            if line.start_date and line.arrive_date and line.start_date > line.arrive_date:
                raise UserError((_('达到时间不能在发货时间之前!')))


class TransportCost(models.Model):
    _name = 'bee.server.transport.cost.line'
    _description = 'Transports Cost Line'
    # _inherit = ['mail.thread']

    order_id = fields.Many2one('bee.server.transport.order', string='运输单号')
    product_id = fields.Many2one('product.product', string='费用项目', track_visibility='onchange', required=True)
    price_unit = fields.Float(string='单价', required=True, default=0.0)
    product_uom_qty = fields.Float(string='数量', digits=(16, 2), required=True,
                                   default=1.0)
    price_total = fields.Float(compute='_compute_amount', string='金额', readonly=True)
    invoice_amount = fields.Float(string='开票金额')
    payment_amount = fields.Float(string='付款金额')

    @api.depends('price_unit', 'product_uom_qty')
    def _compute_amount(self):
        for line in self:
            line.update({'price_total': line.price_unit * line.product_uom_qty})