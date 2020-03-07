# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import xlwt
import io
import re

from odoo import models, fields, api
from odoo.tools import float_is_zero, float_compare, float_round, DEFAULT_SERVER_DATE_FORMAT
from odoo.http import request, content_disposition
from odoo.exceptions import UserError
from odoo.tools.translate import _


class BeeTransportReport(models.Model):
    _name = 'bee.server.transport.report'

    def _get_destination(self, location):
        res = self.sudo().env['bee.server.transport.location'].search([])
        for r in res:
            if location == r.name:
                return r.purchase_destination, r.sale_destination
        return False, False

    @api.model
    def get_purchase_transport_passage_report(self, company_id=None, origin=None, product=None, bill=None,
                                              statistical='1'):
        # for contract_id in self.sudo().env['bee.server.transport.contract'].search([]):
        #     try:
        #         contract_id.check_contract_to_order()
        #     except:
        #         # contract_id.unlink()
        #         pass

        domain = []
        if product:
            domain.append(('product_id.name', 'like', product))
        if statistical in ['1', '2']:
            if company_id:
                domain.append(('company_id', '=', int(company_id)))
            if origin:
                domain.append(('origin', 'like', origin))
            domain.append(('state', '!=', 'draft'))
            domain.append(('state', '!=', 'cancel'))
            domain.append(('purchase_id', '!=', False))
        elif statistical == '3':
            domain.append(('order_id.state', '!=', 'draft'))
            domain.append(('order_id.state', '!=', 'cancel'))
            domain.append(('contract_id.purchase_id', '!=', False))
            if company_id:
                domain.append(('contract_id.company_id', '=', int(company_id)))
            if origin:
                domain.append(('contract_id.origin', 'like', origin))
            if bill:
                domain.append(('bill', '=', bill))
            else:
                domain.append(('bill', '!=', False))
            bill_values = []
            bills = self.sudo().env['bee.server.transport.order.line'].search(domain)
            amount_bill = 0.0
            for bill in bills:
                value = {}
                value['bill'] = bill.bill
                value['product'] = bill.product_id.name
                value['origin'] = bill.contract_id.origin
                value['partner'] = bill.contract_id.purchase_id.partner_id.name
                value['merge_qty'] = '%.3f' % bill.merge_qty
                value['location'] = bill.location_now
                amount_bill += bill.merge_qty
                bill_values.append(value)
            amount_bill = '%.3f' % amount_bill
            return (bill_values or [{
                'product': '',
                'type': '',
            }], amount_bill)
        else:
            return UserError(_('请选择统计口径！'))

        values = []
        amount_passage = 0.0
        amount_overseas = 0
        amount_total = 0
        location = []
        amount_location_num = {}
        contract_ids = self.sudo().env['bee.server.transport.contract'].search(domain)
        product_dict = {}
        for contract_id in contract_ids:
            # contract_id.check_contract_to_order()
            line_value = {
                'passage': 0.0,
            }
            if contract_id.product_id.name not in product_dict:
                product_dict[contract_id.product_id.name] = {
                    'name': contract_id.product_id.name,
                    'total': 0.0,
                    'overseas': 0.0,
                    'passage': 0.0,
                    'locations': {},
                }
            product_dict[contract_id.product_id.name]['total'] += contract_id.product_qty
            line_value['product'] = contract_id.product_id.name
            line_value['type'] = contract_id.type
            line_value['partner'] = contract_id.purchase_id.partner_id.name
            line_value['origin'] = contract_id.origin
            line_value['num'] = contract_id.product_qty

            location_dict_lists = self.sudo().env['bee.server.transport.order.line'].read_group(
                domain=[
                    ('contract_id', '=', contract_id.id),
                    # ('order_id.state', '!=', 'draft'),
                    ('order_id.state', '!=', 'cancel'),
                ],
                fields=['location_now', 'merge_qty'],
                groupby=['location_now']
            )
            for location_dict in location_dict_lists:
                if location_dict['location_now'] not in location:
                    location.append(location_dict['location_now'])
                    amount_location_num[location_dict['location_now']] = 0
                if location_dict['location_now'] not in product_dict[contract_id.product_id.name]['locations']:
                    product_dict[contract_id.product_id.name]['locations'][location_dict['location_now']] = 0.0
                line_value[location_dict['location_now']] = location_dict['merge_qty']
                product_dict[contract_id.product_id.name]['locations'][location_dict['location_now']] += location_dict[
                    'merge_qty']
                amount_location_num[location_dict['location_now']] += location_dict['merge_qty']
                if location_dict['location_now'] != contract_id.location_end.name:
                    line_value['passage'] += location_dict['merge_qty']
                    product_dict[contract_id.product_id.name]['passage'] += location_dict['merge_qty']
                line_value[location_dict['location_now']] = '%.3f' % line_value[location_dict['location_now']]
            line_value['start_num'] = sum([r.start_wet_weight for r in contract_id.line_ids if
                                           r.order_id.location_start.id == contract_id.location_start.id])
            line_value['overseas'] = contract_id.product_qty - line_value['start_num']
            if abs(line_value['overseas']) < abs(line_value['num'] * 0.03) or line_value['overseas'] < 0:
                line_value['overseas'] = 0.0
            product_dict[contract_id.product_id.name]['overseas'] += line_value['overseas']
            amount_total += line_value['num']
            amount_overseas += line_value['overseas']
            line_value['passage'] += line_value['overseas']
            product_dict[contract_id.product_id.name]['passage'] += line_value['overseas']
            line_value['overseas'] = '%.3f' % line_value['overseas']
            line_value['num'] = '%.3f' % line_value['num']
            amount_passage += line_value['passage']
            line_value['passage'] = '%.3f' % line_value['passage']
            values.append(line_value)

        amount_location_num = {k: '%.3f' % v for k, v in amount_location_num.items()}
        amount_total = '%.3f' % amount_total
        amount_overseas = '%.3f' % amount_overseas
        sys_location = self.sudo().env['bee.server.transport.location'].search([])
        sys_method = self.sudo().env['bee.server.transport.method'].search([])
        sys_location = {sl.name: float(sl.purchase_andsingle) for sl in sys_location}
        sys_method = [m.name for m in sys_method]

        location = self.sort_location(location, sys_location, sys_method)
        if statistical == '1':
            product_list = []
            for k1, v1 in product_dict.items():
                for k2 in v1['locations']:
                    v1['locations'][k2] = '%.3f' % v1['locations'][k2]
                v1['total'] = '%.3f' % v1['total']
                v1['overseas'] = '%.3f' % v1['overseas']
                v1['passage'] = '%.3f' % v1['passage']
                product_list.append(v1)
            return (product_list or [{
                'product': '',
                'type': '',
            }], amount_total, amount_passage, amount_overseas, 7.22, location, amount_location_num)
        elif statistical == '2':
            return (values or [{
                'product': '',
                'type': '',
            }], amount_total, amount_passage, amount_overseas, 7.22, location, amount_location_num)

    @api.model
    def get_purchase_transport_cost_report(self, origin=None, order=None, product=None, loss_type=None, vander=None,
                                           statistical='1'):
        domain = []
        if product:
            domain.append(('product_id.name', 'like', product))
        if statistical == '1':
            # domain.append(('state', '=', 'done'))
            domain.append(('contract_id.purchase_id', '!=', False))
            if vander:
                domain.append(('order_id.vander.name', 'like', vander))
            if origin:
                domain.append(('contract_id.origin', 'like', origin))
            if order:
                domain.append(('order_id.name', '=', order))
            if loss_type:
                domain.append(('loss_type', '=', loss_type))
        elif statistical == '2':
            domain.append(('purchase_id', '!=', False))
            if origin:
                domain.append(('origin', 'like', origin))
        else:
            return UserError(_('请选择统计口径！'))

        total_start_wet_weight = 0.0
        total_arrive_wet_weight = 0.0
        total_start_quality = 0.0
        total_arrive_quality = 0.0
        total_start_dry_weight = 0.0
        total_arrive_dry_weight = 0.0
        total_loss_dry = 0.0
        total_loss_quality = 0.0
        total_loss_wet = 0.0
        total_summary_price = 0.0

        values = []
        if statistical == '2':
            contract_ids = self.sudo().env['bee.server.transport.contract'].search(domain)
            for contract_id in contract_ids:
                value = {
                    'start_wet_weight': 0,
                    'arrive_wet_weight': 0,
                    'start_quality': 0,
                    'arrive_quality': 0,
                    'start_dry_weight': 0,
                    'arrive_dry_weight': 0,
                    'summary_price': 0,
                    'loss_wet': 0,
                    'loss_quality': 0,
                    'loss_dry': 0,
                }
                value['product'] = contract_id.product_id.name
                value['origin'] = contract_id.origin
                res = self.sudo().env['bee.server.transport.order.line'].search(
                    [('contract_id', '=', contract_id.id), ('state', '!=', 'draft')])
                for r in res:
                    value['start_wet_weight'] += r.start_wet_weight
                    value['arrive_wet_weight'] += r.arrive_wet_weight
                    value['start_quality'] += r.start_quality
                    value['arrive_quality'] += r.arrive_quality
                    value['start_dry_weight'] += r.start_dry_weight
                    value['arrive_dry_weight'] += r.arrive_dry_weight
                    value['summary_price'] += r.summary_price
                    value['loss_wet'] += r.arrive_wet_weight - r.start_wet_weight if r.state in ['done', 'closed'] else 0
                    value['loss_quality'] += r.arrive_quality - r.start_quality if r.state in ['done', 'closed'] else 0
                    value['loss_dry'] += r.arrive_dry_weight - r.start_dry_weight if r.state in ['done', 'closed'] else 0
                    total_start_wet_weight += r.start_wet_weight
                    total_arrive_wet_weight += r.arrive_wet_weight
                    total_start_quality += r.start_quality
                    total_arrive_quality += r.arrive_quality
                    total_start_dry_weight += r.start_dry_weight
                    total_arrive_dry_weight += r.arrive_dry_weight
                    total_loss_dry += r.arrive_dry_weight - r.start_dry_weight if r.state in ['done', 'closed'] else 0
                    total_loss_quality += r.arrive_quality - r.start_quality if r.state in ['done', 'closed'] else 0
                    total_loss_wet += r.arrive_wet_weight - r.arrive_wet_weight if r.state in ['done', 'closed'] else 0
                values.append(value)
        else:
            lines = self.sudo().env['bee.server.transport.order.line'].search(domain)
            for line in lines:
                data_dict = {}
                data_dict['origin'] = line.contract_id.origin
                data_dict['order'] = line.order_id.name
                data_dict['vander'] = line.order_id.vander.name
                data_dict['product'] = line.product_id.name
                data_dict['start_wet_weight'] = line.start_wet_weight
                data_dict['arrive_wet_weight'] = line.arrive_wet_weight
                data_dict['start_quality'] = line.start_quality
                data_dict['arrive_quality'] = line.arrive_quality
                data_dict['start_dry_weight'] = line.start_dry_weight
                data_dict['arrive_dry_weight'] = line.arrive_dry_weight
                data_dict['loss_wet'] = line.arrive_wet_weight - line.start_wet_weight
                data_dict['loss_quality'] = line.arrive_quality - line.start_quality
                data_dict['loss_dry'] = line.arrive_dry_weight - line.start_dry_weight
                if line.loss_type == '0':
                    data_dict['loss_type'] = '物流公司'
                elif line.loss_type == '1':
                    data_dict['loss_type'] = '我方'
                else:
                    data_dict['loss_type'] = ''
                data_dict['summary_price'] = '%.3f' % line.summary_price
                total_start_wet_weight += line.start_wet_weight
                total_arrive_wet_weight += line.arrive_wet_weight
                total_start_quality += data_dict['start_quality']
                total_arrive_quality += data_dict['arrive_quality']
                total_start_dry_weight += line.start_dry_weight
                total_arrive_dry_weight += line.arrive_dry_weight
                total_loss_wet += data_dict['loss_wet']
                total_loss_quality += data_dict['loss_quality']
                total_loss_dry += data_dict['loss_dry']
                total_summary_price += line.summary_price
                data_dict['loss_wet'] = '%.3f' % data_dict['loss_wet']
                data_dict['loss_quality'] = '%.3f' % data_dict['loss_quality']
                data_dict['loss_dry'] = '%.3f' % data_dict['loss_dry']
                values.append(data_dict)
        total_start_wet_weight = '%.3f' % total_start_wet_weight
        total_arrive_wet_weight = '%.3f' % total_arrive_wet_weight
        total_start_quality = '%.3f' % total_start_quality
        total_arrive_quality = '%.3f' % total_arrive_quality
        total_start_dry_weight = '%.3f' % total_start_dry_weight
        total_arrive_dry_weight = '%.3f' % total_arrive_dry_weight
        total_loss_wet = '%.3f' % total_loss_wet
        total_loss_quality = '%.3f' % total_loss_quality
        total_loss_dry = '%.3f' % total_loss_dry
        total_summary_price = '%.3f' % total_summary_price
        return (values or [{
            'product': '',
            'type': '',
        }], total_start_wet_weight, total_start_quality, total_start_dry_weight,
                total_arrive_wet_weight, total_arrive_quality, total_arrive_dry_weight,
                total_loss_wet, total_loss_quality, total_loss_dry, total_summary_price)

    @staticmethod
    def sort_location(locations, sys_location, sys_method):
        finish_location_dict = {}
        for l in locations:
            if l and '至' in l:
                l_sp = l.split('至')
                for ssm in sys_method:
                    l_sp[0] = l_sp[0].replace(ssm, '')
                finish_location_dict[l] = (sys_location[l_sp[0]] + sys_location[l_sp[1]]) / 2.0
            elif l in sys_location:
                finish_location_dict[l] = sys_location[l]
        # return finish_location_dict
        res = sorted(finish_location_dict.items(), key=lambda x: x[1], reverse=False)
        return [r[0] for r in res]

    @api.model
    def get_product_category_data(self):
        result = self.env['product.category'].search_read([], ['name'])
        return result

    @api.model
    def get_product_data(self, product_type=None):
        result = self.env['product.product'].search_read([], ['name'])
        return result

    @api.model
    def get_state_data(self):
        return [
            {"id": 0, "name": "进行中"},
            {"id": 1, "name": "已完成"},
        ]

    @api.model
    def get_company_data(self):
        result = self.env['res.company'].search_read([], ['name'])
        return result
