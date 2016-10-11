import socketserver
import threading
import logging
import timer

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
        super().__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        # try the super method instead first
        # MRO shouuld eventually find __init__ with socketserver.TCPServer
        # socketserver.TCPServer.__init__(
        #     self, 
        #     server_address, 
        #     RequestHandlerClass, 
        #     bind_and_activate=bind_and_activate
        # )

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
        super().__init__(request, client_address, server) # try if this works
        # socketserver.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        logging.info("Responding to new client: {}", self.request.getpeername())
        self.request.settimeout(5)
        try:
            while True:
                # wait on client to ask for data first (it can be anything)
                if not (self.request.recv(1024)): break
                # send `output_direction:output_rps`
                self.request.sendall(bytes("^{0}:{1}\n".format(output_direction, output_rps), 'ascii'))

                # use self.channel to synchronise the pushing of messages
                # but how to check on both events
                # from the client, and events from the analysis loop?

                # yield to other threads
                timer.sleep(0)
            logging.info("Client: {} closed connection.", self.request.getpeername())
        except:
            logging.info("Timed out waiting for client, closing connection to client: {}", self.request.getpeername())

def start(host, port, channel):
    logging.info("Running Server Loop")
    server = RotationTCPServer((host, port), RotationTCPHandler, channel)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server