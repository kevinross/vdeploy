
name = 'vent'
kernel = "/boot/vmlinuz-xenvm"
ramdisk = "/boot/initramfs-xenvm.img"
extra = "root=LABEL=xenfs.base xenvm=vent aufs=local  ro tmem"
memory = 1024
maxmem = 2048
vcpus = 1
vif = [ 'mac=00:16:3E:9E:0C:3D,bridge=xenbr0' ]
disk = [ 'phy:/dev/zvol/xenfs/root/base,xvda,r', 'phy:/dev/xenfs/vms/vent/system,xvdb,w', 'phy:/dev/xenfs/vms/vent/local,xvdc,w', 'phy:/dev/disk/by-id/ata-WDC_WD20EARS-00MVWB0_WD-WCAZA7579371,xvdd,w', 'phy:/dev/disk/by-id/ata-SAMSUNG_HD204UI_S2HGJ1AZA04356,xvde,w', 'phy:/dev/disk/by-id/ata-TOSHIBA_DT01ABA100V_8398RTANS,xvdf,w', 'phy:/dev/disk/by-id/ata-TOSHIBA_DT01ABA100V_8325822PS,xvdg,w', 'phy:/dev/disk/by-id/ata-ST1000DM003-9YN162_S1D1PG8D,xvdh,w', 'phy:/dev/disk/by-id/ata-ST1000DM003-9YN162_S1D1QHGL,xvdi,w']
on_reboot = 'restart'
