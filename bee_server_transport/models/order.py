# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError


class BeeTransprotOrder(models.Model):
    _name = 'bee.server.transport.order'
    # _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(store=True, string='运输单', copy=False, track_visibility='onchange', required=True)
    transport_method = fields.Many2one('bee.server.transport.method', track_visibility='onchange', string='运输方式', required=True)
    location_start = fields.Many2one('bee.server.transport.location', track_visibility='onchange', string='起点', required=True)
    location_end = fields.Many2one('bee.server.transport.location', track_visibility='onchange', string='终点', required=True)
    location_now = fields.Char(string='当前位置', compute='_get_location_now', track_visibility='onchange', readonly=True, store=True)
    arrive_time = fields.Date(string='到达时间', track_visibility='onchange')
    vander = fields.Many2one('res.partner', track_visibility='onchange', string="物流公司")
    logistic_number = fields.Char(string="物流单号", track_visibility='onchange')
    start_time = fields.Date(string='发货时间', track_visibility='onchange')
    forecast_end_time = fields.Date(string='预计到达时间', track_visibility='onchange')
    loading_date = fields.Date(string='装车时间', track_visibility='onchange')
    unit_price = fields.Float(string='单价', track_visibility='onchange', default=0.00)
    line_ids = fields.One2many('bee.server.transport.order.line', 'order_id', string='在途信息')
    cost_line_ids = fields.One2many('bee.server.transport.cost.line', 'order_id', string='费用项目')

    merge_contract_ids = fields.Many2many('bee.server.transport.contract', string='添加合同单')
    merge_line_ids = fields.Many2many('bee.server.transport.order.line', string='添加在途行')

    total_money = fields.Float(string='金额', compute='_get_total_money', store=True)

    _sql_constraints = [
        ('trans_name_unique', 'unique(name)', '运输单号必须唯一！'),
    ]

    state = fields.Selection([
        ('draft', '起点'),
        ('doing', '途中'),
        ('done', '终点'),
        ('closed', '关闭'),
    ], string='状态', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.sudo().env['ir.sequence'].next_by_code('bee.server.transport.order') or '/'
        return super(BeeTransprotOrder, self).create(vals)

    @api.multi
    def button_doing(self):
        if len(self.line_ids) == 0:
            raise UserError((_('在途信息为空！')))
        for line in self.line_ids:
            if not line.start_wet_weight or line.start_wet_weight <= 0:
                raise ValidationError(_('在途信息所有行的发货湿重必须大于0'))
            if not line.start_dry_weight or line.start_dry_weight <= 0:
                raise ValidationError(_('在途信息所有行的发货干重必须大于0'))
            if line.start_wet_weight < line.start_dry_weight:
                raise UserError((_('发货干重不能大于发货湿重！')))
            if not line.start_date:
                raise UserError((_('发货时间不能为空！')))
            line.write({'merge_qty': line.start_wet_weight})
        self.write({'state': 'doing'})
        return {}

    @api.multi
    def button_done(self):
        for x in self.line_ids:
            if not x.arrive_wet_weight or x.arrive_wet_weight <= 0:
                raise ValidationError(_('在途信息所有行的到达湿重必须大于0'))
            if not x.arrive_dry_weight or x.arrive_dry_weight <= 0:
                raise ValidationError(_('在途信息所有行的到达干重必须大于0'))
            loss_dry = x.arrive_dry_weight - x.start_dry_weight
            if loss_dry < 0 and x.start_dry_weight * 0.003 < abs(loss_dry) and not x.loss_type:
                raise ValidationError(_('当干重损耗大于千分之三时必须指定损耗类型！'))
            if not x.arrive_date:
                raise UserError((_('到达时间不能为空！')))
            if x.arrive_wet_weight < x.arrive_dry_weight:
                raise UserError((_('到达干重不能大于到达湿重！')))
            x.write({'merge_qty': x.arrive_wet_weight})
            contract = self.sudo().env['bee.server.transport.contract'].search([('id', '=', x.contract_id.id)])
            if sum(line.arrive_wet_weight for line in contract.line_ids if line.order_id.location_end == contract.location_end) >= contract.product_qty*0.95:
                contract.write({'state': 'done'})
        self.write({'state': 'done'})
        return {}

    @api.multi
    def button_close(self):
        self.write({'state': 'closed'})
        for line in self.line_ids:
            line.write({'state':'closed'})
            line.merge_qty = 0
        return {}

    @api.multi
    def action_update_merge(self):
        """按钮跳转到新窗口，并传入context作为domain"""
        # If it's a returned stock move, we do not want to create a lot
        view_id = self.env.ref('bee_server_transport.merge_form').id
        contract_ids = []
        line_ids = []
        res = self.env['bee.server.transport.contract'].search(
            [('location_start', '=', self.location_start.id), ('state', '=', 'doing')])
        for r in res:
            if abs(r.product_qty - sum([x.start_wet_weight for x in r.line_ids if x.order_id.location_start == r.location_start])) >= r.product_qty * 0.05:
                contract_ids.append(r.id)

        res = self.env['bee.server.transport.order.line'].search([
            ('order_id', '!=', False),
            ('merge_qty', '>', 0),
            ('state', '=', 'done'),
            ('order_id.location_end.id', '=', self.location_start.id),
        ])
        for r in res:
            if r.merge_qty >= r.arrive_wet_weight * 0.05:
                line_ids.append(r.id)

        action_ctx = {}
        action_ctx['contract_ids'] = contract_ids
        action_ctx['line_ids'] = line_ids

        return {
            'name': _('添加并单'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'bee.server.transport.order',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx,
        }

    @api.multi
    def update_merge_line(self):
        l = []
        self.line_ids.unlink()
        # x:合同单模型
        for x in self.merge_contract_ids:
            # x.update_location()

            if len(x.line_ids) == 0:
                product_qty = x.product_qty
            else:
                product_qty = x.product_qty - sum([_l.start_wet_weight for _l in x.line_ids if _l.order_id.location_start.id == x.location_start.id])
            if product_qty > x.product_qty * 0.05:
                l.append(
                    self.env['bee.server.transport.order.line'].create({
                        'contract_id': x.id,
                        'product_id': x.product_id.id,
                        'start_wet_weight': product_qty,
                        'merge_qty': product_qty,
                        'summary_price': 0.0,
                    }).id
                )
        # x:在途信息模型
        for x in self.merge_line_ids:
            l.append(
                self.env['bee.server.transport.order.line'].create({
                    'contract_id': x.contract_id.id,
                    'product_id': x.product_id.id,
                    'start_wet_weight': x.merge_qty,
                    'merge_qty': x.merge_qty,
                    'merge_from': x.id,
                    'summary_price': 0.0,
                    # TODO 起始质量是否等于上一步的到达...
                }).id
            )
            x.merge_qty = 0
        self.update({'line_ids': [(6, 0, l)]})

    @api.multi
    def unlink(self):
        for order in self:
            for line in order.line_ids:
                line.unlink()
        return super(BeeTransprotOrder, self).unlink()

    @api.depends('cost_line_ids')
    def _get_total_money(self):
        for order in self:
            total_money = 0.0
            for line in order.cost_line_ids:
                total_money += line.price_total
            order.total_money = total_money

    @api.depends('state', 'location_start', 'location_end')
    def _get_location_now(self):
        for order in self:
            if order.state == 'draft' and order.location_start:
                order.update({'location_now': order.location_start.name})
            elif order.state == 'doing' and order.location_start and order.location_end and order.transport_method:
                order.update({'location_now': order.location_start.name + order.transport_method.name + u'至' + order.location_end.name})
            elif (order.state == 'done' or order.state == 'closed') and order.location_end:
                order.update({'location_now': order.location_end.name})