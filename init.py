from lxml import etree
import sys
sys.path.append('/root')
import os, sh, sys, tempfile, time, shutil, vm_macs, optparse
parser = optparse.OptionParser("usage: %prog [options] /path/to/save/to/VMNAME")
parser.add_option("-m", "--mac", dest="mac_address", help="specify a manual MAC address", metavar="MAC")
parser.add_option("-s", "--system-size", dest="system_size", default=8, type="int", help="specify the size of the system data volume (in GB) (will be a thin volume so size doesn't matter, hehe) [default: %default]", metavar="SYSSIZE")
parser.add_option("-l", "--local-size", dest="local_size", default=8192, type="int", help="specify the size of the local configuration data volume (in MB) (ditto on thin) [default: %default]", metavar="LOCSIZE")
parser.add_option("-b", "--base-memory", dest="base_memory", default=256, type="int", help="specify the initial amount of RAM (in MB) [default: %default]", metavar="BASEMEM")
parser.add_option("-u", "--max-memory", dest="max_memory", default=1024, type="int", help="specify the maximum amount of RAM to balloon to (in MB) [default: %default]", metavar="MAXMEM")
parser.add_option("--destroy-existing", dest="destroy", default=False, action="store_true", help="destroy existing volumes and replace configuration")
parser.add_option("--destroy-system", dest="destroy_sys", default=False, action="store_true", help="destroy only system volume")
parser.add_option("-d", "--development", dest="development", default=False, action="store_true", help="mark the VM to run in development mode; this stops the domain join from occuring (for now)")
options, args = parser.parse_args()
def mac_from(f):
	if 'xml' in f:
		e = etree.XML(open(f).read())
		return e.xpath('//mac')[0].attrib['address']
	exec(open(f).read())
	vals = dict([(x.split('=')[0], x.split('=')[1]) for x in vif[0].split(',')])
	return vals['mac']
def newest_mac():
	files = [x for x in os.listdir('/root/vms') if 'template' not in x and not x.endswith('c')]
	macs = [[int(x, 16) for x in mac_from('/root/vms/%s' % y).split(':')] for y in files]
	macs.sort(key=lambda x:x[-1])
	return macs[-1]
def next_mac(vmname):
	if vmname in vm_macs.macs:
		return vm_macs.macs[vmname]
	m = newest_mac()
	m[-1] += 1
	return ':'.join(["{0:0{1}x}".format(x,2).upper() for x in m])

def conf(vmname):
	root = os.path.join('/','dev','xenfs','vms', vmname)
	j = lambda x: os.path.join(root, x)
	vals = {'vmname': vmname,'mac': (options.mac_address or next_mac(vmname)),'base':j('base'),'syst':j('system'),'local':j('local')}
	vals.update(options.__dict__)
	vals['devel'] = 'vmdevel' if options.development else ''
	return """
name = '%(vmname)s'
kernel = "/boot/vmlinuz-xenvm"
ramdisk = "/boot/initramfs-xenvm.img"
extra = "root=LABEL=xenfs.base xenvm=%(vmname)s aufs=local %(devel)s ro tmem"
memory = %(base_memory)s
maxmem = %(max_memory)s
vcpus = 1
vif = [ 'mac=%(mac)s,bridge=xenbr0' ]
disk = [ 'phy:/dev/zvol/xenfs/root/base,xvda,r', 'phy:%(syst)s,xvdb,w', 'phy:%(local)s,xvdc,w' ]
on_reboot = 'restart'
""" % vals
vmname = os.path.basename(args[0])
if vmname == 'vent':
	sys.exit(0)
if options.destroy:
	print 'Destroying existing VM: %s' % args[0]
	try: os.unlink(args[0])
	except: pass
	print 'Destroying volumes: %s' % os.path.join('xenfs','vms',vmname)
	try: sh.zfs.destroy('-R', os.path.join('xenfs','vms',vmname))
	except: pass
if options.destroy_sys:
	print "Destroying %s's system volume" % args[0]
	try: sh.zfs.destroy(os.path.join('xenfs','vms',vmname,'system'))
	except: pass
	while os.path.exists(os.path.join('/','dev','zvol','xenfs','vms',vmname,'system')):
		time.sleep(0.1)
	d = tempfile.mkdtemp()
	sh.mount(os.path.join('/','dev','xenfs','vms',vmname,'local'),d)
	for i in ('rpm','yum','dnf'):
		shutil.rmtree(os.path.join(d, 'var','lib',i), ignore_errors=True)
		shutil.rmtree(os.path.join(d, 'var','cache',i), ignore_errors=True)
	sh.fstrim(d)
	sh.umount(d)
	shutil.rmtree(d)
if not os.path.exists(args[0]):
	print 'Creating configuration'
	s = conf(vmname)
	open(args[0], 'w').write(s)
try: sh.zfs.create('xenfs/vms')
except: pass
try: sh.zfs.create('xenfs/vms/%s' % vmname)
except: pass
syst = os.path.join('/','dev','xenfs','vms',vmname,'system')
local = syst.replace('system','local')
existed = [True, True]
if not os.path.exists(syst):
	print 'Creating volumes'
	if not os.path.exists(syst):
		sh.zfs.create('-s','-V','%dG' % options.system_size, 'xenfs/vms/%s/system' % vmname)
		existed[0] = False
	if not os.path.exists(local):
		sh.zfs.create('-s','-V','%dM' % options.local_size, 'xenfs/vms/%s/local' % vmname)
		existed[1] = False
	while not os.path.exists(syst) and not os.path.exists(local):
		print 'Sleeping for volume'
		time.sleep(0.01)
	if not existed[0]:
		print 'Formatting system...'
		sh.mkfs('-t', 'ext4', syst)
		sh.e2label(syst, 'xenfs.%s.sys' % vmname)
	if not existed[1]:
		print 'Formatting local...'
		sh.mkfs('-t', 'ext4', local)
		sh.e2label(local, 'xenfs.%s.loc' % vmname)
	def hostinfo(mnt):
		d = tempfile.mkdtemp()
		try:
			print 'Setting hostname in %s...' % mnt
			sh.mount(mnt, d)
			try:
				os.mkdir(os.path.join(d, 'etc'))
				os.mkdir(os.path.join(d, 'etc', 'samba'))
			except: pass
			with open(os.path.join(d, 'etc', 'hostname'), 'w') as f:
				f.write(vmname)
				f.write('\n')
			with open(os.path.join(d, 'etc', 'hostname.upper'), 'w') as f:
				f.write(vmname.upper())
			with open(os.path.join(d, 'etc', 'samba', 'name.conf'), 'w') as f:
				f.write("""[global]
	        netbios name = %(vmname)s
""" % dict(vmname=vmname.upper()))

			print 'Installing onetime service in %s...' % mnt
			b = os.path.join(d, 'etc', 'systemd', 'system')
			try:
				os.mkdir(os.path.join(d, 'etc', 'systemd'))
				os.mkdir(os.path.join(d, 'etc', 'systemd', 'system'))
				os.mkdir(os.path.join(d, 'etc', 'systemd', 'system', 'multi-user.target.wants'))
				shutil.copyfile('vm-support/onetime.service', os.path.join(b, 'onetime.service'))
				os.symlink('/etc/systemd/system/onetime.service', os.path.join(b, 'multi-user.target.wants/onetime.service'))
				os.mkdir(os.path.join(d, 'root'))
			except: pass
		except Exception, e:
			import traceback
			traceback.print_exc()
		else:
			sh.umount(d)
			os.rmdir(d)
	hostinfo(syst)
	hostinfo(local)
