import processing.net.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

StringBuilder messageBuffer = new StringBuilder();

class ClientData {

    float rps;
    int direction;

    ClientData(float rps, int direction) {
        this.rps = rps;
        this.direction = direction;
    }

}

/**
 * Established a new TCP connection to the Orbit Server.
 * Since Processing's Client doesn't throw exceptions, it'll check if the connection worked.
 * It also clears any data in the client buffer.
 */
Client clientEstablish(String serverAddress, int serverPort) {
    
    Client client = new Client(this, serverAddress, serverPort);
    if (!client.active()) {
        return null;
    }
    client.clear();
    return client;

}

/**
 * Shutsdown the client if is still active, will also clear the buffer.
 */
void clientShutdown(Client client) {

    if (client != null && client.active()) {
        client.clear();
        client.stop();
    }
    
}

/**
 * Polls the connection and tries to acquire a message frame.
 * Will buffer the byte-stream content until a message frame is available.
 * This is non-blocking, it will just return what is available.
 * The caller must update the pingPongReceiveTime if any ClientData is returned.
 * However the properties of ClientData may be null, if the message was not a RPS and direction message.
 */
ClientData clientRead(Client client, Pattern messageProtocol, String rpsAndDirRegex) {

    Matcher lexer;
    String token;
    String[] rpsAndDirMatches = null;

    // if the client connection was dropped, just return null
    if (!client.active()) {
        return null;
    }

    if (client.available() > 0) {

        this.messageBuffer.append(client.readString());
        lexer = messageProtocol.matcher(this.messageBuffer.toString());

        if (lexer.find()) {

            token = lexer.group(1);
            if (token != null) {

                // process the message token
                rpsAndDirMatches = match(token, rpsAndDirRegex);
                if (rpsAndDirMatches != null) {
                    
                    client.write("SOKE");

                    return new ClientData(
                        float(rpsAndDirMatches[1]), 
                        int(rpsAndDirMatches[2])
                    );
                    
                }

            }

            this.messageBuffer.delete(lexer.start(), lexer.end());

        }

    }
    
    return null;

}