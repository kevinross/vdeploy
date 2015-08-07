import sys, time, dbus, dbus.exceptions, sh, imp
sys.path.append('/root/vms')
bus = dbus.SystemBus()
def wait_for(vm,timeout=90):
	i = 0
	while i < timeout:
		print 'Trying to connect to xen-%s, %i-th time' % (vm, i)
		try:
			proxy = bus.get_object('name.kevinross.vm.vms.%s' % vm, '/name/kevinross/vm/vms/%s' % vm)
			iface = dbus.Interface(proxy, dbus_interface='name.kevinross.vm')
			print 'Connected'
			return iface
		except dbus.exceptions.DBusException, e:
			pass
		i += 1
		time.sleep(1)

vm = imp.load_source(sys.argv[1], '/root/vms/%s' % sys.argv[1])

this = wait_for(sys.argv[1], 90 if not hasattr(vm, 'systemd_timeout') else getattr(vm, 'systemd_timeout'))
if not this:
	sys.exit(1)
if len(sys.argv) > 2:
	sys.exit(0)
# if it's the first boot, it could take a while
# first boot defined by 'local' FS size > the newly formatted size of ~(483328+sizeof(vm-support))
def local_size():
	return int(sh.zfs('list',o='refer',H=True,p='xenfs/vms/%s/local' % sys.argv[1]))
vm_size = int(sh.du(s='/root/vm-support',block_size=1).split('\t')[0])
zero_size = 490000
zero_plus_vm = int(zero_size+vm_size*1.1) # 1.1 for FS overhead

while True:
	try:
		this.ping()
		time.sleep(5)
	except dbus.exceptions.DBusException, e:
		if local_size() < zero_plus_vm:
			this = wait_for(sys.argv[1])
			continue
		print 'VM exited'
		sys.exit(0)
sys.exit(1)
