#!/usr/bin/env python

'''
Usage:
    bliss_tlm_serve.py [options] <pcap-filename>

Arguments:
    -p, --port=<number>     Port to serve up telemetry data [default: 3076]
    -v, --verbose           Report every packet sent

Description:
    Sends the telemetry contained in the given pcap file via TCP server
    connections.

    NOTE: This telemetry server should be started BEFORE the GUI because
    the GUI client does not attempt to reconnect to servers after startup.


Examples:

    $ bliss-tlm-serve.py test/data/pcap/oco3fsw-iss1553-2015-04-22.pcap

'''

from docopt import docopt

# import socket
import gevent

import bliss

clients = { }

def send(data):
    """Sends data to all registered clients.  Deregisters clients on I/O error."""
    for address, socket in clients.items():
        try:
            socket.sendall(data)
            failed = 0
        except IOError:
            del clients[address]
            failed = failed + 1

def on_connect(socket, address):
    """Registers newly connected clients to receive data via send()."""
    global clients
    clients[address] = socket

if __name__ == '__main__':
    args = docopt(__doc__)

    try:

        bliss.log.begin()

        filename = args.pop('<pcap-filename>')
        port = int(args.pop('--port'))
        verbose = args.pop('--verbose')

        host = 'localhost'

        if not verbose:
            bliss.log.info('Will only report every 10 telemetry packets')
            bliss.log.info('Will only report long telemetry send delays')

        print host
        print port
        server = gevent.server.StreamServer((host, port), on_connect)
        server.start()

        with bliss.pcap.open(filename, 'r') as stream:
            npackets = 0
            prev_ts  = None

            for header, packet in stream:
                if prev_ts is None:
                    prev_ts = header.ts

                delay = header.ts - prev_ts

                if delay >= 2:
                    bliss.log.info('Next telemetry in %1.2f seconds' % delay)

                gevent.sleep(delay)

                nbytes = len(packet)

                if npackets == 0:
                    bliss.log.info('Sent first telemetry packet (%d bytes)' % nbytes)
                elif verbose:
                    bliss.log.info('Sent telemetry (%d bytes)' % nbytes)
                elif npackets % 10 == 0:
                    bliss.log.info('Sent 10 telemetry packets')

                send(packet)

                npackets += 1
                prev_ts   = header.ts

    except KeyboardInterrupt:
        bliss.log.info('Received Ctrl-C.  Stopping telemetry stream.')

    except Exception as e:
        bliss.log.error('TLM send error: %s' % str(e))

    bliss.log.end()