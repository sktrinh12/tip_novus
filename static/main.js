var videosrc = $("#videosrc");
//var fpath = 'file:///C:/Program Files/Hamilton/logs/tipNovus/recorded_videos/mp4_format'

function switch_video(self) {
   var filename = self.text;
   var videotag = document.getElementsByTagName("video")[0];
      console.log(filename);
      videosrc.attr('src', `/static/videos/mp4_format/${filename}`);
      videotag.load();
};

$('#date-picker').datepicker({
    changeMonth: true,
    changeYear: true,
    showButtonPanel: true,
    dateFormat: 'dd-mm-yy'
});
