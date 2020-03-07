# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
# from odoo.addons import decimal_precision as dp
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError

class BeeTransportContract(models.Model):
    _name = 'bee.server.transport.contract'
    # _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char('运输合同单', index=True, copy=False, default='New', track_visibility='onchange')
    origin = fields.Char(string='合同号', track_visibility='onchange')
    purchase_id = fields.Many2one('purchase.order', string='关联采购单', track_visibility='onchange')
    sale_id = fields.Many2one('sale.order', string='关联销售单', track_visibility='onchange')
    type = fields.Char('合同类型')
    product_id = fields.Many2one('product.product', string='产品', track_visibility='onchange')
    product_qty = fields.Float(string='订单数量', track_visibility='onchange',
                               digits=(16, 2))
    location_start = fields.Many2one('bee.server.transport.location', string='起点', track_visibility='onchange')
    location_end = fields.Many2one('bee.server.transport.location', string='终点', track_visibility='onchange')
    company_id = fields.Many2one('res.company', '公司')
    line_ids = fields.One2many('bee.server.transport.order.line', 'contract_id', string='在途信息')
    location_ids = fields.One2many('bee.server.transport.contract.location', 'contract_id', string='位置信息')
    state = fields.Selection([
        ('draft', '草稿'),
        ('doing', '进行中'),
        ('done', '已完成'),
        ('cancel', '取消'),
    ], string='状态', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    @api.multi
    @api.depends('name', 'contract')
    def name_get(self):
        val = []
        for r in self:
            if r.name and r.origin:
                val.append((r.id, (r.name[-4:] + ': ' + (r.origin[-4:] or _('Default')))))
            else:
                val.append((r.id, 'TC' + str(r.id)))
        return val

    @api.onchange('sale_id', 'purchase_id')
    def _get_origin(self):
        for r in self:
            if r.sale_id:
                r.update({'origin': r.sale_id.name})
            elif r.purchase_id:
                r.update({'origin': r.purchase_id.name})

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('origin', operator, name)]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()

    @api.multi
    def button_done(self):
        # self.check_contract_to_order()
        self.write({'state': 'done'})
        return {}

    @api.multi
    def check_contract_to_order(self):
        """如果客户不走正常流程，而是手动创建单据，根据合同号反推采购/销售原单据。同时做一些验证判定。"""
        if self.purchase_id or self.sale_id:
            return
        type = '采购'
        origin = self.sudo().env['purchase.order'].search([('name', '=', self.origin)])

        if len(origin) > 1:
            raise ValidationError(_('多张同名的采购单，请检查或上报至系统管理员。'))

        if len(origin) == 0:
            type = u'销售'
            origin = self.sudo().env['sale.order'].search([('name', '=', self.origin)])

            if len(origin) > 1:
                raise ValidationError(_('多张同名的销售单，请检查或上报至系统管理员。'))

        if len(origin) == 0:
            raise ValidationError(_('未找到合同号 %s 对应的采购或销售单，请检查或上报至系统管理员。' % self.origin))

        if type == u'采购':
            self.purchase_id = origin.id
        else:
            self.sale_id = origin.id
        self.type = type

    @api.multi
    def button_doing(self):
        if (self.location_start.id is False) or (self.location_end.id is False):
            raise ValidationError(_(u'请选择起点与终点，以将合同单纳入运输流程。'))
        # self.check_contract_to_order()
        # if not self.origin:
        #     raise ValidationError(_(u'合同号非空。'))
        self.write({'state': 'doing'})
        return {}

    def update_location(self):
        """根据当前合同单据的现有在途行，来更新现有位置行"""
        if self.id is False:
            return
        res = self.env['mingda_trans_ext.order.line'].search([('contract_id', '=', self.id)])

        # 根据当前合同单据的现有在途行res，来更新现有位置行
        # res:在途模型[order.line]
        location_dict = {}
        for r in res:
            try:
                if r.order_id:
                    if r.order_id.state == 'draft':
                        location = r.order_id.location_start.name
                    elif r.order_id.state == 'done':
                        location = r.order_id.location_end.name
                    else:
                        location = r.order_id.location_start.name + r.order_id.transport_method.name + u'至' + r.order_id.location_end.name
                    num = r.merge_qty

                    if location not in location_dict:
                        location_dict[location] = num
                    else:
                        location_dict[location] += num
            except Exception as e:
                print('update_location', e)
        if not location_dict:
            return
        # 根据更新改变的数据到
        l = []
        for ld in location_dict:
            l.append(
                self.env['mingda_trans_ext.contract.location'].create({
                    'location': ld, 'contract_id': self.id, 'qty': location_dict[ld]
                }).id
            )
        self.update({'location_ids': [(6, 0, l)]})

    @api.multi
    def unlink(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('已经开始运输的运输合同单不允许删除！'))
        return super(BeeTransportContract, self).unlink()

class BeeContractLocation(models.Model):
    _name = 'bee.server.transport.contract.location'

    contract_id = fields.Many2one('bee.server.transport.contract', string='运输合同单')
    product_id = fields.Many2one('product.product', related='contract_id.product_id', string='产品', store=True)
    location = fields.Char('当前位置')
    qty = fields.Float('数量', digits=(16, 2))

