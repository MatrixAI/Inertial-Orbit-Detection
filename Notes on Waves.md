The first step to understand sine formulas:

40 Revolutions Per Minute = 0.6* Revolutions Per Second.
Therefore 1 revolution should take 1.5 seconds.

This should be equal to 0.6* Hz on our graph.
The frequency on our chart should be 0.6* Hz.
And the the wavelength should equal 1500 milliseconds.

```
y(t) = A * sin (2 * pi * f * t + p)

A amplitude => 45
f frequency => (1/1.5)
p phase offset => ?

y(t) = 45 * sin (2 * pi * (1/1.5) * t + phi)
y(t) = 45 * sin (2 * pi * (1/1.5) * t)
```

This is a graph over seconds.
But we can create a graph over milliseconds

http://obogason.com/fundamental-frequency-estimation-and-machine-learning/
http://tkf.github.io/2010/10/03/estimate-frequency-using-numpy.html
https://gist.github.com/endolith/255291
http://exnumerus.blogspot.com.au/2010/04/how-to-fit-sine-wave-example-in-python.html
http://scipy-cookbook.readthedocs.io/items/FittingData.html

The `fs` appears to the number of samples in the sample set.

A phase is the position of an instant on a waveform cycle. A 0 degree or 360 degree phase is equivalent to the starting point point of a wave. 180 degrees is in the middle of the wave. 90 degrees is the crest and 270 degrees is trough of the wave. We are talking about the bump then dump.

Phase velocity = Wavelength divided by Period. Period is the time it takes to go from 1 crest to another crest, so basically start to a finish of a wave cycle. Frequency is the number of cycles per second. 

When the wavelength and period is the same, then the phase velocity is 1. Wavelength is measured in meters, while period is measured in seconds.

> Wavelength is given by the distance between two successive peaks/troughs in a displacement vs. position graph.
> Period is given by the distance between two successive peaks in a displacement vs. time graph.

```
l = lambda
v = phase velocity
f = frequency
T = period

     v
l = ---
     f

     v
f = ---
     l

     1
f = ---
     T

     l
v = ---
     T
```

Ok so basically we don't have wavelength. We just have period.

Our period is 1.5 seconds.
