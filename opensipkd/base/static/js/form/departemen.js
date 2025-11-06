$(document).ready(function () {
  $('#parent_nm').bind('typeahead:selected', function (obj, datum, name) {
    $('#parent_id').val(datum.id);
    $('#parent_kd').val(datum.kode);
    console.log(datum.kode);
  });
  $('#parent_nm').on('input',
    function (e) {
      let val = $('#parent_nm').val();
      if (val === null || val === "") {
        $('#parent_id').val("");
        $('#parent_kd').val("");
      }
    });
});