import java.util.regex.Pattern;

/////////////////////
// Visual Settings //
/////////////////////

// pixel radius factor of the balloon applied onto game width
final float hotBalloonSizeFactor = 0.052;
// default screen width
final int defaultGameWidth = 1000;
// default screen height
final int defaultGameHeight = 1000;

///////////////////
// Game Settings //
///////////////////

final String defaultServerAddress = "127.0.0.1";
final int    defaultServerPort = 55555;

// assume pixels are meters
// factor conversion of RPS to force in newtons
final float rotationRPSToForceFactor = 9000.0;
// gravity in pixels/second^2
final float gravity = -30;
// weight in kg
final float hotBalloonWeight = 6;
// velocity factor applied onto game screen width to calculate pixels/second
final float hotBalloonHoriVelocityFactor = 0.12;
// the random range of distance between walls
final float wallMinIntervalFactor = 0.1;
final float wallMaxIntervalFactor = 0.5;
// the random range of gap height for each wall
final float wallMinGapFactor = 0.3;
final float wallMaxGapFactor = 0.8;
// wall width
final float wallMinWidthFactor = 0.1;
final float wallMaxWidthFactor = 0.2;

//////////////////////
// Network Settings //
//////////////////////

final int pingPongTimeout = 5;
final int pingPongInterval = 2; 
final Pattern messageProtocol = Pattern.compile("^(?:[^S]*)(?:S(.*?)E)?");
final String rpsAndDirTokenRegex = "((?:[0-9]*[.])?[0-9]+):(-?[0-1])";