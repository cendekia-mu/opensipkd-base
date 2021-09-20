(function( $ ){

    $.fn.PBB = function() {
        var me = $(this);
        var id = (me.attr('id') != undefined) ? me.attr('id') : '';
        var isForm = me.is('form');
        var isInputText = (!isForm && me.is('input[type="text"]'));
        var isSelect = (!isForm && me.is('select'));
        var val = isForm ? '' : me.val() || me.text;

        var defaults = {
            value: function() {
                if (isInputText || isSelect) {
                    return isInputText ? me.val() : $('option:selected', me).val();
                }
                return isForm ? '' : me.text();
            },
            setValue: function(v) {
                if (isInputText || isSelect) me.val(v);
                else if (!isForm) me.text(v);
                return this;
            },
            digitSplited: function() {
                return this.value().replace(/[^0-9.]/g, '');
            },
            digit: function() {
                return this.value().replace(/[^0-9]/g, '');
            },
            validTahun: function() {
                return (this.digit().length === 4);
            },
            validNOPEL: function() {
                /*
                var s = this.digitSplited().split('.');
                if (s.length !== 3) return false;
                var c = [4, 4, 3];
                var m = true;
                for (i = 0; i < s.length; i++) {
                    if (s[i].length != c[i]) {
                        m = false;
                        break;
                    }
                }
                return m;
                */
                var d = this.digitSplited();
                var m = false;
                if (d.indexOf('.') != -1) {
                    s = d.split('.');
                    if (s.length === 3) {
                        var c = [4, 4, 3];
                        m = true;
                        for (i = 0; i < s.length; i++) {
                            if (s[i].length != c[i]) {
                                m = false;
                                break;
                            }
                        }
                    }
                } else {
                    m = (this.digit().length === 11 && this.value().length === 11);
                }
                return m;
            },
            validNOP: function() {
                var d = this.digitSplited();
                var m = false;
                if (d.indexOf('.') != -1) {
                    s = d.split('.');
                    if (s.length === 7) {
                        var c = [2, 2, 3, 3, 3, 4, 1];
                        m = true;
                        for (i = 0; i < s.length; i++) {
                            if (s[i].length != c[i]) {
                                m = false;
                                break;
                            }
                        }
                    }
                } else {
                    m = (this.digit().length === 18 && this.value().length === 18);
                }
                return m;
            },
            setIntegerValue: function(min = 0, max = 0) {
                if (isInputText) {
                    var v = parseInt(this.value());
                    v = isNaN(v) ? min : v;
                    v = (v < min) ? min : v;
                    v = (v > max && max > 0) ? max : v;
                    //me.val(v);
                    this.setValue(v);
                }
                return this;
            },
            resetForm: function(e = []) {
                var f = (isForm) ? me : me.closest('form');
                var cv = [];
                if (e.length == 0) {
                    e = [id];
                }
                if (e.length > 0) {
                    for (i = 0; i < e.length; i++) {
                        x = e[i];
                        if (x.indexOf('#') == -1) {x = '#' + x;}
                        //cv.push({obj: x, value: $(x).val()});
                        cv.push({obj: x, value: $(x).PBB().value()});
                    }
                }
                f.get(0).reset();
                if (cv.length > 0) {
                    for (i = 0; i < cv.length; i++) {
                        //$(cv[i].obj).val(cv[i].value);
                        $(cv[i].obj).PBB().setValue(cv[i].value);
                    }
                }
                return this;
            },
            //  v = true/false, e = element id atau selector id yg diubah status readonly
            setReadOnly: function(v = false, e = []) {
                if (isForm && e.length > 0) {
                    for (i = 0; i < e.length; i++) {
                        x = e[i];
                        if (x.indexOf('#') == -1) {x = '#' + x;}
                        $(x).attr('readonly', v);
                    }
                } else {
                    me.attr('readonly', v);
                }
                return this;
            },
            //  v = true/false, e = element yg ditampilkan / tidak 
            showElements: function(v, e = []) {
                if (isForm && e.length > 0) {
                    for (i = 0; i < e.length; i++) {
                        x = e[i];
                        if (x.indexOf('#') == -1) {x = '#' + x;}
                        if (v) {
                            $(x).removeClass('hide');
                        } else {
                            $(x).addClass('hide');
                        }
                    }
                } else {
                    if (v) {
                        me.removeClass('hide');
                    } else {
                        me.addClass('hide');
                    }
                }
                return this;
            },
            copyValueTo: function(e, i = true) {
                if (isInputText || isSelect) {
                    if (e.indexOf('#') == -1) {e = '#' + e;}
                    var v = this.value();
                    if (i === true) {$(e).val(v);} else {$(e).text(v);}
                }
                return this;
            },
            setAlignRight: function() {
                me.css('text-align', 'right');
                return this;
            },
            setValueFromData: function(d, p, c, t = 'I') {
                t = t.toUpperCase();
                if (t === 'B') {
                    me.prop('checked', false);
                } else {
                    //me.val('');
                    this.setValue('');
                }
                if (d != undefined && d) {
                    if (t === 'I') {
                        //me.val((isNaN(parseInt(d[p]))) ? 0 : parseInt(d[p]));
                        this.setValue((isNaN(parseInt(d[p]))) ? 0 : parseInt(d[p]));
                    } else if (t === 'F' || t === 'D') {
                        //me.val((isNaN(parseFloat(d[p]))) ? 0 : parseFloat(d[p]));
                        this.setValue((isNaN(parseFloat(d[p]))) ? 0 : parseFloat(d[p]));
                    } else if (t === 'B') {
                        if (d[p] != undefined && d[p]) {
                            me.prop('checked', (d[p] == '1'))
                        }
                        //me.val((isNaN(parseFloat(d[p]))) ? 0 : parseFloat(d[p]));
                        this.setValue((isNaN(parseFloat(d[p]))) ? 0 : parseFloat(d[p]));
                    } else {
                        //me.val(d[p]);
                        this.setValue(d[p]);
                    }
                } else {
                    //me.val(c);
                    this.setValue(c);
                }
                return this;
            },
            formatMoney: function(decPlaces = 2, thouSeparator = '.', decSeparator = ',') {
                var n = this.value(),
                    decPlaces = isNaN(decPlaces = Math.abs(decPlaces)) ? 2 : decPlaces,
                    decSeparator = decSeparator == undefined ? "." : decSeparator,
                    thouSeparator = thouSeparator == undefined ? "," : thouSeparator,
                    sign = n < 0 ? "-" : "",
                    i = parseInt(n = Math.abs(+n || 0).toFixed(decPlaces)) + "",
                    j = (j = i.length) > 3 ? j % 3 : 0;
                return this.setValue(sign + 
                            (j ? i.substr(0, j) + thouSeparator : "") + 
                            i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thouSeparator) + 
                            (decPlaces ? decSeparator + Math.abs(n - i).toFixed(decPlaces).slice(2) : "")
                        );
            },
            setBooleanView: function(v) {
                me.removeClass('glyphicon-check').removeClass('glyphicon-unchecked');
                me.addClass(v == '0' ? 'glyphicon-unchecked' : 'glyphicon-check');
                return me;
            },
            retriveFormDataValue: function(d, e = [], prefix = '', prefix_pos = 1, is_prefix_input = true) {
                if (isForm) {
                    for (var k in d) {
                        if (e.indexOf(k) == -1) {
                            $('#' + k).PBB().setValueFromData(d, k, '', 's');
                            if (prefix != '') {
                                kp = (prefix_pos != 1) ? prefix + k : k + prefix;
                                $('#' + kp).PBB().setValueFromData(d, k, '', 's');
                            }
                        }
                    }
                }
                return this;
            }
        };
        
        return $.fn.extend({}, defaults);
    }
})( jQuery );

(function( $ ){
    $.fn.pbbDatePicker = function(opt = {}) {
        var options = {
            format: 'dd-mm-yyyy',
            autoclose: true
        };
        $.extend(options, opt);
        return $(this).datepicker(options);
    }
})( jQuery );

function pbbDateFormat(str_dt) {
    function getFormated(v) {
        s = '0' + v.toString();
        return s.substring(s.length - 2);
    }
    if (str_dt == '') {
        return '';
    } else {
        var dt = new Date(str_dt);
        return getFormated(dt.getDate()) + '-' + getFormated(dt.getMonth() + 1) + '-' + dt.getFullYear();
    }
}
