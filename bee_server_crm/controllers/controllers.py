# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.custom.CommonAddons.bee_server_erp_base.controllers.bee_http_base_api import BeeServerHttpControllerBase

auth = 'none'


# auth = 'user'

class BeeServerCrmCustomerTypeApi(http.Controller, BeeServerHttpControllerBase):
    ref_model = 'bee.server.customer.type'
    default_fields = ['id', 'name', 'parten_type_id']

    @http.route('/crm/customerType/list', auth=auth, csrf=False, cors='*')
    def list(self, **kw):
        return super(BeeServerCrmCustomerTypeApi, self).list(**kw)

    @http.route('/crm/customerType/edit', auth=auth, csrf=False, cors='*')
    def edit(self, **kw):
        return super(BeeServerCrmCustomerTypeApi, self).edit(**kw)

    @http.route('/crm/customerType/delete', auth=auth, csrf=False, cors='*')
    def delete(self, **kw):
        return super(BeeServerCrmCustomerTypeApi, self).delete(**kw)

    @http.route('/crm/customerType/create', auth=auth, csrf=False, cors='*')
    def create(self, **kw):
        return super(BeeServerCrmCustomerTypeApi, self).create(**kw)

    @http.route('/crm/customerType/detail', auth=auth, csrf=False, cors='*')
    def detail(self, **kw):
        return super(BeeServerCrmCustomerTypeApi, self).detail(**kw)


class BeeServerCrmCustomerContactApi(http.Controller, BeeServerHttpControllerBase):
    ref_model = 'bee.server.customer.contact'
    default_fields = ['id', 'name', 'sex', 'type_ids', 'phone', 'tel', 'email', 'birthday', 'job_profile', 'note', 'grade',
                      'customer_id', 'location']

    @http.route('/crm/customerContact/list', auth=auth, csrf=False, cors='*')
    def list(self, **kw):
        return super(BeeServerCrmCustomerContactApi, self).list(**kw)

    @http.route('/crm/customerContact/edit', auth=auth, csrf=False, cors='*')
    def edit(self, **kw):
        return super(BeeServerCrmCustomerContactApi, self).edit(**kw)

    @http.route('/crm/customerContact/delete', auth=auth, csrf=False, cors='*')
    def delete(self, **kw):
        return super(BeeServerCrmCustomerContactApi, self).delete(**kw)

    @http.route('/crm/customerContact/create', auth=auth, csrf=False, cors='*')
    def create(self, **kw):
        return super(BeeServerCrmCustomerContactApi, self).create(**kw)


class BeeServerCrmCustomerApi(http.Controller, BeeServerHttpControllerBase):
    ref_model = 'bee.server.customer'
    default_fields = ['id', 'company_id', 'name', 'location', 'first_type_ids', 'second_type_ids', 'contact_ids', 'state']

    @http.route('/crm/customer/list', auth=auth, csrf=False, cors='*')
    def list(self, **kw):
        return super(BeeServerCrmCustomerApi, self).list(**kw)

    @http.route('/crm/customer/edit', auth=auth, csrf=False, cors='*')
    def edit(self, **kw):
        return super(BeeServerCrmCustomerApi, self).edit(**kw)

    @http.route('/crm/customer/delete', auth=auth, csrf=False, cors='*')
    def delete(self, **kw):
        return super(BeeServerCrmCustomerApi, self).delete(**kw)

    @http.route('/crm/customer/create', auth=auth, csrf=False, cors='*')
    def create(self, **kw):
        return super(BeeServerCrmCustomerApi, self).create(**kw)

    @http.route('/crm/customer/detail', auth=auth, csrf=False, cors='*')
    def detail(self, **kw):
        return super(BeeServerCrmCustomerApi, self).detail(**kw)
