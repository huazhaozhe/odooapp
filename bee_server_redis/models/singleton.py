# -*- coding: utf-8 -*-

# @Time : 2019/04/27 10:08
# @Author : zhe
# @File : singleton.py
# @Software: PyCharm

from copy import deepcopy


def singleton(mothed='class', key_list=[]):
    '''
    2种单例模式:
    1. 一种是一个类就一个实例,即通常的单例模式:

    @singleton(mothed='class')
    class Example():
        def __init__(self, attr1=None, attr2=None):
            self.attr1 = attr1
            self.attr2 = attr2

    instance1 = Example('attr1', 'attr2')
    instance2 = Example('attr1', 'attr2')
    instance3 = Example('attr3', 'attr4')

    则instance1 is instance2 为True, 且instance1 is instance3 为True

    2. 另一种是根据实例的属性单例模式,即实例中由key_list指定属性的值相同的实例只有一个,这里实例的属性和值取实例__dict__来判断

    @singleton(mothed='attr')
    class Example():
        def __init__(self, attr1=None, attr2=None):
            self.attr1 = attr1
            self.attr2 = attr2
    instance1 = Example('attr1', 'attr2')
    instance2 = Example('attr1', 'attr2')
    instance3 = Example('attr3', 'attr4')

    则instance1 is instance2 为True, 且instance1 is instance3 为False

    bool(key_list)为False时检查实例__dict__中所有的值,否则只检查key_list中的属性：

    @singleton(mothed='attr', key_list=['attr1'])
    class Example():
        def __init__(self, attr1=None, attr2=None):
            self.attr1 = attr1
            self.attr2 = attr2
    instance1 = Example('attr1', 'attr2')
    instance2 = Example('attr1', 'attr2')
    instance3 = Example('attr1', 'attr4')
    instance4 = Example('attr5', 'attr2')

    则instance1 is instance2 为True, instance1 is instance3 为True, instance1 is instance4 为False

    3. python内置的数据类型(int, float, list, dict， set等)没有__dict__，但是继承这些内置数据类型有__dict__
    list_instance = [1, 'name']
    class Example(list):
        pass
    instance = Example()
    list_instance没有__dict__, instance有__dict__

    :param mothed: 'class'或者'attr'
    :param key_list: list
    :return:
    '''

    def main(cls):
        instances_class = {}
        instances_attr = {
            'attr': [],
            'instances': [],
        }

        def wrapper(*args, **kwargs):
            if mothed == 'class':
                if cls not in instances_class:
                    instances_class[cls] = cls(*args, **kwargs)
                return instances_class[cls]
            elif mothed == 'attr':
                instance = cls(*args, **kwargs)
                if key_list:
                    kw = {}
                    for key in key_list:
                        if key in instance.__dict__:
                            kw[key] = instance.__dict__[key]
                else:
                    kw = deepcopy(instance.__dict__)
                if kw in instances_attr['attr']:
                    del instance
                else:
                    instances_attr['attr'].append(kw)
                    instances_attr['instances'].append(instance)
                return instances_attr['instances'][instances_attr['attr'].index(kw)]
            else:
                return cls(*args, **kwargs)

        return wrapper

    return main
