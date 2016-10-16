import socketserver
import socket
import threading
import queue
import select
import time
import re
import logging


class RotationTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server will be in its own thread, and handle TCP connection requests."""
    
    def __init__(
        self, 
        server_address, 
        RequestHandlerClass, 
        channel
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
        # like `Sabcdefg...`
        self.game_protocol = re.compile(
            """
                ^
                (?:[^S]*)  # drop everything before the frame start, this gives us the drop range
                (?:S(    # frame start
                    .*?
                )E)?     # frame end
            """, 
            re.X
        )

        super().__init__(request, client_address, server)
        # socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def graceful_close(socket):

        socket.shutdown(socket.SHUT_RDWR)
        socket.close()
        return

    def handle(self):
        
        logging.info("Responding to new client: {}", self.request.getpeername())

        # this just means settimeout(0.0)
        # this is not the same as OS non-blocking socket, but achieves the same thing
        # see this: http://stackoverflow.com/a/16745561/582917   
        self.request.setblocking(False)

        # we will use a PING PONG protocol for keeping alive this connection
        # this is because TCP keepalive is not easily usable on all OS platforms
        ping_pong_time = int(time.time())
        ping_pong_timeout = 5

        client_input_buffer = bytearray()

        while True:
            
            # PING the client
            try: 
                self.request.sendall(b"SPINGE")
            except: 
                logging.exception("Error in writing to socket, closing connection to: {}", self.request.getpeername())
                self.graceful_close(self.request)
                return

            # poll the client
            try:

                client_data = self.request.recv(64)

            except socket.timeout:

                # no data arrived, only check if the ping pong protocol timed out
                # otherwise continue to the next step
                if int(time.time()) > ping_pong_time + ping_pong_timeout:
                    logging.info("Client timed out, closing connection to: {}", self.request.getpeername())
                    self.request.shutdown(socket.SHUT_RDWR)
                    self.request.close()
                    return
                else:
                    client_data = None

            # socket.error is more general than socket.timeout, it must be caught later
            except socket.error as e:

                logging.exception("Error in reading from socket, closing connection to: {}", self.request.getpeername())
                self.graceful_close(self.request)
                return

            # poll the channel, if the channel is empty, it raises an exception
            try:
                server_data = self.channel.get_nowait()
            except queue.Empty:
                server_data = None

            # handle the server_data
            if server_data is not None:

                (rps, rotation_direction) = server_data
                try:
                    # blocks until all data is sent (it doesn't necessarily wait for ACKs)
                    self.request.sendall(bytes("S{0}:{1}E".format(rps, rotation_direction), 'ascii'))
                except socket.error as e:
                    logging.exception("Error in writing to socket, closing connection to: {}", self.request.getpeername())
                    self.graceful_close(self.request)
                    return

            # handle the client_data
            if client_data is not None:

                if len(client_data) > 0:

                    # extend the buffer indefinitely until we get a token
                    # this is equivalent to a multiple input buffering scheme
                    # an extension of the buffering pair scheme
                    client_input_buffer.extend(client_data)
                    
                    # the regular expression always match something or nothing, it will not return None
                    lexical_analysis = re.search(self.game_protocol, client_input_buffer.decode('ascii'))
                    
                    # a token may not be extracted, if so, we just just pass to the next stage
                    token = lexical_analysis.group(1)
                    if token:
                        if   token == "PING":

                            ping_pong_time = int(time.time())
                            try: 
                                self.request.sendall(b"SPONGE")
                            except: 
                                logging.exception("Error in writing to socket, closing connection to: {}", self.request.getpeername())
                                self.graceful_close(self.request)
                                return

                        elif token == "PONG":

                            ping_pong_time = int(time.time())

                    # drops the handled input and characters before the start frame
                    client_input_buffer = client_input_buffer[lexical_analysis.span()[1]:]

                else:

                    # this means we received EOF character from the client
                    logging.info("Client closed connection, closing connection to: {}", self.request.getpeername())
                    self.graceful_close(self.request)
                    return

            time.sleep(0)

def start(host, port, channel):
    
    logging.info("Running Server Loop")
    server = RotationTCPServer((host, port), RotationTCPHandler, channel)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server