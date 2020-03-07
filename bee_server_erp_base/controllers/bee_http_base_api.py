#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/5/14 9:25
# @Author  : zhe
# @Email   :
# @Site    : 
# @File    : api.py
# @Software: PyCharm


import json
from odoo import http


class BeeServerHttpControllerBase():
    condition = {
        'many2one': '=',
        'many2many': 'in',
        'one2many': 'in',
        'char': 'ilike',
        'integer': '=',
        'float': '=',
        'boolean': '=',
        'text': 'ilike',
        'selection': '=',
    }

    def get_model_fields(self):
        if not hasattr(self, 'model_fields'):
            fields = http.request.env['ir.model.fields'].sudo().search([
                ('model', '=', self.ref_model)
            ])
            self.model_fields = {}
            for field in fields.filtered(lambda x: x.name in self.default_fields):
                self.model_fields[field.name] = {
                    'condition': self.condition[field.ttype],
                    'ttype': field.ttype,
                    'relation': field.relation,
                    'relation_field': field.relation_field,
                }

    def detail(self, **kw):
        if http.request.httprequest.method != 'POST':
            result = {
                'code': 0,
                'message': '请求方法错误',
            }
            return json.dumps(result)
        self.get_model_fields()
        if 'id' not in kw:
            result = {
                'code': 0,
                'message': '缺少记录的ID'
            }
            return json.dumps(result)
        else:
            try:
                id = int(kw['id'])
            except:
                result = {
                    'code': 0,
                    'message': '错误的ID %s' % kw['id'],
                }
                return json.dumps(result)
        data = http.request.env[self.ref_model].sudo().search_read([('id', '=', id)], fields=self.default_fields)
        if data:
            data = self.del_empty(data[0])
            for key in data:
                if data[key] and key in self.default_fields and self.model_fields[key]['ttype'] in ['many2one',
                                                                                                    'many2many',
                                                                                                    'one2many']:
                    fields = http.request.env['ir.model.fields'].sudo().search([
                        ('model', '=', self.model_fields[key]['relation']),
                        ('ttype', 'not in', ['many2one', 'many2many', 'one2many', 'datetime']),
                        ('name', 'not in', ['create_uid', 'create_date', 'write_uid', 'write_date', '__last_update'])
                    ]).mapped('name')
                    val = data[key][0] if self.model_fields[key]['ttype'] == 'many2one' else data[key]
                    res = http.request.env[self.model_fields[key]['relation']].sudo().search_read(
                        [('id', self.model_fields[key]['condition'], val)], fields=fields)
                    data[key] = self.del_empty(res)
            result = {
                'code': 1,
                'message': '成功',
                'object': data,
            }
        else:
            result = {
                'code': 0,
                'message': 'ID为 %s 的记录不存在!' % kw['id']
            }
        return json.dumps(result)

    def list(self, **kw):
        if http.request.httprequest.method != 'POST':
            result = {
                'code': 0,
                'message': '请求方法错误',
            }
            return json.dumps(result)
        self.get_model_fields()
        domain = []
        if 'id' in kw:
            try:
                id = int(kw['id'])
            except:
                result = {
                    'code': 0,
                    'message': '错误的ID %s' % kw['id'],
                }
                return json.dumps(result)
            domain.append(('id', '=', id))
        else:
            for key in kw:
                if key in self.default_fields:
                    field = self.model_fields[key]
                    val = self.format_val(kw[key], field['ttype'], field['relation'])
                    if val['error']:
                        result = {
                            'code': 0,
                            'message': '创建失败! %s 的值 %s 不正确' % (key, kw[key])
                        }
                        return json.dumps(result)
                    elif val['flag']:
                        if self.model_fields[key] == 'boolean':
                            if kw[key] == 'true':
                                domain.append((key, self.model_fields[key]['condition'], True))
                            elif kw[key] == 'false':
                                domain.append((key, self.model_fields[key]['condition'], False))
                            else:
                                domain.append((key, self.model_fields[key]['condition'], True))
                                domain.append((key, self.model_fields[key]['condition'], False))
                        else:
                            domain.append((key, self.model_fields[key]['condition'], val['val']))
                else:
                    result = {
                        'code': 0,
                        'message': '查询失败! 未知的 %s 的值 %s' % (key, kw[key])
                    }
                    return json.dumps(result)
        res = http.request.env[self.ref_model].sudo().search_read(domain, fields=self.default_fields)
        if res:
            res = self.del_empty(res)
            result = {
                'code': 1,
                'message': '成功',
                'object': res,
            }
        elif 'id' in kw:
            result = {
                'code': 0,
                'message': 'ID为 %s 的记录不存在!' % kw['id']
            }
        else:
            result = {
                'code': 1,
                'message': '成功',
                'object': [],
            }
        return json.dumps(result)

    def edit(self, **kw):
        if http.request.httprequest.method != 'POST':
            result = {
                'code': 0,
                'message': '请求方法错误',
            }
            return json.dumps(result)
        self.get_model_fields()
        if 'id' not in kw:
            result = {
                'code': 0,
                'message': '缺少记录的ID'
            }
            return json.dumps(result)
        else:
            try:
                id = int(kw['id'])
            except:
                result = {
                    'code': 0,
                    'message': '错误的ID %s' % kw['id'],
                }
                return json.dumps(result)
        res = http.request.env[self.ref_model].sudo().search([('id', '=', id)])
        if res:
            data = {}
            for key in kw:
                if key == 'id':
                    continue
                elif key in self.default_fields:
                    field = self.model_fields[key]
                    val = self.format_val(kw[key], field['ttype'], field['relation'])
                    if val['error']:
                        result = {
                            'code': 0,
                            'message': '修改失败! %s 的值 %s 不正确' % (key, kw[key])
                        }
                        return json.dumps(result)
                    elif val['flag']:
                        if field['ttype'] in ['one2many', 'many2many']:
                            val['val'] = [(6, 0, val['val'])]
                        data[key] = val['val']
                else:
                    result = {
                        'code': 0,
                        'message': '修改失败! 未知的 %s 的值 %s' % (key, kw[key])
                    }
                    return json.dumps(result)
            try:
                res.write(data)
                result = {
                    'code': 1,
                    'message': '修改成功',
                }
            except BaseException as e:
                print(e)
                result = {
                    'code': 0,
                    'message': '修改失败 %s' % e,
                }
        else:
            result = {
                'code': 0,
                'message': 'ID为 %s 的记录不存在!' % kw['id']
            }
        return json.dumps(result)

    def delete(self, **kw):
        if http.request.httprequest.method != 'POST':
            result = {
                'code': 0,
                'message': '请求方法错误',
            }
            return json.dumps(result)
        self.get_model_fields()
        if 'id' not in kw:
            result = {
                'code': 0,
                'message': '缺少记录的ID'
            }
            return json.dumps(result)
        else:
            try:
                id = int(kw['id'])
            except:
                result = {
                    'code': 0,
                    'message': '错误的ID %s' % kw['id'],
                }
                return json.dumps(result)
        res = http.request.env[self.ref_model].sudo().search([('id', '=', id)])
        if res:
            try:
                res.unlink()
                result = {
                    'code': 1,
                    'message': '删除成功',
                }
            except:
                result = {
                    'code': 0,
                    'message': '删除失败',
                }
        else:
            result = {
                'code': 0,
                'message': 'ID为 %s 的记录不存在!' % kw['id']
            }
        return json.dumps(result)

    def create(self, **kw):
        if http.request.httprequest.method != 'POST':
            result = {
                'code': 0,
                'message': '请求方法错误',
            }
            return json.dumps(result)
        self.get_model_fields()
        if 'id' in kw:
            result = {
                'code': 0,
                'message': '创建记录不接受ID参数!'
            }
            return json.dumps(result)
        else:
            data = {}
            for key in kw:
                if key in self.default_fields:
                    field = self.model_fields[key]
                    val = self.format_val(kw[key], field['ttype'], field['relation'])
                    if val['error']:
                        result = {
                            'code': 0,
                            'message': '创建失败! %s 的值 %s 不正确' % (key, kw[key])
                        }
                        return json.dumps(result)
                    elif val['flag']:
                        if field['ttype'] in ['one2many', 'many2many']:
                            val['val'] = [(6, 0, val['val'])]
                        data[key] = val['val']
                else:
                    result = {
                        'code': 0,
                        'message': '创建失败! 未知的 %s 的值 %s' % (key, kw[key])
                    }
                    return json.dumps(result)
            try:
                res = http.request.env[self.ref_model].sudo().create(data)
                result = {
                    'code': 1,
                    'message': '创建成功!',
                    'object': {
                        'id': res.id,
                    }
                }
            except BaseException as e:
                result = {
                    'code': 0,
                    'message': '创建失败! %s' % e
                }
        return json.dumps(result)

    def format_val(self, val, ttype, model):
        flag = False
        error = False
        if ttype in ['char', 'text', 'selection']:
            try:
                val = str(val)
                flag = True
            except:
                error = True
        elif val in ['', ]:
            pass
        elif ttype in ['float', 'monetary']:
            try:
                val = float(val)
                flag = True
            except:
                error = True
        elif ttype == 'integer':
            try:
                val = int(val)
                flag = True
            except:
                error = True
        elif ttype == 'many2one' and model:
            try:
                val = int(val)
            except:
                error = True
            res = http.request.env[model].sudo().search([('id', '=', val)])
            if res:
                val = res[0].id
                flag = True
            else:
                error = True
        elif ttype in ['one2many', 'many2many'] and model:
            try:
                val = eval(val)
                assert type(val) is list
                assert all(type(id) is int for id in val) is True
                res = http.request.env[model].sudo().search([('id', 'in', val)])
                if res:
                    val = res.ids
                    flag = True
                else:
                    error = True
            except:
                error = True
        else:
            error = True
        return {
            'val': val,
            'flag': flag,
            'error': error
        }

    def del_empty(self, val):
        if type(val) is list:
            for i, element in enumerate(val):
                if element in [None, False]:
                    val[i] = ''
                elif type(val[i]) in [list, dict]:
                    val[i] = self.del_empty(val[i])
        elif type(val) is dict:
            for k in val:
                if val[k] in [None, False]:
                    val[k] = ''
                elif type(val[k]) in [list, dict]:
                    val[k] = self.del_empty(val[k])
        return val
