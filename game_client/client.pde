import java.util.regex.Matcher;
import java.util.regex.Pattern;

StringBuilder message_buffer = new StringBuilder();

Pattern game_protocol = Pattern.compile("^(?:[^S]*)(?:S(.*?)E)?");
// we also have to deal with other tokens
String message_regex = "(-?[0-1]):((?:[0-9]*[.])?[0-9]+)";

class RPSAndDir {

    float rps;
    int direction;
    Combo(float rps, int direction) {
        this.rps = rps;
        this.direction = direction;
    }

}

void clientPingPongCheck(Client client, long pingPongTime) {

    client.write("SPINGE");

    // send a PING regardless
    // if the server failed to answer a pong in time
    // return false, the client connection should be retried

}

RPSAndDir clientReadOrbitServer(Client client, long pingPongTime) {

    Matcher lexer;
    String token;
    String[] rpsAndDirMatches;

    if (client.available() > 0) {
        message_buffer.append(client.readString());
        lexer = game_protocol.matcher(message_buffer.toString());
        if (lexer.find()) {
            token = lexer.group(1);
            if (token != null) {

                rpsAndDirMatches = match(rpsAndDirString, message_regex);
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

                pingPongTime = System.currentTimeMillis() / 1000L;

            }
            message_buffer.delete(lexer.start(), lexer.end());
        }
    }

    // WE NEED to return the new pingPongTime here

    if (rpsAndDirMatches != null) {
        return new RPSAndDir(float(rpsAndDirMatches[0]), int(rpsAndDirMatches[1]));
    } else {
        return null;
    }

}