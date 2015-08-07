#!/bin/bash

# $1 is the user with join privileges
# $2 is the domain server with samba 4
# $3 is the FQDN of the domain, uppercase
# $4 is the filename to export to; scripts use admin.keytab and $1==Administrator

samba-tool domain exportkeytab --principal=$1@$3 $4
samba-tool domain exportkeytab --princiapl=cifs/$2@$3 $4
