#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/4/26 17:05
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : redis_connection.py
# @Software: PyCharm


import logging
import redis
from odoo import http, models, fields, api, _
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
from .singleton import singleton

_logger = logging.getLogger(__name__)


@singleton(mothed='attr', key_list=['name', ])
class ConnectionPool():

    def __init__(self, name):
        redis_setting = http.request.env['bee.server.redis.setting'].sudo().search(
            [('name', '=', name), ('activate', '=', True)])
        if redis_setting:
            self.redis_setting = redis_setting
            self.host = redis_setting.host
            self.port = redis_setting.port
            self.requirepass = redis_setting.requirepass
            try:
                self.pool = redis.ConnectionPool(host=redis_setting.host, port=redis_setting.port,
                                                 password=redis_setting.requirepass)
                self.r = redis.Redis(connection_pool=self.pool)
                res = self.r.get('test')
                self.name = name
            except:
                # pass
                raise UserError('Redis name 为 %s 的连接出错!' % name)
        else:
            raise UserError('不存name为 %s 的redis配置!' % name)
            # pass
