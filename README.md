# Goal

Bring up a VM with a simple `systemctl start xen@$VMNAME`, including domain join and network home shares, without having to worry about anything other than the name.

# Usage

For a bare-bones VM, the above systemctl command will suffice. If customization is desired, read on!

## Files

Several files may be provided to customize the resulting VM; customization happens once and re-run is wholly manual and intentionally undocumented (the idea is that the files and scripts should be enough from a clean slate).

These files are documented in the order they are processed.

A 'list' of things is a list of things, one per line.

### packages

A list of packages to install. The lines are joined by spaces and passed to `yum install -y`.

Note: one can also pass a URL.

### `files.tar.gz`

Provide this file to drop arbitrary files into the filesystem. Think config files, persistent DB info, keys, etc.

### `rpms.tar.gz`

Provide this file to drop arbitrary RPMs into the system and install them.

### `installscript`

Actually almost identical to the next option but conceptually should be used for installing things

### `sh`

An arbitrary script to run; passed `init` or `reload` if the same kernel param is passed

### `service`

A list of services to get keytab entries for (cifs, httpd, etc) to be used to auth with kerberos

### `units`

A list of systemd units to enable

### `online`

A list of systemd units that must be running for `vm_online` to consider the VM online. For example, a LAMP VM would need mysql/mariadb and httpd here.

