#!/usr/bin/python

import argparse
import serial
import time

try:
    import meterbus
except ImportError:
    import sys
    sys.path.append('../')
    import meterbus



def setPrimary(address, newAddress):

    meterbus.send_request_setPrimary(ser, address, newAddress )
    try:
        frame = meterbus.load(meterbus.recv_frame(ser, 1))
        if isinstance(frame, meterbus.TelegramACK):
            return True
    except meterbus.MBusFrameDecodeError:
        pass

    return False

def setG4modern(address):
    meterbus.send_request_setLUG_G4_readout_control(ser, address, 0x00)
    try:
        frame = meterbus.load(meterbus.recv_frame(ser, 1))
        if isinstance(frame, meterbus.TelegramACK):
            return True
    except meterbus.MBusFrameDecodeError:
        pass

    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Scan serial M-Bus for devices.')
    parser.add_argument('-a', '--address',
                        type=str, default=meterbus.ADDRESS_BROADCAST_REPLY,
                        help='Primary address')
    parser.add_argument('-m', '--modern',
                        action='store_true',
                        help='Sets modern data output G4 Landis und Gyr')
    parser.add_argument('-b', '--baudrate',
                        type=int, default=2400,
                        help='Serial bus baudrate')
    parser.add_argument('-d', action='store_true',
                        help='Enable verbose debug')
    parser.add_argument('-n', '--newAddress',
                        type=int,
                        help='New Primary address')
    parser.add_argument('-r', '--retries',
                        type=int, default=5,
                        help='Number of ping retries for each address')
    parser.add_argument('device', type=str, help='Serial device or URI')

    args = parser.parse_args()

    meterbus.debug(args.d)

    try:
        with serial.serial_for_url(args.device,
                           args.baudrate, 8, 'E', 1, timeout=1) as ser:
                if args.modern:
                    if setG4modern(args.address):
                        print(
                            "Set M-Bus device at address {0} to G4 compatible modern output".format(args.address)
                        )

                if args.newAddress:
                    if setPrimary(args.address, args.newAddress):
                        print(
                            "Set M-Bus device at address {0} to {1}".format(args.address,args.newAddress)
                        )

    except serial.serialutil.SerialException as e:
        print(e)
