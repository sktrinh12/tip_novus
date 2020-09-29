//var videosrc = $("#videosrc > source");
//var videosrc = document.getElementsByTagName("source")[0];
var videotag = document.getElementsByTagName("video")[0];
var plybktitle = document.getElementById("playback-title");
//var fpath = 'file:///C:/Program Files/Hamilton/logs/tipNovus/recorded_videos/mp4_format'

function switch_video(self, ipaddr) {
   var filename = self.text;
   var videosrc = document.createElement("source");
   videotag.innerHTML = '';
   url = `http://${ipaddr}:5000/tp_ser_wbsrv/video/${filename}`;
   console.log(url);
   videosrc.setAttribute('src', url);
   videosrc.setAttribute('type', "video/mp4");
   videotag.appendChild(videosrc);
   plybktitle.innerHTML = filename;
   videotag.load();
};

$('#date-picker').datepicker({
    changeMonth: true,
    changeYear: true,
    showButtonPanel: true,
    dateFormat: 'dd-mm-yy'
});

 //$('#date-picker').on('click', function(e) {
 //   e.preventDefault();
 //   $(this).attr("autocomplete", "off");
 //});


function switch_lamp() {
   var triggerBtn = document.getElementById("lamp-switch");
   if (triggerBtn.checked === true) {
      $.ajax({
         url: '/on',
         success: () => {
            console.log('turned lamp on');
         }});
   } else {
      $.ajax({
         url: '/off',
         success: () => {
            console.log('turned lamp off');
         }});
      }
};

