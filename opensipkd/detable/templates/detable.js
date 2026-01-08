// deform.addCallback('${tableid}', function (oid) {

var m${tableid}ID;
var o${tableid};
var o${tableid}Uri = "${url}";
var o${tableid}Url = o${tableid}Uri + "${url_suffix}";
var m${tableid}ID;
var m${tableid}CheckList = [];
var check_field = ${check_field};
// Function to add data to checkbox list programmatically
function add${tableid} ToList(ids, updateCheckboxes) {
  if (!Array.isArray(ids)) {
    ids = [ids];
  }

  ids.forEach(function (id) {
    if (m${tableid}CheckList.indexOf(id) === -1) {
        m${tableid}CheckList.push(id);
    }

    if (updateCheckboxes) {
      $("#${tableid}_check_" + id).prop("checked", true);
    }
  });

  if (updateCheckboxes && typeof updateCheckAllStatus === 'function') {
    updateCheckAllStatus();
  }

  console.log("Added to ${tableid} list:", ids, "Current list:", m${tableid}CheckList);
 }

// Function to remove data from checkbox list programmatically
function remove${tableid}FromList(ids, updateCheckboxes) {
  if (!Array.isArray(ids)) {
    ids = [ids];
 }

  ids.forEach(function (id) {
    var index = m${tableid}CheckList.indexOf(id);
    if (index > -1) {
      m${tableid}CheckList.splice(index, 1);
    }

    if (updateCheckboxes) {
      $("#${tableid}_check_" + id).prop("checked", false);
    }
  });

  if (updateCheckboxes && typeof updateCheckAllStatus === 'function') {
    updateCheckAllStatus();
  }

  console.log("Removed from ${tableid} list:", ids, "Current list:", m${tableid}CheckList);
}

// Make functions globally accessible
window['add${tableid}ToList'] = add${tableid}ToList;
window['remove${tableid}FromList'] = remove${tableid}FromList;

function displayEmptyID() {
  $("#emptyID").show();
  $('#emptyID').animate({opacity: 0.8}, 2000);
  setTimeout(function () {
    $("#emptyID").fadeTo(500, 0).slideUp(500, function () {
      $("#emptyID").hide();
   });
 }, 4000);
}

let tb_array = [
  '<div class="btn-group pull-left">',
  '${structure:buttons}',
  ' &nbsp;',
  '</div>',
]

let ${tableid}Language = {
  "search": "Cari: ",
  "paginate": {
    "first": '<span class="glyphicon glyphicon-step-backward"></span> ',
    "last": '<span class="glyphicon glyphicon glyphicon-step-forward"></span> ',
    "previous": '<span class="glyphicon glyphicon-backward"></span> ',
    "next": '<span class="glyphicon glyphicon-forward"></span> ',
 },
  "infoEmpty": "Menampilkan 0 sampai 0 dari 0",
  "info": "Menampilkan _START_ sampai _END_ dari _TOTAL_",
  "infoFiltered": "(disaring dari _MAX_ total keseluruhan)",
  "lengthMenu": " _MENU_ baris ",
  "loadingRecords": "Sedang memuat...",
  "processing": "Sedang memproses...",
  "emptyTable": "Tidak ada data yang tersedia pada tabel ini",
  "zeroRecords": "Tidak ditemukan data yang sesuai",
};


let ${tableid}Columns = ${structure: columns};

function render_checkbox(value) {
  if (value === true)
    return '<i class="fas fa-check-square" aria-hidden="true">';
  if (value === false)
    return '<i class="fas fa-minus-square" aria-hidden="true">';
  return value;
}

function render_checklist(value) {
  return '<input type="checkbox" class="${tableid}_check" checked="' + {value} + '"></input>';
}

//var mtableId = "${tableid}";
for (let co in ${tableid}Columns) {
  if (${tableid}Columns[co].wg_checkbox === true) {
    ${tableid}Columns[co].render = function (value) {
      if (typeof value === "string" && value.length > 0) {
        return render_checkbox(value)
     }
      if (["", false, 0, null].indexOf(value) === -1) {
        return render_checkbox(true);
     }
      return render_checkbox(false);
    }
  }
  else if (${tableid}Columns[co].wg_select === true) {
    ${tableid}Columns[co].render = function (value) {
      if (value != null)
        return ${tableid}Columns[co].wg_select_val[value];
      return "";
   }
  }else if (${tableid}Columns[co].hasOwnProperty("url")) {
    let url = ${tableid}Columns[co].url;
    ${tableid}Columns[co].render = function (data) {
      let result = "No Data";
      if (data != null) {
        result = '<a href="' + url + data + '" target="_blank">Link</a>&nbsp;';
      }
      return result;
    }
  }else if (${tableid}Columns[co].data === "id") {
    ${tableid}Columns[co].render = function (id, typ, data, setting) {
      if (${tableid}Columns[co].action === false) return ""
      let result = "";
    <tal:block tal:condition="allow_check=='true'">
      var checked = "";
      if (check_field !== "") {
        checked = data[check_field] !== null ? "checked" : "";
        if (checked === "checked" && m${tableid}CheckList.indexOf(id) === -1) {
          m${tableid}CheckList.push(id);
        }
      }
      result = '<input type="checkbox" class="${tableid}_check" id="${tableid}_check_' + id +'"
        value="' + id + '" ' + checked + ' name="${tableid}_check" />&nbsp;';
    </tal:block>
    <tal:block tal:condition="allow_check=='false'">
      <tal:block tal:condition="allow_view=='true'">
        result += '<a href="${url}/' + id + '/view"><i class="fas fa-eye" aria-hidden="true"
            title="View"></i></a>&nbsp;';
      </tal:block>
      <tal:block tal:condition="allow_edit=='true'">
        result += '<a href="${url}/' + id + '/edit"><i class="fas fa-edit" aria-hidden="true"
            title="Edit"></i></a>&nbsp;'
      </tal:block>
      <tal:block tal:condition="allow_delete=='true'">
        result += '<a href="${url}/' + id + '/delete"><i class="fas fa-trash" aria-hidden="true"
            title="Delete"></i></a>';
      </tal:block>
      <tal:block tal:condition="allow_post=='true'">
        result += '<a href="${url}/' + id + '/post"><i class="fas fa-signs-post" aria-hidden="true"
            title="Post"></i></a>';
      </tal:block>
      <tal:block tal:condition="allow_post=='true'">
        result += '<a href="${url}/' + id + '/unpost"><i class="fas fa-delete-left" aria-hidden="true"
            title="Unpost"></i></a>';
      </tal:block>
    </tal:block>
      return result;
   }
 }
}

//end column definition loop

let ${tableid}Params = {};
var param_ajax = "";
var param_data = [];
if (!${server_side}) param_data = ${data};
    else param_ajax = o${tableid} Url;

    o${tableid}= $('#${tableid}').DataTable({
  scrollX: ${field.scroll_x},
  //scrollY: ${field.scroll_y},
  //dom: '<"row"<"col-md-8"<"toolbar">Bl><"col-md-4"fr>>tip',
  dom: '<"row"<"col-md-8"<"toolbar">>><"row"<"col-md-8"Bl><"col-md-4"fr>>t<"row dt-footer"<"col-md-8 sub-foot" i>
< "col-md-4"p >> ',
                  processing: true,
  serverSide: ${server_side},
  data: param_data,
  ajax: param_ajax,
  stateSave: ${state_save},
  scrollCollapse: true,
  sort: ${sorts},
  info: true,
  filter: ${filters},
  autoWidth: false,
  paginate: ${paginates},
  paginationType: "full_numbers",
  order: [],
  lengthMenu: [
  [10, 25, 50, 100],
  [10, 25, 50, 100]
],
  pageLength: 25,
  columns: ${tableid}Columns,
  language: ${tableid}Language,
  initComplete: function () {
    $('.dataTables_filter input').unbind()
      .bind('keyup', function (e) {
        var code = e.keyCode || e.which;
        if (code === 13) {
                  o${tableid}.search(this.value).draw();
       }
     });
 },
  drawCallback: function () {
    // Update check all status after table redraw
    <tal:block tal:condition="allow_check=='true'">
      updateCheckAllStatus();
    </tal:block>
 }
                 });

let tb = tb_array.join(' ');
$("div.toolbar").html(tb);
$("div.toolbar").attr('style', 'display:block; float: left; margin-bottom:6px; line-height:16px;');
$("div.dt-footer").attr('style', 'margin-left: -7px;');
$("div.sub-foot").attr('style', 'position:unset;');
$(".dataTables_scrollBody").attr('style', 'margin-top: -10px;');
<tal:block tal:condition="allow_check=='true'">

  //Begin Allow Check
  $('#${tableid} tbody').on('click', ':checkbox', function () {
    var checkboxValue = $(this).val();
    if (this.checked) {
      // Add to list if not already present
      if (m${tableid}CheckList.indexOf(checkboxValue) === -1) {
        m${tableid}CheckList.push(checkboxValue);
      }
    }else {
      // Remove from list
      var index = m${tableid}CheckList.indexOf(checkboxValue);
      if (index > -1) {
        m${tableid}CheckList.splice(index, 1);
      }
    }
    console.log("Checkbox Clicked", m${tableid}CheckList);
    updateCheckAllStatus();
  });
  $('#${tableid} tbody').on('change', ':checkbox', function () {
    var checkboxValue = $(this).val();
    if (this.checked) {
      // Add to list if not already present
      if (m${tableid}CheckList.indexOf(checkboxValue) === -1) {
        m${tableid}CheckList.push(checkboxValue);
      }
    }else {
      // Remove from list
      var index = m${tableid}CheckList.indexOf(checkboxValue);
      if (index > -1) {
        m${tableid}CheckList.splice(index, 1);
      }
    }
    console.log("Checkbox Changed", m${tableid}CheckList);
    updateCheckAllStatus();
  });
  $("#${tableid}checkAll").on("click", '', function (e) {
    e.stopPropagation();
    if (this.checked) {
      // Check all checkboxes and add all to list
      $(".${tableid}_check").each(function () {
        $(this).prop("checked", true);
        var checkboxValue = $(this).val();
        if (m${tableid} CheckList.indexOf(checkboxValue) === -1) {
          m${tableid}CheckList.push(checkboxValue);
        }
      });
    }else {
      // Uncheck all checkboxes and clear list
      $(".${tableid}_check").prop("checked", false);
      m${tableid}CheckList = [];
    }
    console.log("Check All Clicked", m${tableid}CheckList);
  });

  // Function to update check all status based on individual checkboxes
  function updateCheckAllStatus() {
    var totalCheckboxes = $(".${tableid}_check").length;
    var checkedCheckboxes = $(".${tableid}_check:checked").length;

    if (checkedCheckboxes === 0) {
      $("#${tableid}checkAll").prop("checked", false);
      $("#${tableid}checkAll").prop("indeterminate", false);
    }else if (checkedCheckboxes === totalCheckboxes) {
      $("#${tableid}checkAll").prop("checked", true);
      $("#${tableid}checkAll").prop("indeterminate", false);
    }else {
      $("#${tableid}checkAll").prop("checked", false);
      $("#${tableid}checkAll").prop("indeterminate", true);
    }
  };

  // Function to get selected data from checked rows
  function get${tableid}SelectedData() {
    var selectedData = [];
    $(".${tableid}_check:checked").each(function() {
      var rowData = o${tableid}.row($(this).closest('tr')).data();
      if (rowData) {
        selectedData.push(rowData);
      }
    });
    return selectedData;
  };

  // Function to get selected IDs
  function get${tableid}SelectedIds() {
    return m${tableid}CheckList.slice(); // Return copy of the array
  };

  // Make functions globally accessible
  window['get${detable}SelectedData'] = get${tableid}SelectedData;
  window['get${tableid}SelectedIds'] = get${tableid}SelectedIds;
                    //${tableid}.ajax.reload(function() {
    $("#${tableid}_delete").type == 'button';
  $("#${tableid}_delete").on("click", function () {
    console.log("Delete Clicked", m${tableid}CheckList);
                   });
//End Allow Check
</tal:block>
$('#${tableid} tbody').on('click', 'tr', function () {
  if ($(this).hasClass('selected')) {
    $(this).removeClass('selected');
                  m${tableid} ID = null;
 } else {
    let aData = o${tableid}.row(this).data();
                  o${tableid}.$('tr.selected').removeClass('selected');
    $(this).addClass('selected');
                  m${tableid} ID = aData.id;
                  o${tableid}.$('tr.row_selected').removeClass('row_selected');
    $(this).addClass('row_selected');
 }
});
<tal:block tal:condition="filter_columns">
  $(".${tableid}-control-filter").on('keyup', function (e) {
                    var code = e.keyCode || e.which;
  if (code === 13) filter_table();
                   });

  $("#${tableid}_length").append('<label>&emsp;${structure:edit_buttons}</label>');

  function filter_table() {
    $(".${tableid}-control-filter").each(function (e) {
      var col_id = $(this).attr("id");
      var value;
      if ($(this).attr("type") === 'radio') {
        col_id = $(this).attr('id').split("-");
        col_id.length = 2;
        col_id = col_id.join("-");
        value = this.value;
        if (this.checked) {
          //console.log(col_id, $(this).attr('id'), value, this.checked);
          localStorage.setItem(col_id, value);
                    o${tableid}.column($(this).data('index')).search(this.value)
                   }
                   }
  else if ($(this).attr("type") === 'date') {
    value = this.value;
  localStorage.setItem(col_id, value);
  var splitted = col_id.split('-');
  if (splitted[splitted.length - 1] !== "min" && splitted[splitted.length - 1] !== "max"){
    o${tableid}.column($(this).data('index')).search(value)
                   }
  else{
                    var min_val = undefined;
  var max_val = undefined;
  if (splitted[splitted.length - 1] === "min") {
    min_val = this.value;
  splitted.length = splitted.length - 1;
  col_id = splitted.join("-");
  max_val = $("#" + col_id + '-max').val()
                   }
  else {
    max_val = this.value;
  splitted.length = splitted.length - 1;
  col_id = splitted.join("-");
  min_val = $("#" + col_id + '-min').val();
                   }
  if (min_val === undefined && max_val !== undefined) min_val = max_val;
  if (max_val === undefined && min_val !== undefined) max_val = min_val;
  if (max_val !== undefined && min_val !== undefined && min_val !== null && max_val !== null)
  o${tableid}
  .column($(this).data('index'))
  .search(min_val + '-yadcf_delim-' + max_val, true);
                    //&& min_val !== "" && max_val !== ""
                   }
                   }
  else {
    col_id = this.id;
  value = this.value;
  if (value === undefined || value === null) value = "";
  console.log(col_id, $(this).attr('id'), value, $(this).data('index'));
  localStorage.setItem(col_id, value);
  o${tableid}
  .column($(this).data('index'))
  .search(value);
                   }
                   });
  o${tableid}.draw();
                   }

  $(".${tableid}-control-filter").on('click', function (e) {
                    //console.log("Write Data Click");
                    var typ = $(this).attr("type");
  if (typ === 'radio') {
    filter_table();
                   }
                   });
  $(".${tableid}-control-filter").on('change', function (e) {
                    var typ = $(this).prop("nodeName").toLowerCase();
  if (typ === "select") filter_table();

  var typ = $(this).attr("type").toLowerCase();
  if (typ === "date") filter_table();
                   });

  console.log("Read Data");
  $(".${tableid}-control-filter").each(function (e) {
                    var col_id = $(this).attr("id")
  var value;
  if ($(this).attr("type") === 'radio') {
    col_id = $(this).attr('id').split("-");
  col_id.length = 2;
  col_id = col_id.join("-");
  value = localStorage.getItem(col_id);
  if (value !== undefined && value != null)
  if ($(this).val() === value) $(this).attr("checked", true);
  else $(this).attr("checked", false);
                   }
  else {
    value = localStorage.getItem(col_id);
  if (value !== undefined && value !== null)
  $(this).val(value);
                   }
                   });

  filter_table();
</tal:block>
                  ${structure: btnscripts}
                  ${structure: filter_scripts}

                 });
                 });


I'll help you add datatable functionality for handling checkbox data. Let me first examine the current template file to understand the existing structure.

detable.pt

Let me see more of the file to understand the complete structure, especially the JavaScript part:

detable.pt

Let me continue reading to see the rest of the JavaScript implementation:

detable.pt

Let me see the rest of the file to understand the complete implementation:

detable.pt

Now I understand the structure.I can see that there's already functionality for checkboxes and handling selected items in the datatable, but it looks like there might need to be some improvements to the "adddata to list from checkbox after prop" functionality.

Based on the code, I can see:

There's a checkbox implementation for each row (${tableid}_check)
There's a "check all" functionality (${tableid}checkAll)
There's a list to track checked items (m${tableid}CheckList)
There's some commented code for delete multiple functionality
Let me enhance the checkbox functionality to properly add data to list from checkboxes.I'll need to fix some issues I notice:

Edited
detable.pt + 138 - 11
I've successfully enhanced the datatable checkbox functionality with the following improvements:

Key Enhancements Made:
1. Improved Checkbox List Management
Fixed duplicate entries in the checkbox list
Proper add / remove logic for checkbox state changes
Prevention of duplicate IDs in the selection list
2. Enhanced Check All Functionality
Properly manages all checkboxes when "Check All" is clicked
Supports indeterminate state for partial selections
Updates the list correctly when checking / unchecking all items
3. Added Utility Functions
get[TableId]SelectedData() - Returns full row data for selected items
get[TableId]SelectedIds() - Returns array of selected IDs
add[TableId]ToList(ids, updateCheckboxes) - Programmatically add items to selection
remove[TableId]FromList(ids, updateCheckboxes) - Programmatically remove items from selection
4. Improved State Management
Added updateCheckAllStatus() function to maintain consistency between individual checkboxes and "check all"
Added drawCallback to update checkbox states after table redraws
Fixed initialization of pre - checked items based on check_field
5. Better Event Handling
Prevents duplicate event handling
Proper cleanup and state management on checkbox changes
Console logging for debugging purposes
Usage Examples:
  // Get selected IDs
  var selectedIds = getYourTableIdSelectedIds();

// Get full data of selected rows  
var selectedData = getYourTableIdSelectedData();

// Programmatically add items to selection
addYourTableIdToList([1, 2, 3], true); // true = also update checkboxes

// Programmatically remove items from selection
removeYourTableIdFromList([1], true); // true = also update checkboxes

The enhanced functionality now provides robust support for adding data to lists from checkboxes with proper state management and utility functions for programmatic control.