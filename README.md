API for robotic liquid handler tip cleaner - Grenova TipNovus. The API is hosted on a raspberry pi 4 running flask on the backend. The app allows users to get liquid level sensor data real-time and monitors reagent carboys with coloured LEDS. A pi-camera is installed which can stream data on a endpoint. 

Calling the api can be done using curl:

getting the status of the washer compartment:
curl http:{gethostname}:5000/tp_ser_wbsrv/dply_wash -X PUT

OR ... running the python script (argparse) through the termainal:

python read_response_api.py -e dply_wash -t put

typing curl http:{gethostname}:5000/tp_ser_wbsrv/cmds -X GET will list all the available commands.  


Streaming video can be done typing: 

entering http://{gethostname}:5000/tp_ser_wbsrv into a browser one can view live video stream from the picamera. 

Project completed for integrating the Grenova TipNovus mini tip cleaner into a Hamilton Vantage.
