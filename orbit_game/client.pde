import processing.net.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

StringBuilder messageBuffer = new StringBuilder();

class ClientData {

    Float rps;
    Integer direction;

    ClientData(Float rps, Integer direction) {
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
 * Checks if it is the right time to ping the Orbit Server for liveness.
 * Returns true if it checked, returns false it hasn't checked.
 * The caller needs to update the pingPongSendTime if true is returned.
 */
boolean clientPingCheck(Client client, int pingPongInterval, int pingPongSendTime, int currentTime) {

    if (!client.active()) {
        return false;
    }

    if (currentTime >= (pingPongSendTime + pingPongInterval)) {
        client.write("SPINGE");
        return true;
    }

    return false;

}

/**
 * Checks if the connection hasn't timed out according to the ping pong protocol.
 * Also checks if the connection is still active.
 * The caller should handle a timed-out or closed connection appropriately.
 */
boolean clientPongCheck(Client client, int pingPongTimeout, int pingPongReceiveTime, int currentTime) {

    if (!client.active()) {
        return false;
    }

    if (currentTime >= (pingPongReceiveTime + pingPongTimeout)) {
        return false; 
    }

    return true;

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
    boolean acquired = false;

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

                // we have acquired a message token
                acquired = true;

                // process the message token
                rpsAndDirMatches = match(token, rpsAndDirRegex);
                if (rpsAndDirMatches == null) {
                    switch (token) {
                        case "PING":
                            client.write("SPONGE");
                        break;
                        case "PONG":
                            // pass
                        break;
                    }
                }

            }

            this.messageBuffer.delete(lexer.start(), lexer.end());

        }

    }

    if (acquired) {

        // if just get a PING/PONG message, then its still client data, but no rps and dir updates
        if (rpsAndDirMatches != null) {

            return new ClientData(
                float(rpsAndDirMatches[0]), 
                int(rpsAndDirMatches[1])
            );

        } else {

            return new ClientData(
                null,
                null
            );

        }

    } else {

        return null;

    }

}