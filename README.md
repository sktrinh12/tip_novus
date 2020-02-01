## Integration API for TipNovus tip washer in Hamiton Vantage

The API is hosted on a **raspberry pi 4** running flask on the backend. The app allows users to get liquid level sensor data real-time and monitors reagent carboys with coloured LEDS. A pi-camera is installed which can stream data on an endpoint or save a video for a particular time-frame.

#### Calling the api can be done using curl:

getting the status of the washer compartment:

   curl http:{$hostname}:5000/tp_ser_wbsrv/dply_wash -X PUT

where `$hostname` is the nameof the current host (computer). A json response will be
outputted in the terminal, such as: 
   { "cmd": "dply_wash", "response": "01,TI,WA,WS,#", "code_cmd" : "01,ACK,00,#", "interpreation": "washer compartment is not in operation" }

OR ... running the python script (read_response_api.py which uses argparse) through the termainal:

   python read_response_api.py -e dply_wash -t put

typing `curl http:{$hostname}:5000/tp_ser_wbsrv/cmds -X GET` will list all the available valid commands.  

Streaming video can be done typing: `http://{gethostname}:5000/tp_ser_wbsrv into a browser where one can view live video stream from the picamera.


*Project completed for integrating the Grenova TipNovus mini tip cleaner into a Hamilton Vantage.*
