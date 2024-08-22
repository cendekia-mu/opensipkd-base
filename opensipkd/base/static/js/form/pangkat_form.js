$(document).ready(function () {
  $('#pangkat_nm').bind('typeahead:selected', function (obj, datum, name) {
    $('#pangkat_id').val(datum.id);
    $('#pangkat_kd').val(datum.kode);
    console.log(datum.kode);
  });

  $('#pangkat_nm').on('input',
      function (e) {
        let val = $('#pangkat_nm').val();
        if (val === null || val === "") {
          $('#pangkat_id').val("");
          $('#pangkat_kd').val("");
        }
      });
});