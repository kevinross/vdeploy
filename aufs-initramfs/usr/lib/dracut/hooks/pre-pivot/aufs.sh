#!/bin/sh
. /lib/dracut-lib.sh

aufs=$(getargs aufs)
isiscsi=$(getargs netroot)

if [ -z "$aufs" ]; then
	return
fi

modprobe aufs

# unmount
umount $NEWROOT

# tree
mkdir /aufs
mkdir -p /aufs/{base,system,local,sysbase}

BASE="xvda"
SYS="xvdb"
LOC="xvdc"
if [ ! -z "$isiscsi" ]; then
	BASE="sda";
	SYS="sdb";
	LOC="sdc";
	if [ -b "/dev/sda" ]; then
		BASE="sdb";
		SYS="sdc";
		LOC="sdd";
	fi
fi

# mount base
mount -t ext4 -o ro /dev/$BASE /aufs/base
if [ ! -d /aufs/base/aufs ]; then
	mkdir -p /aufs/base/aufs
fi

# mount system
mount -t ext4 /dev/$SYS /aufs/system

# mount local
mount -t ext4 /dev/$LOC /aufs/local

src="/aufs/local=rw:/aufs/system=ro:/aufs/base=rr"

# mount local aufs on original sysroot
mount -t aufs -o noatime,noxino,dirs=$src aufs $NEWROOT

# mount base+system aufs for VM-specific maintenance
mount -t aufs -o noatime,noxino,dirs="/aufs/system=rw:/aufs/base=rr" aufs /aufs/sysbase

# give access to the original trees
mount --bind /aufs $NEWROOT/aufs
mount --bind /aufs/base $NEWROOT/aufs/base
mount --bind /aufs/system $NEWROOT/aufs/system
mount --bind /aufs/sysbase $NEWROOT/aufs/sysbase
mount --bind /aufs/local $NEWROOT/aufs/local
