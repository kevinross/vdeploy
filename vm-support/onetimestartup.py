def tr(n):
	print "ONE TIME STARTUP TRACE %r" % n
import procfs, sh, shutil, os, glob, sys, ping, time, traceback
from sh import systemctl, mount, tar, hostname, mount
from subprocess import call
from functools import partial

b = '/root/vm-support'
pj = os.path.join
vms = partial(pj, b)
bs = pj(vms(), 'bootstrap')
bsp = lambda x, y='': partial(pj, bs, vmname, x + y)

vmname = procfs.Proc().cmdline.split('xenvm=')[1].split(' ')[0].strip()
vmdevel = 'vmdevel' in str(procfs.Proc().cmdline)
vmreload = 'vmreload' in str(procfs.Proc().cmdline)
sysbase = sh.Command('systemd-nspawn').bake(D='/aufs/sysbase',M='sysbase-%s' % vmname, _out=sys.stdout)
yum = sysbase.yum

class Logger(object):
	def __init__(self):
		self.terminal = sys.stdout
		self.log = open("/tmp/onetime.log", "a")
	def write(self, message):
		self.terminal.write(message)
		self.log.write(message)
sys.stdout = Logger()
tr('starting')

# set hostname so things work right
hostname(vmname)

###########################################################################
################                                      #####################
################               SYSTEMD                #####################
################                                      #####################
###########################################################################

if not vmreload:
	tr('systemd')

	for i in glob.glob(vms('systemd/*')):
		tgt = '/etc/systemd/system/%s' % os.path.basename(i)
		if os.path.exists(tgt):
			os.unlink(tgt)
		shutil.copy(i, tgt)
		if 'target' not in i:
			systemctl.enable(os.path.basename(i))
	systemctl('daemon-reload')
	tr('systemd - done')

###########################################################################
################                                      #####################
################              VM SERVICE              #####################
################                                      #####################
###########################################################################

if not vmreload:
	tr('vm service')

	shutil.copy(vms('vm_service.py'), '/sbin/')
	shutil.copy(vms('ping.py'), '/lib64/python2.7/site-packages/')

	tr('vm service - done')

###########################################################################
################       	       	       	       	      #####################
################               ADS JOIN               #####################
################       	       	       	       	      #####################
###########################################################################

if not vmreload:
	tr('ads join')

	def pinger():
		try:
			return ping.do_one('pellet.cave.kevinross.name') > 0
		except:
			with open('/tmp/pings', 'a') as o:
				traceback.print_exc(file=o)
				o.write('\n')
			return False

	# try for 3 seconds
	i = 0
	while not pinger() and i < 6:
		time.sleep(0.5)
		i += 1
	if vmdevel:
		tr('ads join - skipping (devel mode)')
	else:
		sh.bash(vms('join_domain.sh'))

	tr('ads join - done')

###########################################################################
################       	       	       	       	      #####################
################                 PAM                  #####################
################       	       	       	       	      #####################
###########################################################################

if not vmreload:
	tr('pam')

	for i in glob.glob(vms('pam.d/*')):
		shutil.copy(i, '/etc/pam.d/')
	
	tr('pam - done')

###########################################################################
################                                      #####################
################               SERVICES               #####################
################                                      #####################
###########################################################################

if not vmreload:
	tr('services')
	if not vmdevel:
		systemctl.enable('kinit')
		if 'vent' not in vmname:
			systemctl.enable('nasfs')
		systemctl.enable('sssd')

		systemctl.start('sssd')
		systemctl.start('timer-daily.timer')
		systemctl.start('kinit')
	else:
		tr('services - skipping sssd,timer,kinit,nasfs (devel mode)')

	systemctl.start('vm-register')

	tr('services - done')

###########################################################################
################                                      #####################
################               SCRIPTS                #####################
################                                      #####################
###########################################################################

tr('packages')

# packages to install
k = bsp('packages')()
if os.path.exists(k):
	packs = ['-y'] + open(k).read().splitlines()
	yum.install(*packs)

tr('packages - done')

if not vmreload: # files will already be in local
	tr('files')
	# files to distribute
	k = bsp('files', '.tar.gz')()
	if os.path.exists(k):
		tar('-xzv',C='/',f=k)
	tr('files - done')

tr('rpms')
k = bsp('rpms', '.tar.gz')()
if os.path.exists(k):
	tar('-xzv',C='/aufs/sysbase',f=k)
	packs = [x.replace('/aufs/sysbase','') for x in glob.glob('/aufs/sysbase/tmp/rpms/*.rpm')]
	l = ['-y'] + packs
	yum.install(*l)
	shutil.rmtree('/aufs/sysbase/tmp/rpms')
tr('rpms - done')

tr('install sh')
k = bsp('installscript')()
if os.path.exists(k):
	shutil.copy(k, '/aufs/sysbase/tmp/installscript')
	sysbase.sh('/tmp/installscript')
	os.unlink('/aufs/sysbase/tmp/installscript')

tr('script')
# bash/python/... script
k=bsp('sh')()
if os.path.exists(k):
	os.system('bash %s %s' % (k, 'reload' if vmreload else 'init')) # pass the script info about whether reload or initial
tr('script - done')

if not vmdevel and not vmreload:
	tr('keytab')
	# keytabs to copy
	k = bsp('service')()
	if os.path.exists(k):
		with open(k) as f:
			for svc in f.read().splitlines():
				os.system('bash %s %s %s' % (vms('services'), vmname, svc))
	tr('keytab - done')

if not vmreload:
	tr('systemd units')
	# units to enable
	k = bsp('units')()
	if os.path.exists(k):
		with open(k) as f:
			for svc in f.read().splitlines():
				if os.path.exists('/lib/systemd/system/%s.service' % svc):
					systemctl.enable(svc)
				elif os.path.exists('/aufs/sysbase/usr/lib/systemd/system/%s.service' % svc) or os.path.exists('/aufs/system/lib/systemd/system/%s.service' % svc):
					os.symlink('/lib/systemd/system/%s.service' % svc, '/etc/systemd/system/multi-user.target.wants/%s.service' % svc)
				elif os.path.exists('/etc/systemd/system/%s.service' % svc) and not os.path.exists('/etc/systemd/system/multi-user.target.wants/%s.service' % svc):
					os.symlink('/etc/systemd/system/%s.service' % svc, '/etc/systemd/system/multi-user.target.wants/%s.service' % svc)
				else:
					tr('MUST ENABLE %s MANUALLY ON NEXT BOOT' % svc)

if not vmreload:
	# units that vm-register should depend on
	k = bsp('online')()
	if os.path.exists(k):
		try: os.mkdir('/etc/systemd/system/vm-register.service.d')
		except: pass
		with open(k) as f:
	               	for svc in f.read().splitlines():
				with open('/etc/systemd/system/vm-register.service.d/%s.conf' % svc, 'w') as o:
					o.write("""[Unit]
Requires=%s.service
After=%s.service
""" % (svc, svc))

	tr('systemd units - done')
	
###########################################################################
################                                      #####################
################               CLEANUP                #####################
################                                      #####################
###########################################################################

tr('cleanup')

shutil.rmtree(vms())
for i in ('base', 'system', 'local'):
	try:
		os.unlink('/aufs/%s/etc/systemd/system/onetime.service' % i)
		os.unlink('/aufs/%s/etc/systemd/system/multi-user.target.wants/onetime.service' % i)
	except:
		pass

tr('cleanup done')
