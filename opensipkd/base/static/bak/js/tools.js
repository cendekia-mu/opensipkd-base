Number.prototype.formatMoney = function(decPlaces, thouSeparator, decSeparator) {
var n = this,
    decPlaces = isNaN(decPlaces = Math.abs(decPlaces)) ? 2 : decPlaces,
    decSeparator = decSeparator == undefined ? "." : decSeparator,
    thouSeparator = thouSeparator == undefined ? "," : thouSeparator,
    sign = n < 0 ? "-" : "",
    i = parseInt(n = Math.abs(+n || 0).toFixed(decPlaces)) + "",
    j = (j = i.length) > 3 ? j % 3 : 0;
return sign + (j ? i.substr(0, j) + thouSeparator : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + thouSeparator) + (decPlaces ? decSeparator + Math.abs(n - i).toFixed(decPlaces).slice(2) : "");
};

var rows_selected = [];
function updateDataTableSelectAllCtrl(table){
  var $table             = table.table().node();
  var $chkbox_all        = $('tbody input[type="checkbox"]', $table);
  var $chkbox_checked    = $('tbody input[type="checkbox"]:checked', $table);
  var chkbox_select_all  = $('thead input[name="select_all"]', $table).get(0);

  // If none of the checkboxes are checked
  if($chkbox_checked.length === 0){
    chkbox_select_all.checked = false;
    if('indeterminate' in chkbox_select_all){
      chkbox_select_all.indeterminate = false;
      }
    } 
  else if ($chkbox_checked.length === $chkbox_all.length){
    chkbox_select_all.checked = true;
    if('indeterminate' in chkbox_select_all){
       chkbox_select_all.indeterminate = false;
      }
    } 
  // If some of the checkboxes are checked
  else {
    chkbox_select_all.checked = true;
    if('indeterminate' in chkbox_select_all){
       chkbox_select_all.indeterminate = true;
      }
    }
  }

function formatNumber(toFormat) {
   return toFormat.toString().replace(
       /\B(?=(\d{3})+(?!\d))/g, ".");
};

function digitOnly(toFormat) {
    val = toFormat.toString().replace(/\D/g, "");
    if(val=='')val = 0;
    return val;
};


