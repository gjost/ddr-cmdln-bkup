import os

import envoy


def mount( device_file, label ):
    """Mounts specified device at the label; returns mount_path.
    
    TODO FIX THIS HORRIBLY UNSAFE COMMAND!!!
    
    @param device_file: Device file (ex: '/dev/sdb1')
    @param label: Human-readable name of the drive (ex: 'mydrive')
    @return: Mount path (ex: '/media/mydrive')
    """
    mount_path = None
    cmd = 'pmount -w {} {}'.format(device_file, label)
    r = envoy.run(cmd, timeout=2)
    for d in removables_mounted():
        if label in d['mountpath']:
            mount_path = d['mountpath']
    return mount_path

def umount( device_file ):
    """Unmounts device at device_file.
    
    TODO FIX THIS HORRIBLY UNSAFE COMMAND!!!
    
    @param device_file: Device file (ex: '/dev/sdb1')
    @return: True/False
    """
    unmounted = 'error'
    cmd = 'pumount {}'.format(device_file)
    r = envoy.run(cmd, timeout=2)
    in_removables = False
    for d in removables_mounted():
        if device_file in d['devicefile']:
            in_removables = True
    if not in_removables:
        unmounted = 'unmounted'
    return unmounted

def removables():
    """List removable drives whether or not they are attached.
    
    This is basically a wrapper around "udisks --dump" that looks for
    "/dev/sdb*" devices and extracts certain info.
    Requires the udisks package (sudo apt-get install udisks).
    
    >> removables()
    [{'device-file': '/dev/sdb1', 'type': 'ntfs', 'uuid': '1A2B3C4D5E6F7G89', 'label': 'USBDRIVE1'}, {'device-file': '/dev/sdb2', 'type': 'ntfs', 'uuid':  '98G7F6E5D4C3B2A1', 'label': 'USBDRIVE2'}]
    
    @return: list of dicts containing attribs of devices
    """
    d = []
    r = envoy.run('udisks --dump', timeout=2)
    sdchunks = []
    chunks = r.std_out.split('========================================================================\n')
    # get sdb* devices (sdb1, sdb2, etc)
    for c in chunks:
        if ('sdb' in c) or ('sdc' in c) or ('sdd' in c):
            lines = c.split('\n')
            numbrs = ['0','1','2','3','4','5','6','7','8','9',]
            if lines[0][-1] in numbrs:
                sdchunks.append(c)
    # grab the interesting data for each device
    # IMPORTANT: spaces are removed from these labels when they are assigned!!!
    interesting = ['devicefile', 'isreadonly', 'ismounted', 'mountpaths', 'type', 'uuid', 'label',]
    for c in sdchunks:
        attribs = {}
        for l in c.split('\n'):
            if ':' in l:
                k,v = l.split(':', 1)
                k = k.strip().replace('-','').replace(' ','')
                v = v.strip()
                if (k in interesting) and v and (not k in attribs.keys()):
                    attribs[k] = v
        d.append(attribs)
    return d

def removables_mounted():
    """List mounted and accessible removable drives.
    
    This is basically a wrapper around pmount, which allows mounting of
    removable devices by non-admin users.
    Requires the pmount package (sudo apt-get install pmount).
    
    $ pmount
    Printing mounted removable devices:
    /dev/sdb1 on /media/WD5000BMV-2 type fuseblk (rw,nosuid,nodev,relatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096)
    To get a short help, run pmount -h
    
    >> removables_mounted()
    [{'mountpath': '/media/USBDRIVE1', 'devicefile': '/dev/sdb1'}, {'mountpath': '/media/USBDRIVE2', 'devicefile': '/dev/sdb2'}]
    
    @return: List of dicts containing attribs of devices
    """
    d = []
    rdevices = removables()
    r = envoy.run('pmount', timeout=2)
    for l in r.std_out.split('\n'):
        if '/dev/' in l:
            parts = l.split(' ')
            attrs = {'devicefile':parts[0], 'mountpath':parts[2],}
            if is_writable(attrs['mountpath']):
                d.append(attrs)
    return d

def is_writable(path):
    """Indicates whether user has write permissions; does not check presence.
    
    @param path: Absolute path
    @return: True/False
    """
    return os.access(path, os.W_OK)

def mount_point( path ):
    """Given an absolute path, finds the mount point.
    
    >>> mount_point('/media/USBDRIVE1/tmp/ddr-testing-201303211200/files/')
    '/media/USBDRIVE1'
    >>> mount_point('/home/gjost/ddr-local/ddrlocal')
    '/'
    
    @param path: Absolute file path
    @return: Path to mount point or '/'
    """
    p1 = os.sep.join( path.split(os.sep)[:-1] )
    if os.path.ismount(p1):
        return p1
    if p1 == '':
        return os.sep
    return mount_point(p1)

def storage_type( path ):
    """Indicates whether path points to internal drive, removable storage, etc.
    """
    # get mount pount for path
    # get label for mount at that path
    # 
    m = mount_point(path)
    if m == '/':
        return 'internal'
    elif '/media' in m:
        return 'removable'
    return 'unknown'

def storage_status( path ):
    """
    """
    status = 'unknown'
    if path and os.path.exists(path) and is_writable(path):
        status = 'ok'
    return status
