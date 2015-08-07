#!/bin/bash

export KRB5CCNAME="FILE:/tmp/krb5cc_0"

kinit -k -t /root/vm-support/admin.keytab Administrator

net ads join -k

kdestroy
