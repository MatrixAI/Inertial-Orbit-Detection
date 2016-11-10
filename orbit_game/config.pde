import java.util.regex.Pattern;

/////////////////////
// Visual Settings //
/////////////////////

// pixel radius of the balloon
final int hotBalloonSize = 25;
// default screen width
final int defaultGameWidth = 500;
// default screen height
final int defaultGameHeight = 500;

///////////////////
// Game Settings //
///////////////////

// assume pixels are meters
// factor conversion of RPS to force in newtons
final float rotationRPSToForceFactor = 4.0;
// gravity in pixels/second^2
final float gravity = -9.8;
// weight in kg
final float hotBalloonWeight = 10;
// velocity in pixels/second
final float hotBalloonHoriVelocity = 1.0;
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