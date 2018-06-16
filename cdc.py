#!/usr/bin/python
import ConfigParser
import ctypes
import glob
import io
import locale
import logging
import logging.config
import os
import RPi.GPIO as GPIO  ## Import GPIO library
import usb.core
import usb.util
from time import sleep
import time
import os
import subprocess
from mpd import MPDClient
mpd = MPDClient()               # create client object
mpd.timeout = 10                # network timeout in seconds (floats allowed), default: None
mpd.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None
mpd.connect("localhost", 6600)

from pybtooth import BluetoothManager

bm = BluetoothManager()

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import Image
import ImageDraw
import ImageFont

RST = 24
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
disp.begin()
disp.clear()
disp.display()

filename = ''

width = disp.width
height = disp.height

disp.clear()
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
font = ImageFont.truetype('font1.ttf', 14)
text = 'Start player...'
w, h = draw.textsize(text, font=font)
draw.text(((width / 2) - (w / 2), (height / 2) - (h / 2)), text, font=font, fill=255)

disp.image(image)
disp.display()

lcdt = 0
power_off = 0
lcd_state = ''

def update_lcd():
    global lcdt
    global filename
    global lcd_state
    new_lcd_state = filename+str(power_off)+str(bluetooth)+str(usb_storage)

    #if(lcd_state==new_lcd_state):
#	return
    # disp.begin()
    disp.clear()
    if(power_off==1):
	return
    lcd_state=new_lcd_state
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    font = ImageFont.truetype('font1.ttf', 14)

    if ((bluetooth and lcdt<10) or bluetooth_mp):
        # draw BT icon
        draw.line((width - 4, 0, width - 4, 10), fill=255)
        draw.line((width - 3, 1, width - 1, 3), fill=255)
        draw.line((width - 6, 8, width - 1, 3), fill=255)
        draw.line((width - 6, 3, width - 1, 7), fill=255)
        draw.line((width - 3, 9, width - 1, 7), fill=255)

    if (usb_storage):
        # draw USB icon
        draw.line((width - 14, 0, width - 14, 10), fill=255)
        draw.line((width - 14, 0, width - 13, 1), fill=255)
        draw.line((width - 14, 0, width - 15, 1), fill=255)
        draw.line((width - 13, 9, width - 13, 10), fill=255)
        draw.line((width - 17, 4, width - 17, 5), fill=255)
        draw.line((width - 16, 4, width - 16, 7), fill=255)
        draw.line((width - 15, 8, width - 15, 9), fill=255)
        draw.line((width - 13, 7, width - 13, 7), fill=255)
        draw.line((width - 12, 4, width - 12, 6), fill=255)
        draw.line((width - 11, 4, width - 11, 5), fill=255)

    w, h = draw.textsize(filename, font=font)
    draw.text((0, 16), filename, font=font, fill=255)

    if(filename==''):
        text = '- - -'
        w, h = draw.textsize(text, font=font)
        draw.text(((width / 2) - (w / 2), (height / 2) - (h / 2)), text, font=font, fill=255)

    disp.image(image)
    disp.display()
    if (lcdt>10):
        lcdt = 1
    else:
        lcdt = lcdt+1


# from oled.device import ssd1306, sh1106
# from oled.render import canvas
# from PIL import ImageFont, ImageDraw
# font = ImageFont.load_default()
# device = ssd1306(port=1, address=0x3C)

# with canvas(device) as draw:
#    font = ImageFont.truetype('font1.ttf', 20)
#    draw.text((10, 10), "Start",  font=font, fill=255)
#    draw.text((20, 20), 'CDC', font=font, fill=255)


# import kbd as hu
import vag as hu
import child

# Sd Card
MASS_STORAGE = 0x8
# Bluetooth
WIRELESS_CONTROLLER = 0xE0

DEV_SD_STAR = '/dev/sd*'
USB_PATH = '/media/usb'
CDC_PATH = USB_PATH  # + '/music'
CONFIG = 'cdc.ini'
# GPIO_Pin = 7
# PIN_ON_TIME = 30

# create logger
logging.config.fileConfig('logging.cfg')
logger = logging.getLogger('root')


# check devices for a class id
def find_dev(dev_class_id):
    device = usb.core.find()

    # is there a device at all
    if device is None:
        return False

    # check the device class
    if device.bDeviceClass == dev_class_id:
        return True

    # check configurations
    for cfg in device:
        # chack descriptors for interface class
        intf = usb.util.find_descriptor(cfg, bInterfaceClass=dev_class_id)
        if intf is not None:
            return True

    # found nothing
    return False


def mount():
    while True:
        sd = glob.glob(DEV_SD_STAR)
        if len(sd) > 1:
            logger.debug(sd)
            source = sd[0]
            if len(source) == 8:
                source = sd[1]
            break
        sleep(0.1)
    # logger.info(source)
    target = USB_PATH
    fs = 'vfat'
    options = '-t'

    ret = ctypes.CDLL('libc.so.6', use_errno=True).mount(source, target, fs, 0, options)
    if ret < 0:
        errno = ctypes.get_errno()
        # raise RuntimeError
        logger.error('Error mounting {} ({}) on {} with options \'{}\': {}'.
                     format(source, fs, target, options, os.strerror(errno)))
    return


# load the configuration file
# fix it
def read_config(albumNum, trackNum):
    with open(CONFIG, 'r') as file:
        cfgfile = file.read()
    config = ConfigParser.RawConfigParser(allow_no_value=True)
    config.readfp(io.BytesIO(cfgfile))

    # list all contents
    # logger.info('List all contents')
    # logger.info('Sections: {}'.format(config.sections()))
    # for section in config.sections():
    #	logger.info('Section: {}'.format(section))
    #	logger.info('Options: {}'.format(config.options(section)))
    #	for option in config.options(section):
    #		val = config.get(section, option)
    #		if val == -1:
    #			logger.warning('skip: {}'.format(option))
    #		logger.info('read config: {} {} {}'.format(section, option, val))

    try:
        albumNum = config.getint('cdc', 'album')
        trackNum = config.getint('cdc', 'track')
        logger.info('read config album: {}, track: {}'.format(albumNum, trackNum))
    except:
        logger.warning('can\'t read config file')
    return [albumNum, trackNum]


# store the configuration file
def write_config(albumNum, trackNum):
    # Add content to the file
    config = ConfigParser.ConfigParser()
    config.add_section('cdc')
    config.set('cdc', 'album', albumNum)
    config.set('cdc', 'track', trackNum)

    # Create the configuration file as it doesn't exist yet
    with open(CONFIG, 'w') as file:
        config.write(file)

    logger.info('write config album: {}, track: {}'.format(albumNum, trackNum))
    return


# execute a command
def cmd(command):
    logger.debug(command)
    res = os.popen(command).read()
    if res is not None:
        logger.debug(res)
    return res


def shuffle(album):
    shuffle = '\'' + CDC_PATH + '/' + album + '/shuffle\''
    if os.path.exists(shuffle):
        logger.info(shuffle)
        return True
    return False


# load new cd-dir
def play_cd(change, albumNum, trackNum, play):
    r = cmd('mpc ls')
    if r is not None:
        r = r.split('\n')
        logger.info('found {} albums'.format(len(r) - 1))
        if albumNum > len(r) - 2:  # there is an empty line at the end
            albumNum = 0
            trackNum = 1
        if albumNum < 0:
            albumNum = len(r) - 2  # there is an empty line at the end
            trackNum = 1
        album = r[albumNum]
        logger.info(album)
        write_config(albumNum, trackNum)
        cmd('mpc clear')
        if shuffle(album):
            cmd('mpc listall \'' + album + '\' | shuf | mpc add')
        else:
            cmd('mpc listall \'' + album + '\' | mpc add')
        #		cmd('mpc volume 100')
        if play:
            cmd('mpc play ' + str(trackNum))
            hu.set_status(albumNum, trackNum)
        else:
            cmd('mpc pause')
        logger.info('debug: album: {}, track: {}'.format(albumNum, trackNum))
    return [albumNum, trackNum]


# logging.basicConfig(filename='cdc.log',level=logging.INFO)
# logging.basicConfig(level=logging.INFO)
usb_storage = False
bluetooth = False
bluetooth_play = False
bluetooth_me = False
bluetooth_mp = False
bluetooth_mp1 = False
bluetooth_mpl = False

# bluetooth_mp = bm.getCurrentMediaPlayer()
albumNum = 0
trackNum = 1
play = False
hu.connect()
logger.info('start cdc')
# GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
# GPIO.setup(GPIO_Pin, GPIO.OUT) ## Setup GPIO Pin to OUT
# GPIO.output(GPIO_Pin, True) ## Turn on GPIO pin
# t = time.time()

# read hu commands from the vag and act like a cd changer
while True:
    try:
        #		if ((t + PIN_ON_TIME) <  time.time()):
        #			GPIO.output(GPIO_Pin, False) ## Turn on GPIO pin

        # get hu commands
        #update_lcd()
        cdc_cmd = hu.get_command()
        #cdc_cmd = None
        if (cdc_cmd != None):
            logger.info(cdc_cmd)
        # find a bluetooth player
        #bluetooth_mp = bm.getCurrentMediaPlayer()

        # find a bluetooth
        # if (not bluetooth): #and find_dev(WIRELESS_CONTROLLER):
        #	logger.info('found bluetooth')
        #	btSource = 'bluez_source.30_75_12_8A_D4_A0'
        #	btSink = 'alsa_output.platform-soc_sound.analog-stereo'
        #	#bt_command = 'pactl load-module module-loopback source={} sink={}'.format(btSource, btSink)
        #	bt_command = 'pactl load-module module-loopback'
        #	#child.main(['pi', '/home/pi', bt_command])
        #	bluetooth = True

        # find a usb storage
        if (not usb_storage) and find_dev(MASS_STORAGE):
            usb_storage = True
            logger.info('found Mass Storage')

            if not os.path.exists(CDC_PATH):
                mount()

            # cmd('mpd /home/pi/.mpd/mpd.conf') #restart mpd
            sleep(5)
            cmd('mpc update')
            #			r = cmd('mpc update music')
            #			logger.info(r)

            nums = read_config(albumNum, trackNum)
            albumNum = nums[0]
            trackNum = nums[1]
            logger.debug('read from config album: {}, track: {}'.format(albumNum, trackNum))
            nums = play_cd(None, albumNum, trackNum, play)
            albumNum = nums[0]
            trackNum = nums[1]

        if usb_storage and not find_dev(MASS_STORAGE):
            logger.warning('missing Mass Storage')
            cmd('mpc stop')
            usb_storage = False
        # cmd('mpc stop')

	if cdc_cmd == hu.HU_POWER_OFF:
	    power_off=1

	    disp.begin()
	    disp.clear()
	    disp.display()

	    subprocess.call(["shutdown", "-h", "now"], shell=False)

        if cdc_cmd == hu.HU_PLAY:
            play = True
        #			GPIO.output(GPIO_Pin, False) ## Turn on GPIO pin
        elif cdc_cmd == hu.HU_STOP:
            play = False

        #bm = BluetoothManager()
        #logger.info(bluetooth_mp)
        devices = bm.getDevices()
        connected = False
        for d in devices:
            if(d.Connected):
                connected = True
        if(connected):
            bluetooth_mp1 = bm.getCurrentMediaPlayer()
            try:
                bluetooth_status = bluetooth_mp.Status
                bluetooth_mp = bluetooth_mp1
            except:
                bluetooth_mp = False
            finally:
                bluetooth_mp = bluetooth_mp1

        update_lcd()


        if (connected and not bluetooth):
            bluetooth = True
            logger.info('found bluetooth')
        if (not connected and bluetooth):
            bluetooth = False
            bluetooth_mp = False
            logger.info('no bluetooth')
            devices = bm.getDevices()
            for d in devices:
                d.Disconnect()

        if(connected):
            if (bluetooth_mp and not bluetooth_mpl):
                bluetooth_mpl = True
                logger.info('found bluetooth player')
                logger.info(bluetooth_mp)
            if (not bluetooth_mp and bluetooth_mpl):
                bluetooth_mpl = False
                logger.info('no bluetooth player')

            try:
                if (bluetooth and bluetooth_mp != False and bluetooth_mp.Status == 'playing'):
                    bluetooth_play = True
                    play = True
                else:
                    bluetooth_play = False
                    play = False
                #logger.info(bluetooth_mp)
            except:
                #logger.error(bluetooth_mp)
                #bluetooth_mp = False
                bluetooth_play = False
                play = False


        if (usb_storage and bluetooth_play == False):
            # start play
            if cdc_cmd == hu.HU_PLAY:
                cmd('mpc play')
                trackNum = None  # in order to set status

            # stop play
            elif cdc_cmd == hu.HU_STOP:
                cmd('mpc pause')

            if play:
                # next
                if cdc_cmd == hu.HU_NEXT:
                    cmd('mpc next')

                # prev
                elif cdc_cmd == hu.HU_PREV:
                    mpd.previous()
                    #cmd('mpc prev')
                    #cmd('mpc prev')

                # next
                elif cdc_cmd == hu.HU_SEEK_FWD:
                    while (1):
                        cmd('mpc seek +00:00:10')
                        if hu.get_command() is not None:
                            break

                # prev
                elif cdc_cmd == hu.HU_SEEK_RWD:
                    while (1):
                        cmd('mpc seek -00:00:10')
                        if hu.get_command() is not None:
                            break

                elif cdc_cmd == hu.HU_CD1:
                    nums = play_cd(albumNum, 0, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_CD2:
                    nums = play_cd(albumNum, 1, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_CD3:
                    nums = play_cd(albumNum, 2, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_CD4:
                    nums = play_cd(albumNum, 3, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_CD5:
                    nums = play_cd(albumNum, 4, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_CD6:
                    nums = play_cd(albumNum, 5, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_NEXT_CD:
                    nums = play_cd(None, albumNum + 1, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_PREV_CD:
                    nums = play_cd(None, albumNum - 1, 1, play)
                    albumNum = nums[0]
                    trackNum = nums[1]

                elif cdc_cmd == hu.HU_SCAN:
                    cmd('mpc update')

                elif cdc_cmd == hu.HU_SHFFL:
                    cmd('mpc random on')

                elif cdc_cmd == hu.HU_SEQNT:
                    cmd('mpc random off')

                # check playing
                r = cmd('mpc |grep ] #')
		#logger.info(r)
		curSongInfo = mpd.currentsong()
		#logger.info(curSongInfo)
		if(curSongInfo.has_key('artist')):
		    filename = curSongInfo['artist'] + " - " + curSongInfo['title']
		else:
		    #logger.info(curSongInfo)
		    if(curSongInfo.has_key('file')):
			filename = curSongInfo['file']
		    else:
			filename = '...'
		#print "\n\n", curSongInfo['artist'] + " - " + curSongInfo['title'] + "\n"
                if (r is not None) and (len(r) > 0):
                    # r='[playing] #18/37   1:53/4:50 (38%)'
                    r = r.split('/')
                    # r='[playing] #18', '37   1:53', '4:50 (38%)
                    timer = None
                    if len(r) > 2:
                        timer = r[2].split(' ')[0]
                    r = r[0].split('#')
                    # r='[playing] ', '18'
                    if len(r) > 1:
                        tr = locale.atoi(r[1])
                        # hu.set_status(albumNum, trackNum, timer)
                        if tr != trackNum:
                            trackNum = tr
                            write_config(albumNum, trackNum)
                            hu.set_status(albumNum, trackNum, timer)
                else:
                    albumNum = albumNum + 1
                    trackNum = 1
                    nums = play_cd(None, albumNum, trackNum, play)
                    albumNum = nums[0]
                    trackNum = nums[1]
	    else:
		filename = ''
        # if play
        # if usb_storage
        if(connected):
            if (bluetooth and bluetooth_mp):
                # logger.info(cdc_cmd)
                if cdc_cmd == hu.HU_PLAY:
                    logger.info('play BT')
                    bluetooth_mp.Play()
                    trackNum = None  # in order to set status
                    logger.info('play')

                # stop play
                elif cdc_cmd == hu.HU_STOP:
                    bluetooth_mp.Pause()

                # print bluetooth_mp

                try:
                    if (bluetooth_mp != False and bluetooth_mp.Status == 'playing'):
                        bluetooth_play = True
                        play = True
                    else:
                        bluetooth_play = False
                        play = False
                except:
                    bluetooth_play = False
                    play = False



                if play:
                    try:
                        logger.info(bluetooth_mp.Track)
                    except:
                        logger.info('no data')

                    # next
                    if cdc_cmd == hu.HU_NEXT:
                        bluetooth_mp.Next()

                    # prev
                    elif cdc_cmd == hu.HU_PREV:
                        bluetooth_mp.Prev()

        # hu.set_status(0, 0, 0)

        #sleep(2)

    except (KeyboardInterrupt):
        hu.close()
        break

    except:
        usb_storage = False
        raise
