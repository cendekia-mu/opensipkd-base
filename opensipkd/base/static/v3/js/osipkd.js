function showError(msg) {
    $("#success").css('display', 'none', 'important');
    $("#errors").css('display', 'box', 'important');
    $("#errors").html("<span class='glyphicon glyphicon-remove'></span> " + msg);
    console.log(msg);
};

function showSuccess(msg) {
    $("#errors").css('display', 'none', 'important');
    $("#success").css('display', 'box', 'important');
    $("#success").html("<span class='glyphicon glyphicon-ok'></span> " + msg);
};
$(function () {
    var current = location.pathname;
    $('nav li a').each(function () {
        var $this = $(this);
        if ($this.attr('href') != '' && $this.attr('href') != '#') {
            if ($this.attr('href') == current) {
                $this.parent().addClass('active');
                var ul_parent = $this.parents('ul');
                ul_parent.show();
                ul_parent.parents('li').addClass('open');
            }
        }
    })
});
$(document).ready(function () {
    // DO NOT REMOVE : GLOBAL FUNCTIONS!
    pageSetUp();
    /*
     * PAGE RELATED SCRIPTS
     */
});

function number_format(number, decimals, dec_point, thousands_sep) {
    // Strip all characters but numerical ones.
    number = (number + '').replace(/[^0-9+\-Ee.]/g, '');
    var n = !isFinite(+number) ? 0 : +number,
        prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
        sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
        dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
        s = '',
        toFixedFix = function (n, prec) {
            var k = Math.pow(10, prec);
            return '' + Math.round(n * k) / k;
        };
    // Fix for IE parseFloat(0.55).toFixed(0) = 0;
    s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
    if (s[0].length > 3) {
        s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
    }
    if ((s[1] || '').length < prec) {
        s[1] = s[1] || '';
        s[1] += new Array(prec - s[1].length + 1).join('0');
    }
    return s.join(dec);
}
