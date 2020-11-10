import os
import time
from Phidget22.Phidget import *
from Phidget22.Devices.RFID import *
import serial
import sqlite3


db_filepath = '/home/pi/hamilton_web_app_v1.2/tip_novus/db/'

# dmso kegs db file - mapping of serial number/rfid tag to tare weight
db_keg_filepath = os.path.join(db_filepath, 'dmso_kegs.db')

port_addr = '/dev/ttyUSB1' # scale port on rpi
baudrate = 9600
timeout = 10


def read_scale(port=port_addr):
    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        ser.write(b'W\r')
        time.sleep(0.5)
        res = ser.read(10).decode().strip().replace('k', '')
        #print(f'scale read: {res}')
    return res


def read_tag():
    """
    using phidget library, read the current tag and output
    """
    try:
        ch = RFID()
        ch.openWaitForAttachment(5000)
        time.sleep(1)
        val = ch.getLastTag()[0]
        ch.close()
        return val
    except PhidgetException as e:
        print(f'no tag present - {e}')
        return None


def get_tare_weight(rfid_tag):
    """
    get the tare weight and serial number from the sqlite3 db; this requires to
    pass a rfid_tag string to get the tare weight according to that rfid_tag
    this is a mapping of rfid tags to serial numbers and thus tare weights
    """
    try:
        if rfid_tag:
            with sqlite3.connect(db_keg_filepath) as con:
                res = con.execute(
                    f"SELECT SERIAL_NUMBER, TARE_WEIGHT FROM 'DMSO_KEGS' WHERE RFID_TAG= '{rfid_tag}'")
                return [r for r in res][0]
        else:
            return None
    except Exception as e:
        print(e)
        return None

#if __name__ == "__main__":
#    rftag = read_tag()
#    print(f'rfid tag: {rftag}')
#    serial_nbr, tare_wt = get_tare_weight(rftag)
#    gross_wt = read_scale()
#    print(f'tare weight: {tare_wt}')
#    print(f'gross weight: {gross_wt}')
#    print(f'serial number: {serial_nbr}')
