from pybtooth import BluetoothManager
bm = BluetoothManager()
#devices = bm.getDevices()
#for device in devices:
#    print device.get("Address")
mp = bm.getCurrentMediaPlayer()
print mp