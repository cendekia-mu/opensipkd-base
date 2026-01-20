$(document).ready(function () {
  $('#partner_nm').bind('typeahead:selected', function (obj, datum, name) {
    $('#partner_id').val(datum.id);
    console.log(datum.kode);
  });
  $('#partner_nm').on('input',
    function (e) {
      let val = $('#partner_nm').val();
      if (val === null || val === "") {
        $('#partner_id').val("");
      }
    });

  
  $('#departemen_nm').bind('typeahead:selected', function (obj, datum, name) {
    $('#departemen_id').val(datum.id);
    console.log(datum.kode);
  });
  $('#departemen_nm').on('input',
    function (e) {
      let val = $('#departemen_nm').val();
      if (val === null || val === "") {
        $('#departemen_id').val("");
      }
    });


});