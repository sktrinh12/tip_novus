//var videosrc = $("#videosrc > source");
//var videosrc = document.getElementsByTagName("source")[0];
var videotag = document.getElementsByTagName("video")[0];
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
   videotag.load();
};

$('#date-picker').datepicker({
    changeMonth: true,
    changeYear: true,
    showButtonPanel: true,
    dateFormat: 'dd-mm-yy'
});
