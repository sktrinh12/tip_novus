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

$(document).ready(function() { 
    // $("#video_stream").prepend('<img src="https://tse3.mm.bing.net/th?id=OIP.qHlRBDXIrAX4QnBqZ3LhKwHaE8&pid=Api" width="100" height="100" alt="" />') //initialise img tag

      $("#start_btn").click(function(e) {
        e.preventDefault();
        $.when(
            ajax_call('/start', 
                      contentype_txt, 
                      'json', 
                      {btn_type : $("#start_btn").text().replace(/ /g,'')},
                      function(data) { console.log(data['btn']); }
                    )
        ).done(function() {
          console.log('Starting video stream');
          $("#overlay").css("display", "none");
          // $("#video_stream").css("display", "none");
          $("#video_stream").css("display", "block");}
          // $("#video_stream").html(`<img src="{{ url_for('video_feed') }}">`); }
        );
      });

      $("#stop_btn").click(function(e) {
        e.preventDefault();
        $.when(
            ajax_call('/stop', 
                      contentype_txt, 
                      'json', 
                      {btn_type : $("#stop_btn").text().replace(/ /g,'')},
                      function(data) { console.log(data['btn']); }
                    )
        ).done(function() {
          console.log('Stopping video stream');
          $("#overlay").css("display", "block");
          $("#video_stream").css("display", "none");
        }
      );
      });
});
