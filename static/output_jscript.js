$(document).ready(function () {
     const output_div = document.getElementById('console_output');
       const source = new EventSource("/console_output");
         source.onmessage = function(event) {
               console.log('credentials: ' + source.withCredentials);
               console.log('state: ' + source.readyState);
               console.log('URL: ' + source.url);
//                const data = JSON.parse(event.data);
                  output_div.innerHTML += event.data + "</br>";                
//                    output_div.innerHTML += data + "</br>";
                      }
});
