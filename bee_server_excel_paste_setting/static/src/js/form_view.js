odoo.define('bee.server.excel.paste.setting', function (require) {
    var FormController = require('web.FormController');
    var session = require('web.session');

    setting_model = [];

    FormController.include({
        start: function () {
            var self = this;
            var def = this._super();
            this.$el.on('mousedown.formBlur', function () {
                self.__clicked_inside = true;
            });
            self.get_setting_model();
            this.$el.on('paste', function (e) {
                var model = self.getUrlParam('model');
                var id = self.getUrlParam('id');
                var value = setting_model.includes(model);
                console.log(model);
                console.log(id);
                console.log(value);
                if (model != '' && id != '' && value) {
                    event.preventDefault();
                    var data = null;
                    var clipboardData = window.clipboardData || e.originalEvent.clipboardData; // IE || chrome
                    data = clipboardData.getData('Text');
                    console.log(data);
                    console.log(data.replace(/\t/g, '\\t').replace(/\n/g, '\\n')); //data转码
                    event.stopPropagation()
                    session.rpc('/excel/paste', {
                        data: data,
                        url: window.location.hash,
                        real_url: window.location.href
                    }).then(function (result) {
                        if (result == 'no') {
                            alert('excel输入错误,请检查');
                        }
                        if (result == 'yes') {
                            window.location.reload()
                        }
                    });
                }
            });
            return def
        },
        get_setting_model: function () {
            this._rpc({
                model: 'bee.server.excel.paste.setting',
                method: 'get_setting_model',
                args: [],
                kwargs: {context: session.user_context},
            }).then(function (result) {
                setting_model = result;
                console.log(setting_model);
            })
        },
        getUrlParam: function (paraName) {
            var url = document.location.toString();
            if (url.indexOf('?') != -1) {
                url = url.replace('#', '&');
            } else {
                url = url.replace('#', '?');
            }
            var arrObj = url.split("?");

            if (arrObj.length > 1) {
                var arrPara = arrObj[1].split("&");
                var arr;

                for (var i = 0; i < arrPara.length; i++) {
                    arr = arrPara[i].split("=");

                    if (arr != null && arr[0] == paraName) {
                        return arr[1];
                    }
                }
                return "";
            } else {
                return "";
            }
        }
    });

});