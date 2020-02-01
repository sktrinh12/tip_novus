var contentype_img = 'image/jpeg'
var contentype_txt = 'application/json; charset=utf-8'


// $("#video_stream").prop("src",reply); },
// $("#video_stream").attr("src", reply); },

function ajax_call(u, ct, dt, dat, succ){ //u = url, ct = contentType, dt = dataType, dat = data, succ = success
  var params = {
    url : u,
    contentType : ct,
    dataType : dt,
    data : dat,
    success : succ,
    error: function(error, txt_status) {
                    console.log(txt_status);
                    console.log(error);}
    };
    if (dat == null) {delete params.data;}
    $.ajax(params);
}

function template_img(){
    $("#video_stream").prepend('<img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs" id="init_img" width="695" height="460" alt="" />'); //initialise img tag
    $("#overlay").html('<h4><font color="#2152bd"><strong>No video currently streaming...</strong></font></h4>');
}

$(document).ready(function() {
      template_img();

      $("#start_btn").click(function(e) {
        e.preventDefault();
        //console.log('testing');
        $.when(
            ajax_call('/tp_ser_wbsrv/video_feed/start',
                      contentype_txt,
                      'json',
                      {btn_type : $("#start_btn").text().replace(/ /g,'')},
                      function(data) { console.log(data['btn']); }
                    )
        ).done(function() {
          console.log('Starting video stream');
          // $("#overlay").css("display", "none");
          $("#init_img").remove();
          $("#video_stream").css("display", "block");
          $("#video_stream").find("img").removeAttr("src").attr("src", "/videofeed");
          $("#overlay").css("display", "none");
          }
        );
      });

      $("#stop_btn").click(function(e) {
        e.preventDefault();
        $.when(
            ajax_call('/tp_ser_wbsrv/video_feed/stop',
                      contentype_txt,
                      'json',
                      {btn_type : $("#stop_btn").text().replace(/ /g,'')},
                      function(data) { console.log(data['btn']); }
                    )
        ).done(function() {
          console.log('Stopping video stream');
          template_img();
          $("#overlay").css("position", "inherit");
          $("#overlay").css("display", "flex");
          $("#video_stream").css("display", "none");
        }
      );
      });
});
