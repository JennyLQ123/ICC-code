import turtle
import time
import sys

model=sys.argv[1]

turtle.speed(10)
turtle.ht()
turtle.setup(width=0.75, height=0.75)
#turtle.screensize(canvwidth=800, canvheight=600)
for i in range(20):
    turtle.clear()
    turtle.Screen().bgpic("virpng/%s-%d.png"%(model,i))
    turtle.penup()
    turtle.goto(-450,200)
    turtle.color("blue")
    turtle.write("%s-%d"%(model,i),font=("Times",22,"bold"))
    turtle.end_fill()
    time.sleep(1)
turtle.done()
