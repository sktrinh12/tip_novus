import board
import digitalio
import busio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO

pins = {'pin17' : 17,  'pin18' : 18,  'pin27' : 27, 'pin23' : 23, 'pin24' : 24}
# gpio 24 is for the light switch 

GPIO.setmode(GPIO.BCM)
for pn in pins.values():
    GPIO.setup(pn, GPIO.OUT, initial=GPIO.LOW)

# create the spi bus
spi = busio.SPI(clock = board.SCK, MISO = board.MISO, MOSI = board.MOSI)

# create the chip select
cs = digitalio.DigitalInOut(board.D5)

#create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analogue input channel on pin0 (small sensor/small carboy)
chan_sm = AnalogIn(mcp, MCP.P0)

# create an analogue input channel on pin1 (large sensor/big carboy)
chan_lg = AnalogIn(mcp, MCP.P1)

# small carboy channel and large carboy channel
channels_dict = {'small' : chan_sm, 'large' : chan_lg}

# 4x led pins (2x reds, 2x greens)
led_dict = {'red_small' : pins['pin17'], 'green_small' :pins['pin18'], 'red_large' : pins['pin27'], 'green_large' : pins['pin23']}

# capacities of small and large carboys
carboy_capacity = {'small' : {'min':1.5,'max':7}, 'large' : {'min': 0,'max':24.75}}
