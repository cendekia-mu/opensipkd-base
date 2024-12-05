$(document).ready(function () {
  $('#departemen_nm').bind('typeahead:selected', function (obj, datum, name) {
    $('#departemen_id').val(datum.id);
    $('#departemen_kd').val(datum.kode);
    // console.log(datum.kode);
  });

  $('#departemen_nm').on('input',
      function (e) {
        let val = $('#departemen_nm').val();
        if (val === null || val === "") {
          $('#departemen_id').val("");
          $('#departemen_kd').val("");
        }
      });
});