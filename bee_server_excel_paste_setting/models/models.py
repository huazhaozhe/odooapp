# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError

_logger = logging.getLogger(__name__)


class BeeServerExcelPasteSetting(models.Model):
    _name = 'bee.server.excel.paste.setting'
    _description = '粘贴配置的模型'


    model_id = fields.Many2one('ir.model', string='模型', required=True)
    model_line_field_id = fields.Many2one('ir.model.fields', string='模型的One2many字段', required=True)
    foreign_model_id = fields.Many2one('ir.model', string='明细行模型', required=True)
    foreign_model_line_field_id = fields.Many2one('ir.model.fields', string='明细行模型的Many2one字段', required=True)
    action_id = fields.Many2one('ir.actions.act_window', string='关联的action')
    name = fields.Char(string='设置的模型和字段', compute='_get_model_info')
    describe = fields.Text(string='描述')
    activate = fields.Boolean(string='有效', default=True)
    line_ids = fields.One2many('bee.server.excel.paste.setting.line', 'order_id', string='模型的字段')

    @api.constrains('model_id', 'foreign_model_id', 'model_line_field_id', 'foreign_model_line_field_id')
    def _constrains_foreign(self):
        if self.model_id.id != self.model_line_field_id.model_id.id:
            raise UserError('模型 %s 没有字段 %s !' % (self.model_id.name, self.model_line_field_id.name))
        if self.foreign_model_id.id != self.foreign_model_line_field_id.model_id.id:
            raise UserError('模型 %s 没有字段 %s !' % (self.foreign_model_id.name, self.foreign_model_line_field_id.name))
        if self.model_line_field_id.relation != self.foreign_model_line_field_id.model or self.model_line_field_id.relation_field != self.foreign_model_line_field_id.name:
            raise UserError(
                '字段 %s 和字段 %s 没有One2many的关系!' % (self.model_line_field_id.name, self.foreign_model_line_field_id.name))

    @api.constrains('action_id')
    def _constrains_action(self):
        if self.action_id and self.action_id.res_model != self.model_id.model:
            raise UserError('action与model不匹配!')

    @api.depends('model_id', 'foreign_model_id')
    def _get_model_info(self):
        for order in self:
            if order.model_id:
                order.name = order.model_id.name + '(%s:%s)_' % (
                    order.model_id.model, order.model_line_field_id.name) + order.foreign_model_id.name + '(%s:%s)_' % (
                                 order.foreign_model_id.model,
                                 order.foreign_model_line_field_id.name) + order.action_id.name + '(%s)' % order.action_id.id

    @api.model
    def get_setting_model(self):
        result = self.sudo().search([('activate', '=', True)]).mapped('model_id.model')
        return result

    @api.model
    def create(self, vals_list):
        res = super(BeeServerExcelPasteSetting, self).create(vals_list)
        print(res)
        for field in res.foreign_model_id.field_id:
            self.sudo().env['bee.server.excel.paste.setting.line'].create({
                'order_id': res.id,
                'field_id': field.id,
                'field_ttype': field.ttype,
                'field_display_name': field.field_description,
                'field_name': field.name
            })
        return res


class BeeServerExcelPasteSettingLine(models.Model):
    _name = 'bee.server.excel.paste.setting.line'
    _description = '关联的明细行'

    order_id = fields.Many2one('bee.server.excel.paste.setting')
    field_id = fields.Many2one('ir.model.fields', string='模型的字段')
    field_display_name = fields.Char(string='字段名')
    field_name = fields.Char(string='内部变量名')
    is_paste = fields.Boolean(string='可粘贴', default=False)
    is_matched = fields.Boolean(string='匹配', default=False)
    matched_key = fields.Char(string='匹配关键字')
    matched_condition = fields.Char(string='匹配条件')
    field_ttype = fields.Char(string='字段类型')
    table_header = fields.Char(string='表头匹配')
    key_word = fields.Char(string='搜索关键字')
    condition = fields.Char(string='判断条件')
    note = fields.Char(string='备注')

    @api.constrains('is_paste')
    def _constrains_is_past(self):
        for line in self:
            if line.is_paste and not line.table_header:
                raise UserError('可粘贴的字段必须设置表头!')
            if line.is_paste and line.field_ttype == 'many2one' and (not line.key_word or not line.condition):
                raise UserError('many2one字段必须设置domain匹配的字段!')

    @api.onchange('is_matched')
    def set_is_past(self):
        for line in self:
            if line.is_matched:
                line.is_paste = True

    @api.constrains('table_header')
    def _constrains_table_header(self):
        for line in self:
            table_header = line.order_id.line_ids.filtered(lambda x: x.table_header and x.id != line.id).mapped(
                'table_header')
            if line.table_header and line.table_header in table_header:
                raise UserError('表头不能够重复!')
