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

final int wallSpeed = 3;
final int wallInterval = 1600;
final int wallWidth = 80;
final float wallLastAddTime = 0;
final color wallColors = color(240, 248, 255);
final int minGapHeight = 250;
final int maxGapHeight = 300;

//////////////////////
// Network Settings //
//////////////////////

final int pingPongTimeout = 5;
final int pingPongInterval = 2; 
final Pattern messageProtocol = Pattern.compile("^(?:[^S]*)(?:S(.*?)E)?");
final String rpsAndDirTokenRegex = "(-?[0-1]):((?:[0-9]*[.])?[0-9]+)";