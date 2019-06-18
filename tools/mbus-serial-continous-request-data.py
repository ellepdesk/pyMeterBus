#!/usr/bin/python

from __future__ import print_function

import argparse
import serial
import time
import os
import stat
import _thread as thread

try:
    import meterbus
except ImportError:
    import sys
    sys.path.append('../')
    import meterbus

keep_going = True

def ping_address(ser, address, retries=5):
    for i in range(0, retries + 1):
        meterbus.send_ping_frame(ser, address)
        try:
            frame = meterbus.load(meterbus.recv_frame(ser, 1))
            if isinstance(frame, meterbus.TelegramACK):
                return True
        except meterbus.MBusFrameDecodeError:
            pass

    return False

def do_reg_file(args):
    with open(args.device, 'rb') as f:
        frame = meterbus.load(f.read())
        if frame is not None:
            print(frame.to_JSON())

def do_char_dev(args):
    address = None

    try:
        address = int(args.address)
        if not (0 <= address <= 254):
            address = args.address
    except ValueError:
        address = args.address.upper()

    try:
        #vib_to_show = ['14:0','59:1','59:0','89:0', '93:0', '255.34:0']
        #vib_to_show = ['14:0','59:0','89:0', '93:0']
        filter = {((14,), 0, 0): "one",
                  #((14,), 0, 1): "one_b",
                  ((59,), 0, 0): "two",
                  ((89,), 0, 0): "three",
                  ((93,), 0, 0): "four",
                  ((255, 34), 0, 0): "five",
                  }

        ibt = meterbus.inter_byte_timeout(args.baudrate)
        with serial.serial_for_url(args.device,
                           args.baudrate, 8, 'E', 1,
                           inter_byte_timeout=ibt,
                           timeout=1) as ser:
            frame = None

            if meterbus.is_primary_address(address):
                ping_address(ser, meterbus.ADDRESS_NETWORK_LAYER, 0)
                t_start = time.time()-100
                try:
                    while keep_going:
                        time.sleep(0.1)
                        if (time.time() - t_start) <= 10:
                            continue
                        t_start=time.time()
                        meterbus.send_request_frame(ser, address)
                        framedata = meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH)
                        frame = meterbus.load(framedata)


                        if not frame:
                            continue

                        records = frame.body.bodyPayload.records
                        filtered = {"ts": '{:10.0f}'.format(time.time()),
                                    "records": [],
                                    "framedata": framedata.hex(),

                                    }
                        for record in records:
                            vib = tuple(record.vib.parts)
                            func = record.dib.function_type.value
                            storage_number = record.dib.storage_number
                            key = (vib, func, storage_number)
                            if key in filter:
                                name = filter[key]
                                filtered['records'].append(record.interpreted)
                                # print(name)
                                #record = records[vib]
                                #print('{:10},{:30}:{}'.format(vib, record['type'], record['value']))
                                # value = record.value
                                # if type(value) is int:
                                #     print(' {:8} '.format(value), end='')
                                # else:
                                #     print(' {:10.8} '.format(value), end='')
                                #print()
                        import simplejson as json
                        print(json.dumps(filtered, sort_keys=True, indent=4, use_decimal=True))


                except KeyboardInterrupt:
                    pass

            elif meterbus.is_secondary_address(address):
                meterbus.send_select_frame(ser, address)
                try:
                    frame = meterbus.load(meterbus.recv_frame(ser, 1))
                except meterbus.MBusFrameDecodeError as e:
                    frame = e.value

                assert isinstance(frame, meterbus.TelegramACK)

                frame = None
                # ping_address(ser, meterbus.ADDRESS_NETWORK_LAYER, 0)

                meterbus.send_request_frame(
                    ser, meterbus.ADDRESS_NETWORK_LAYER)

                time.sleep(0.3)

                frame = meterbus.load(
                    meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))

                if frame is not None:
                    print(frame.to_JSON())

    except serial.serialutil.SerialException as e:
        print(e)


def key_capture_thread():
    global keep_going
    print("bla{} bla".format(input()))
    keep_going = False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Request data over serial M-Bus for devices.')
    parser.add_argument('-d', action='store_true',
                        help='Enable verbose debug')
    parser.add_argument('-b', '--baudrate',
                        type=int, default=2400,
                        help='Serial bus baudrate')
    parser.add_argument('-a', '--address',
                        type=str, default=meterbus.ADDRESS_BROADCAST_REPLY,
                        help='Primary or secondary address')
    parser.add_argument('-r', '--retries',
                        type=int, default=5,
                        help='Number of ping retries for each address')
    parser.add_argument('device', type=str, help='Serial device, URI or binary file')

    args = parser.parse_args()

    meterbus.debug(args.d)

    # thread.start_new_thread(key_capture_thread, ())

    try:
        mode = os.stat(args.device).st_mode
        if stat.S_ISREG(mode):
            do_reg_file(args)
        else:
            do_char_dev(args)
    except OSError:
        do_char_dev(args)

