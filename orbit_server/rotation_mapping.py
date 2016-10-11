'''
There are 4 quadrants to a circular motion.

The 4 quadrants can be grouped into 4 semicircles:
    
    * the bottom semicircle
    * the top semicircle
    * the left semicircle
    * the right semicircle

If we project a circular motion onto the horizontal axis, we see that the change 
between left to right semicircle will register a change in acceleration 
direction on the horizontal axis.

If we project a circular motion onto the vertical axis, we see that the change 
between bottom to top semicircle will register a change in acceleration 
direction on the vertical axis.

Visually speaking, the first diagram below shows for a clockwise rotation, the 
change-over in horizontal acceleration direction when the orbiting device is at 
the top and bottom of its rotational circle.

                                     RtL
                                     -|-  
                                    / | \ 
    Accelerating to Left ----->>   |  |  |   <<------ Accelerating to Right
                                    \ | / 
                                     -|-  
                                     LtR

This diagram shows velocity direction and velocity magnitude for a horizontally 
projected motion of a clockwise orbiting device.

                               * ->
                                 * --> 
                                   * --->
                                     * ---->
                                       * --->
                                         * -->
                                           * ->
                                          <- *
                                       <-- *
                                    <--- *
                                 <---- *
                                <--- *
                               <-- *
                              <- *
                               * ->
                                 * --> 
                                   * --->
                                     * ---->
                                       * --->
                                         * -->
                                           * ->
             

For a vertically projected motion, similar graphs will appear, however they will 
be rotationed 90 degrees (to the right for a clockwise motion or left for an 
anticlockwise motion).

In conclusion, we should see a mapping from position to acceleration direction: 

    * left semicircle   = right acceleration
    * right semicircle  = left acceleration
    * top semicircle    = down acceleration
    * bottom semicircle = up acceleration

The displacement, velocity and acceleration will all be a sine wave when graphed 
onto a time axis.

To find out whether the motion is really clockwise or anticlockwise, we still 
need 1 more piece of knowledge. This is the change in acceleration vectors 
between 2 time-adjacent samples or any time interval.

We can find the change acceleration vector for any given time interval by 
looking at the X & Z acceleration values for T1 and comparing with X & Z 
acceleration values at T2.

For now we do not care about Y acceleration values, because we only care about 
2D orbit and not a 3D orbit.

Because a user can reverse their direction of rotation in between a data window, 
we will be doing a majority vote between all time interval calculations in order 
to tell us what the majority rotation direction is for the given data window.

If the data window is not periodic, but a rolling data window, we should instead 
perform a weighted majority vote, weighing on the more recent samples.
'''

# This is mapping from the sign of the acceleration vector deltas to rotational 
# tangent direction.
# 
# The keys are in the form of (East Axis Delta Sign, Up Axis Delta Sign).
#
# +,+ => NE
# +,- => SE
# -,- => SW
# -,+ => NW
# 0,+ => N
# 0,- => S
# +,0 => E
# -,0 => W
# 0,0 => ?
accel_vector_delta_direction_mapping = {
    (1 ,  1): 'NE',
    (1 , -1): 'SE',
    (-1, -1): 'SW',
    (-1,  1): 'NW',
    (0 ,  1): 'N',
    (0 , -1): 'S',
    (1 ,  0): 'E',
    (-1,  0): 'W',
    (0 ,  0): '?'
}

# This is mapping from the sign of the acceleration vector to rotational 
# position.
# 
# The keys are in the form of (East Axis Sign, Up Axis Sign).
# 
# +,+ => Left Bottom Quadrant
# +,- => Left Top Quadrant
# -,- => Right Top Quadrant
# -,+ => Right Bottom Quadrant
# 0,+ => Bottom Semicircle
# 0,- => Top Semicircle
# +,0 => Left Semicircle
# -,0 => Right Semicircle
# 0,0 => ?
accel_vector_position_mapping = {
    (1 ,  1): 'LB',
    (1 , -1): 'LT',
    (-1, -1): 'RT',
    (-1,  1): 'RB',
    (0 ,  1): 'B',
    (0 , -1): 'T',
    (1 ,  0): 'L',
    (-1,  0): 'R',
    (0 ,  0): '?'
}

# This is a mapping from:
#   1. acceleration vector delta direction
#   2. acceleration vector position 
# to clockwise or anti-clockwise.
# 
# 1 represents clockwise.
# -1 represents anticlockwise.
# 
# The opposite of the acceleration vector delta direction is the tangential 
# rotational direction.
# 
# NE - LT => anticlockwise
# NE - RB => clockwise
# NE - L  => anticlockwise
# NE - B  => clockwise
# NE - *  => ?
#  
# SE - LB => clockwise
# SE - RT => anticlockwise
# SE - L  => clockwise
# SE - T  => anticlockwise
# SE - *  => ?
# 
# SW - LT => clockwise
# SW - RB => anticlockwise
# SW - R  => anticlockwise
# SW - T  => clockwise
# SW - *  => ?
# 
# NW - RT => clockwise
# NW - LB => anticlockwise
# NW - R  => clockwise
# NW - B  => anticlockwise
# NW - *  => ?
# 
# (all of these below is rare or impossible because it requires T1 and T2 to be at the same position)
# 
# N - L => anticlockwise
# N - R => clockwise
# N - * => ?
# 
# S - L => clockwise
# S - R => anticlockwise
# S - * => ?
# 
# E - T => anticlockwise
# E - B => clockwise
# E - * => ?
# 
# W - T => clockwise
# W - B => anticlockwise
# W - * => ?
accel_vector_direction_and_position_mapping = {
    ('NE', 'LT'): -1,
    ('NE', 'RB'):  1,
    ('NE', 'L' ): -1,
    ('NE', 'B' ):  1,
    ('SE', 'LB'):  1,
    ('SE', 'RT'): -1,
    ('SE', 'L' ):  1,
    ('SE', 'T' ): -1,
    ('SW', 'LT'):  1,
    ('SW', 'RB'): -1,
    ('SW', 'R' ): -1,
    ('SW', 'T' ):  1,
    ('NW', 'RT'):  1,
    ('NW', 'LB'): -1,
    ('NW', 'R' ):  1,
    ('NW', 'B' ): -1,
    ('N' , 'L' ): -1,
    ('N' , 'R' ):  1,
    ('S' , 'L' ):  1,
    ('S' , 'R' ): -1,
    ('E' , 'T' ): -1,
    ('E' , 'B' ):  1,
    ('W' , 'T' ):  1,
    ('W' , 'B' ): -1
}