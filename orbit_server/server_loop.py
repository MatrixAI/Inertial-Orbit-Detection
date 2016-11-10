import socketserver
import socket
import errno
import threading
import time
import re
import logging

class RotationTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server will be in its own thread, and handle TCP connection requests."""
    
    def __init__(
        self, 
        server_address, 
        RequestHandlerClass, 
        broadcaster,
        bind_and_activate=True,
    ):

        self.broadcaster = broadcaster
        socketserver.TCPServer.__init__(
            self, 
            server_address, 
            RequestHandlerClass, 
            bind_and_activate=bind_and_activate
        )

class RotationTCPHandler(socketserver.BaseRequestHandler):
    """On establishing a connection, this handler will handle the connection in a separate thread.

    It will push messages to the game client, and the pushing operation is synchronised 
    to the processing of a data window by the analysis loop. This is done via a broadcaster 
    performing fan-out between the main thread and the handler threads.

    All clients will be subscribers of the broadcaster, and the main thread will 
    broadcast new rotations per second and rotation direction.

    Handlers will eventually timeout in 10 seconds unless the client responds with an "OK" message.
    This is an application-level keepalive protocol because TCP keep alive does not work reliably 
    across all operating systems.

    The handler will not respond back to the client, it will only send rotation data.
    """

    def __init__(self, request, client_address, server):

        self.broadcaster = server.broadcaster
        self.channel = self.broadcaster.add_channel()
        
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

    def __del__(self):

        self.broadcaster.remove_channel(self.channel)
        
        s = super()
        if hasattr(s, "__del__"): 
            s.__del__(self)

    def handle(self):
        
        logging.info("Responding to new client: %s", self.request.getpeername())

        # this just means settimeout(0.0)
        # this is not the same as OS non-blocking socket, but achieves the same thing
        # see this: http://stackoverflow.com/a/16745561/582917   
        self.request.setblocking(False)

        # we expect a keep alive ping every once and a while
        # it can be in response to every message we send to the client
        # this allows us to end the connection handler in case the client quits without closing the connection
        # that way we don't have a resource leak
        ping_time = time.time()
        ping_timeout = 10

        client_input_buffer = bytearray()

        while True:

            # poll the client
            try:

                client_data = self.request.recv(64)

            except socket.error as e:

                # this exception is raised when no data is received, not socket.timeout
                if e.args[0] == errno.EWOULDBLOCK or e.args[0] == errno.EAGAIN:

                    # no data arrived, only check if the connection has timed out
                    # otherwise continue to the next step
                    if time.time() >= ping_time + ping_timeout:
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
                    self.request.sendall(bytes("S{0}:{1}E".format(rps, rotation_direction), 'ascii'))
                    logging.info("%d - Wrote RPS and RPS Direction to connection %s", trace_id, self.request.getpeername())
                except socket.error as e:
                    logging.exception("%d - Error writing to connection: %s", trace_id, self.request.getpeername())
                    break

            # handle the client_data
            # if the client_data is None, then nothing was sent at all
            if client_data is not None:

                # if the length of the received data is 0 then it's an EOF character
                if len(client_data) > 0:

                    # extend the buffer indefinitely until we get a token
                    # this is equivalent to a multiple input buffering scheme
                    # an extension of the buffering pair scheme
                    client_input_buffer.extend(client_data)
                    
                    # the regular expression always match something or nothing, it will not return None
                    lexical_analysis = re.search(self.message_protocol, client_input_buffer.decode('ascii'))
                    
                    # a token may not be extracted, if so, we just just pass to the next stage
                    token = lexical_analysis.group(1)

                    if token == "OK":
                        ping_time = time.time()

                    # drops the handled input and characters before the start frame
                    client_input_buffer = client_input_buffer[lexical_analysis.span()[1]:]

                else:

                    logging.info("Client closed connection: %s", self.request.getpeername())
                    break

            time.sleep(0)
      
        # event loop for the connection was broken, so here we just clean up the connection and pinging action 
        logging.info("Closing connection to: %s", self.request.getpeername()) 

        self.request.close()

def start(host, port, broadcaster):
    
    logging.info("Running Server Loop")
    server = RotationTCPServer((host, port), RotationTCPHandler, broadcaster)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server
