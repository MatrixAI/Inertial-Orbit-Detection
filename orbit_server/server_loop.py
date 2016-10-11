# this will be the server loop running in multithreaded
import socketserver

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server will be in its own thread, and handle TCP connection requests."""
    pass

# TCP request handling will be in its own thread
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """On establishing a connection, this handler will handle the connection.

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

    def handle(self):
        print("Responding to new client: {}".format(self.request.getpeername()))
        self.request.settimeout(5)
        try:
            while True:
                # wait on client to ask for data first (it can be anything)
                if not (self.request.recv(1024)): break
                # send `output_direction:output_rps`
                self.request.sendall(bytes("^{0}:{1}\n".format(output_direction, output_rps), 'ascii'))
            print("Client: {} closed connection.".format(self.request.getpeername()))
        except:
            print("Timed out waiting for client, closing connection to client: {}".format(self.request.getpeername()))
