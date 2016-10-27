import socketserver
import socket
import errno
import threading
import queue
import select
import time
import re
import logging

class TimerForever():

    def __init__(self, interval, callback, args=[], kwargs={}):
        self.interval = interval
        self.callback = callback 
        self.args = args
        self.kwargs = kwargs
        self.thread = threading.Timer(self.interval, self.call_callback)

    def call_callback(self):
        self.callback(*self.args, **self.kwargs)
        self.thread = threading.Timer(self.interval, self.call_callback)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        if self.thread.is_alive():
            self.thread.cancel()


class RotationTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server will be in its own thread, and handle TCP connection requests."""
    
    def __init__(
        self, 
        server_address, 
        RequestHandlerClass, 
        channel,
        bind_and_activate=True,
    ):

        self.channel = channel
        socketserver.TCPServer.__init__(
            self, 
            server_address, 
            RequestHandlerClass, 
            bind_and_activate=bind_and_activate
        )

class RotationTCPHandler(socketserver.BaseRequestHandler):
    """On establishing a connection, this handler will handle the connection in a separate thread.

    It will push messages to the game client, and the pushing operation is synchronised 
    to the processing of a data window by the analysis loop. This is done via a queue 
    channel between the main thread and this handler thread.

    All clients will be subscribers of this queue channel, and the main thread will 
    broadcast new rotations per second and rotation direction to the queue channel.

    Handlers will also perform application-level keepalive protocol of PING PONG. 
    This is because TCP keep alive does not work reliably across all operating systems.

    The client is expected to send PINGs across the duration of the connection.
    The client may also receive PINGs from the server, and will need to respond to it.
    """

    def __init__(self, request, client_address, server):

        self.channel = server.channel
        
        # this regular expression will always succeed and match something or nothing
        # a problem with this is it can receive a DOS if a client sends a large message of garbage
        self.message_protocol = re.compile(
            """
                ^
                (?:[^S]*) # drop everything before the frame start, this gives us the drop range
                (?:S(     # frame start
                    .*?
                )E)?      # frame end
            """, 
            re.X
        )

        super().__init__(request, client_address, server)
        # socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def server_ping(self, interval, fail_event):

        ping_action = None

        def ping():
            try:
                self.request.sendall(b"SPINGE");
            except:
                fail_event.set()
                ping_action.cancel()

        ping_action = TimerForever(interval, ping)

        return ping_action


    def handle(self):
        
        logging.info("Responding to new client: %s", self.request.getpeername())

        # this just means settimeout(0.0)
        # this is not the same as OS non-blocking socket, but achieves the same thing
        # see this: http://stackoverflow.com/a/16745561/582917   
        self.request.setblocking(False)

        # we will use a PING PONG protocol for keeping alive this connection
        # this is because TCP keepalive is not easily usable on all OS platforms
        # ping timeout will be 5 seconds, and pinging interval will be 2 seconds
        # the pinging action will take place in a separate thread
        # if the pinging action fails, it will signal failure via the ping_pong_fail_event
        ping_pong_time    = int(time.time())
        ping_pong_timeout = 5
        ping_pong_failure = threading.Event()
        ping_action       = self.server_ping(2, ping_pong_failure)

        client_input_buffer = bytearray()

        while True:
            
            # poll for the pinging action failure
            if (ping_pong_failure.is_set()): 
                logging.exception("Error pinging client: %s", self.request.getpeername())
                break

            # poll the client
            try:

                client_data = self.request.recv(64)

            except socket.timeout:

                # no data arrived, only check if the ping pong protocol timed out
                # otherwise continue to the next step
                if int(time.time()) >= ping_pong_time + ping_pong_timeout:
                    logging.info("Client timed out: %s", self.request.getpeername())
                    break 
                else:
                    client_data = None

            # socket.error is more general than socket.timeout, it must be caught later
            except socket.error as e:

                # this is the exception that is raised when no data is received, not socket.timeout
                if e.args[0] == errno.EWOULDBLOCK:

                    # no data arrived, only check if the ping pong protocol timed out
                    # otherwise continue to the next step
                    if int(time.time()) >= ping_pong_time + ping_pong_timeout:
                        logging.info("Client timed out: %s", self.request.getpeername())
                        break 
                    else:
                        client_data = None

                else:

                    logging.exception("Error in reading from connection: %s", self.request.getpeername())
                    break 

            # poll the channel
            try:
                server_data = self.channel.pop()
            except IndexError:
                server_data = None

            # handle the server_data
            if server_data is not None:

                (rps, rotation_direction, trace_id) = server_data
                try:
                    logging.info("%d - Wrote RPS and RPS Direction to connection %s", trace_id, self.request.getpeername())
                    self.request.sendall(bytes("S{0}:{1}E".format(rps, rotation_direction), 'ascii'))
                except socket.error as e:
                    logging.exception("%d - Error writing to connection: %s", trace_id, self.request.getpeername())
                    break

            # handle the client_data
            if client_data is not None:

                if len(client_data) > 0:

                    # extend the buffer indefinitely until we get a token
                    # this is equivalent to a multiple input buffering scheme
                    # an extension of the buffering pair scheme
                    client_input_buffer.extend(client_data)
                    
                    # the regular expression always match something or nothing, it will not return None
                    lexical_analysis = re.search(self.message_protocol, client_input_buffer.decode('ascii'))
                    
                    # a token may not be extracted, if so, we just just pass to the next stage
                    token = lexical_analysis.group(1)
                    if token:
                        if   token == "PING":

                            ping_pong_time = int(time.time())
                            
                            try: 
                                self.request.sendall(b"SPONGE")
                            except: 
                                logging.exception("Error writing to connection: %s", self.request.getpeername())
                                break

                        elif token == "PONG":

                            ping_pong_time = int(time.time())

                    # drops the handled input and characters before the start frame
                    client_input_buffer = client_input_buffer[lexical_analysis.span()[1]:]

                else:

                    # this means we received EOF character from the client
                    logging.info("Client closed connection: %s", self.request.getpeername())
                    break

            time.sleep(0)
      
        # event loop for the connection was broken, so here we just clean up the connection and pinging action 
        logging.info("Closing connection to: %s", self.request.getpeername()) 

        ping_action.cancel()
        self.request.close()

def start(host, port, channel):
    
    logging.info("Running Server Loop")
    server = RotationTCPServer((host, port), RotationTCPHandler, channel)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server
