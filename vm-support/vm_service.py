import sys
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
import gobject
import ping
import netifaces as ni
import time
try:
	from procfs import Proc
	proc = Proc()
	def parse():
		opts = {}
		for option in proc.cmdline.strip().split():
			fields = option.split("=")
			if len(fields) == 1:
				opts[fields[0]] = True
			else:
				opts[fields[0]] = fields[1]
		return opts
	vmname = parse().get('xenvm', 'default')
except:
	vmname = sys.argv[1]
DBusGMainLoop(set_as_default=True)

wheatley = None
while wheatley == None:
	try:
		print 'Trying to connect to wheatley...'
		wheatley = dbus.bus.BusConnection('tcp:host=wheatley,port=55556,family=ipv4')
	except:
		time.sleep(0.5)
		wheatley = None
print 'Connected, registering...'
class MyDBUSService(dbus.service.Object):
    def __init__(self):
        bus_name = dbus.service.BusName('name.kevinross.vm.vms.%s' % vmname, bus=wheatley)
        dbus.service.Object.__init__(self, bus_name, '/name/kevinross/vm/vms/%s' % vmname)

    @dbus.service.method('name.kevinross.vm')
    def ping(self):
	l = ni.ifaddresses('eth0')
	try:
	        return ping.do_one(l[2]['addr']) > 0
	except:
		try:
			return ping.do_one(l[2][0]['addr']) > 0
		except:
			return False

myservice = MyDBUSService()
ml = gobject.MainLoop()
print 'Registered. Starting MainLoop.'
ml.run()
