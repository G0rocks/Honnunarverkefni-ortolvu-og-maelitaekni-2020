import termplotlib as tpl
import numpy

x = numpy.linspace(0,2*numpy.pi,10)
y = numpy.sin(x)

fig = tpl.figure()
fig.plot(x, y, label ="data", width=50, height=15)
fig.show()
