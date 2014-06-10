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
    cmd = 'pmount --read-write --umask 022 {} {}'.format(device_file, label)
    r = envoy.run(cmd, timeout=60)
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
    r = envoy.run(cmd, timeout=60)
    in_removables = False
    for d in removables_mounted():
        if device_file in d['devicefile']:
            in_removables = True
    if not in_removables:
        unmounted = 'unmounted'
    return unmounted

def remount( device_file, label ):
    unmounted = umount(device_file)
    mount_path = mount(device_file, label)
    return mount_path

def _parse_removables( udisks_dump_stdout ):
    """Parse the output of 'udisks --dump'
    NOTE: Separated from .removables() for easier testing.
    """
    d = []
    sdchunks = []
    chunks = udisks_dump_stdout.split('========================================================================\n')
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

def removables():
    """List removable drives whether or not they are attached.
    
    This is basically a wrapper around "udisks --dump" that looks for
    "/dev/sdb*" devices and extracts certain info.
    Requires the udisks package (sudo apt-get install udisks).
    
    >> removables()
    [{'device-file': '/dev/sdb1', 'type': 'ntfs', 'uuid': '1A2B3C4D5E6F7G89', 'label': 'USBDRIVE1'}, {'device-file': '/dev/sdb2', 'type': 'ntfs', 'uuid':  '98G7F6E5D4C3B2A1', 'label': 'USBDRIVE2'}]
    
    @return: list of dicts containing attribs of devices
    """
    r = envoy.run('udisks --dump', timeout=2)
    return _parse_removables(r.std_out)

def _parse_removables_mounted( df_h_stdout ):
    d = []
    for l in df_h_stdout.split('\n'):
        if (l.find('/dev/sd') > -1) and (l.find('/media') > -1):
            attrs = {'devicefile':l.split()[0], 'mountpath':l.split()[-1],}
            if is_writable(attrs['mountpath']):
                d.append(attrs)
    return d

def removables_mounted():
    """List mounted and accessible removable drives.
    
    This is basically a wrapper around df:
    $ df -h
    ...
    /dev/sdc1               466G   76G  391G  17% /media/WD5000BMV-2
    
    @return: List of dicts containing attribs of devices
    """
    r = envoy.run('df -h', timeout=2)
    return _parse_removables_mounted(r.std_out)

def _make_drive_label( storagetype, mountpath ):
    """Make a drive label based on inputs.
    NOTE: Separated from .drive_label() for easier testing.
    """
    if storagetype == 'removable':
        label = mountpath.replace('/media/', '')
        if label:
            return label
    return None

def drive_label( path ):
    """Returns drive label for path, if path points to a removable device.
    
    @param path: Absolute path
    @return: String drive_label or None
    """
    realpath = os.path.realpath(path)
    storagetype = storage_type(realpath)
    mountpath = mount_path(realpath)
    return _make_drive_label(storagetype, mountpath)

def is_writable(path):
    """Indicates whether user has write permissions; does not check presence.
    
    @param path: Absolute path
    @return: True/False
    """
    return os.access(path, os.W_OK)

def mount_path( path ):
    """Given an absolute path, finds the mount path.
    
    >>> mount_path('/media/USBDRIVE1/tmp/ddr-testing-201303211200/files/')
    '/media/USBDRIVE1'
    >>> mount_path('/home/gjost/ddr-local/ddrlocal')
    '/'
    
    @param path: Absolute file path
    @return: Path to mount point or '/'
    """
    if not path:
        return '/'
    p1 = os.sep.join( path.split(os.sep)[:-1] )
    if os.path.ismount(p1):
        return p1
    if p1 == '':
        return os.sep
    return mount_path(p1)

def _guess_storage_type( mountpath ):
    """Guess storage type based on output of mount_path().
    NOTE: Separated from .storage_type() for easier testing.
    """
    if mountpath == '/':
        return 'internal'
    elif '/media' in mountpath:
        return 'removable'
    return 'unknown'
    
def storage_type( path ):
    """Indicates whether path points to internal drive, removable storage, etc.
    """
    # get mount pount for path
    # get label for mount at that path
    # 
    m = mount_path(path)
    return _guess_storage_type(m)

def storage_status( path ):
    """Indicates status of storage path.
    
    If the VM gets paused/saved
    """
    try: exists = os.path.exists(path)
    except: exists = False
    try: listable = os.listdir(path)
    except: listable = False
    writable = os.access(path, os.W_OK)
    # conditions
    if exists and listable and writable:
        return 'ok'
    elif exists and not listable:
        return 'unmounted'
    return 'unknown'

def disk_space( mountpath ):
    """Returns disk space info for the mounted drive.
    
    Uses 'df -h' on the back-end.
        Filesystem  Size  Used  Avail  Use%  Mounted on
    TODO Make this work on drives with spaces in their name!
    """
    fs = None
    if mount_path:
        r = envoy.run('df -h')
        for line in r.std_out.strip().split('\n'):
            while line.find('  ') > -1:
                line = line.replace('  ', ' ')
            parts = line.split(' ')
            path = parts[5]
            if (path in mountpath) and (path != '/'):
                fs = {'size': parts[1],
                      'used': parts[2],
                      'total': parts[3],
                      'percent': parts[4].replace('%',''),
                      'mount': parts[5],}
    return fs
