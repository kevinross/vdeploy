#!/bin/sh
. /lib/dracut-lib.sh

aufs=$(getargs overlayfs)
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
rm -rf /aufs/system/work
mkdir /aufs/system/work

# mount local
mount -t ext4 /dev/$LOC /aufs/local
rm -rf /aufs/local/work
mkdir /aufs/local/work

sbase="upperdir=/aufs/system/fs,lowerdir=/aufs/base,workdir=/aufs/system/work"
sroot="upperdir=/aufs/local/fs,lowerdir=/aufs/sysbase,workdir=/aufs/local/work" 

# mount sysbase
mount -t overlay overlay -o noatime,$sbase /aufs/sysbase

# mount local aufs on original sysroot
mount -t overlay overlay -o noatime,$sroot $NEWROOT

# give access to the original trees
mount --bind /aufs $NEWROOT/aufs
mount --bind /aufs/base $NEWROOT/aufs/base
mount --bind /aufs/system $NEWROOT/aufs/system
mount --bind /aufs/sysbase $NEWROOT/aufs/sysbase
mount --bind /aufs/local $NEWROOT/aufs/local
