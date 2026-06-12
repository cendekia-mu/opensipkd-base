$(function () {
  $('#deformcheck').click(function (e) {
    var url = '%s';
    e.preventDefault();
    console.log('Check button clicked: ' + url);
    $.get(url, function (data) {
      console.log("Data loaded:", data);
      $('#errors').hide();
      $('#success').text(data.message).show();

    }).fail(function (jqXHR, textStatus, errorThrown,) {
      var err = ("Error printing: " + errorThrown + " " + jqXHR.responseJSON.message);
      $('#success').hide();
      $('#errors').text(err).show();
    });
  });
});