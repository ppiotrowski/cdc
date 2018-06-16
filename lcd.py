#!/usr/bin/python
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import Image
import ImageDraw
import ImageFont
import time

RST = 24
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
disp.begin()
disp.clear()
disp.display()

width = disp.width
height = disp.height

#disp.clear()
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
font = ImageFont.truetype('/home/pi/player/font1.ttf', 14)	
text = '...BOOT...'
w, h = draw.textsize(text, font=font)
draw.text(((width / 2) - (w / 2), (height / 2) - (h / 2)), text, font=font, fill=255)

disp.image(image)
disp.display()