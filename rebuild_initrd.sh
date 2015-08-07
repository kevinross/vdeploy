set -x
mv /lib/modules-load.d/zfs.conf /tmp
if [ -z "$KVER" ]; then
	KVER=3.16.1-302.aufs.fc21.x86_64
fi

dracut -N -o 'zfs' --omit-drivers 'zfs spl' --add-drivers 'tmem xen-blkfront xen-pcifront xen-privcmd netxen_nic xen-netfront' --kver $KVER  --include 'aufs-initramfs/usr/lib/dracut/hooks/pre-pivot/overlayfs.sh' '/usr/lib/dracut/hooks/pre-pivot/overlayfs.sh' --include 'aufs-initramfs/etc/modules-load.d/xen.conf' '/lib/modules-load.d/xen.conf' --force $1
mv /tmp/zfs.conf /lib/modules-load.d/

#mkdir xeninitrd
#pushd xeninitrd
#cpio -i </boot/initramfs-xenvm.img
#rsync -rah /root/aufs-initramfs/ ./
#find ./ | cpio -H newc -o >/boot/xenvm.img
#gzip /boot/xenvm.img
#mv /boot/xenvm.img.gz /boot/initramfs-xenvm.img
#popd
#rm -rf xeninitrd
