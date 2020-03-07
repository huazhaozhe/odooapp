# -*- coding: utf-8 -*-
from odoo import http

# class BeeServerErpBase(http.Controller):
#     @http.route('/bee_server_erp_base/bee_server_erp_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bee_server_erp_base/bee_server_erp_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bee_server_erp_base.listing', {
#             'root': '/bee_server_erp_base/bee_server_erp_base',
#             'objects': http.request.env['bee_server_erp_base.bee_server_erp_base'].search([]),
#         })

#     @http.route('/bee_server_erp_base/bee_server_erp_base/objects/<model("bee_server_erp_base.bee_server_erp_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bee_server_erp_base.object', {
#             'object': obj
#         })