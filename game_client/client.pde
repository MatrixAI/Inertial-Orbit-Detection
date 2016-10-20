import processing.net.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

StringBuilder message_buffer = new StringBuilder();
Pattern game_protocol = Pattern.compile("^(?:[^S]*)(?:S(.*?)E)?");
String rpsAndDirRegex = "(-?[0-1]):((?:[0-9]*[.])?[0-9]+)";

class ClientUpdate {

    float rps;
    int direction;
    int pingPongTime;

    ClientUpdate(float rps, int direction, int pingPongTime) {
        this.rps = rps;
        this.direction = direction;
        this.pingPongTime = pingPongTime;
    }

}

Client clientEstablish(serverAddress, serverPort) {
    
    Client client = new Client(this, serverAddress, serverPort);
    if (!client.active()) {
        return null;
    }
    client.clear();
    return client;

}

void clientShutdown(Client client) {

    // find out if this works with non-active connection
    client.clear();
    client.stop();

}

boolean clientPing(Client client) {

    if (client.active()) {
        client.write("SPINGE");
        return true;
    }
    return false;

}

boolean clientLiveCheck(Client client, int pingPongTimeout, int pingPongTime) {

    if (!client.active()) {
        return false;
    }

    long currentTime = System.currentTimeMillis() / 1000L;
    if (currentTime > (pingPongTime + pingPongTimeout)) {
        return false;    
    }

    return true;

}

ClientUpdate clientRead(Client client, int pingPongTime) {

    Matcher lexer;
    String token;
    String[] rpsAndDirMatches;
    boolean acquired = false;

    // if the client connection was dropped, just return null
    if (!client.active()) {
        return null;
    }

    if (client.available() > 0) {

        this.message_buffer.append(client.readString());
        lexer = this.game_protocol.matcher(this.message_buffer.toString());

        if (lexer.find()) {

            token = lexer.group(1);
            if (token != null) {

                // we have acquired a message token
                acquired = true;

                // process the message token
                rpsAndDirMatches = match(rpsAndDirString, this.rpsAndDirRegex);
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

                // since the server responded, we just update the ping pong time
                pingPongTime = millis() / 1000;

            }

            this.message_buffer.delete(lexer.start(), lexer.end());

        }

    }

    if (acquired) {

        return new ClientUpdate(
            float(rpsAndDirMatches[0]), 
            int(rpsAndDirMatches[1]),
            pingPongTime
        );

    } else {

        return null;

    }

}
