# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError

_logger = logging.getLogger(__name__)



class BeeServerRedisSetting(models.Model):
    _name = 'bee.server.redis.setting'

    name = fields.Char(string='Redis Name', required=True)
    host = fields.Char(string='Redis Host', default='127.0.0.1')
    port = fields.Char(string='Redis Port', default='6379')
    requirepass = fields.Char(string='Redis Requirepass')
    activate = fields.Boolean(string='有效', default=True)

    @api.constrains('name', 'host', 'port')
    def _constrains_host_port(self):
        setting = self.sudo().search([
            ('id', '!=', self.id),
            ('host', '=', self.host),
            ('port', '=', self.port),
            ('activate', '=', True)
        ])
        if len(setting) != 0:
            raise UserError('已存在host 为 %s port 为 %s 的Redis设置!' % (self.host, self.port))
        setting = self.sudo().search([
            ('id', '!=', self.id),
            ('name', '=', self.name)
        ])
        if len(setting) != 0:
            raise UserError('Name 为 %s 的设置已经存在!' % self.name)