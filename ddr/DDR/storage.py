import logging
logger = logging.getLogger(__name__)
import os

import envoy
import psutil

from DDR import MEDIA_BASE

DEVICE_TYPES = ['vhd', 'usb']

DEVICE_STATES = {
    'vhd': {
        '--': [],
        'm-': ['link'],
        'ml': ['unlink'],
        '-l': ['unlink'],
    },
    'usb': {
        '--': ['mount'],
        'm-': ['unmount','link'],
        'ml': ['unmount','unlink'],
        '-l': ['unlink'],
    },
    'unknown': {}
}


def device_actions(device):
    """Given device from devices(), return possible actions.
    
    @param device: dict
    @returns: list
    """
    devicetype = device['devicetype']
    state = []
    if device['mounted']: state.append('m')
    else:                 state.append('-')
    if device['linked']:  state.append('l')
    else:                 state.append('-')
    state = ''.join(state)
    return DEVICE_STATES[devicetype][state]

def list_nfs(df_T_stdout):
    """List mounted NFS volumes.
    
    @param df_T_stdout: str Output of "df -T".
    @returns: list of dicts containing device info.
    """
    cleaned = []
    lines = df_T_stdout.strip().split('\n')
    for line in lines:
        if 'nfs' in line:
            while '  ' in line:
                line = line.replace('  ', ' ')
            parts = line.split(' ')
            data = {
                'devicefile': parts[0],
                'mountpath': parts[-1],
                'mounted': os.path.exists(parts[-1]),
                'fstype': parts[1],
            }
            cleaned.append(data)
    return cleaned

def _parse_udisks(udisks_dump_stdout, symlink=None):
    """Parse the output of 'udisks --dump'
    NOTE: Separated from .devices() for easier testing.
    NOTE: This is probably unique to VirtualBox!
    
    @param udisks_dump_stdout: str Output of "udisks --dump".
    @param symlink: str Absolute path to MEDIA_BASE symlink.
    @returns: list of dicts containing device info.
    """
    chunks = udisks_dump_stdout.split('========================================================================\n')
    udisks_dump_stdout = None
    # get sdb* devices (sdb1, sdb2, etc)
    sdchunks = []
    NUMBRS = [c for c in '0123456789']
    for c in chunks:
        if ('sdb' in c) or ('sdc' in c) or ('sdd' in c):
            lines = c.split('\n')
            if lines[0][-1] in NUMBRS:
                sdchunks.append(c)
    chunks = c = None
    # grab the interesting data for each device
    # IMPORTANT: spaces are removed from these labels when they are assigned!!!
    devices = []
    INTERESTING = [
        'device-file', 'mount paths', 'label', 'is mounted', 'type',
        'native-path', 'by-id',
    ]
    for c in sdchunks:
        device = {
            'devicetype':'unknown',
            'mounted':False,
            'linked':False
        }
        for l in c.split('\n'):
            if ':' in l:
                k,v = l.split(':', 1)
                k = k.strip()
                v = v.strip()
                if (k in INTERESTING) and v and (not k in device.keys()):
                    device[k] = v
        devices.append(device)
    sdchunks = c = None
    # rm spaces and dashes
    RENAME_FIELDS = {
        'device-file': 'devicefile',
        'mount paths': 'mountpath',
        'is mounted': 'mounted',
        'type': 'fstype',
    }
    for device in devices:
        for keyfrom,keyto in RENAME_FIELDS.iteritems():
            if device.get(keyfrom,None):
                device[keyto] = device.pop(keyfrom)
    # I like ints
    INTEGERS = ['mounted', 'linked']
    for device in devices:
        for field in INTEGERS:
            if device.get(field, None):
                device[field] = int(device[field])
    # interpret device type
    for device in devices:
        # HDD
        if ('harddisk' in device['by-id'].lower()):
            device['devicetype'] = 'vhd'
            device['label'] = device['mountpath'].replace('/media/', '')
        # USB
        elif 'usb' in device['native-path'].lower():
            device['devicetype'] = 'usb'
        device.pop('by-id')
        device.pop('native-path')
    # collections directory
    for device in devices:
        if device.get('mountpath', None):
            device['basepath'] = os.path.join(device['mountpath'], 'ddr')
    # is device the target of symlink?
    if symlink:
        target = os.path.realpath(symlink)
        for device in devices:
            device['linked'] = 0
            if device.get('mountpath', None) and (device['mountpath'] in target):
                device['linked'] = 1
    # what actions are possible from this state?
    for device in devices:
        device['actions'] = device_actions(device)
    return devices

def devices(symlink=None):
    """List removable drives whether or not they are attached.
    
    This is basically a wrapper around "udisks --dump" that looks for
    "/dev/sd*" devices and extracts certain info.
    Requires the udisks package (sudo apt-get install udisks).
    TODO Switch to udiskie? https://github.com/coldfix/udiskie
    
    >> devices()
    [
        {'devicetype': 'usb', fstype': 'ntfs', 'devicefile': '/dev/sdb1', 'label': 'USBDRIVE1', mountpath:'...', 'mounted':1, 'linked':True},
        {'device_type': 'vhd', fs_type': 'ext3', 'devicefile': '/dev/sdb2', 'label': 'USBDRIVE2', mountpath:'...', 'mounted':0, 'linked':True}
    ]
    
    @return: list of dicts containing attribs of devices
    """
    r = envoy.run('udisks --dump', timeout=2)
    return _parse_udisks(r.std_out, symlink=symlink)

def mounted_devices():
    """List mounted and accessible removable drives.
    
    Note: this is different from base_path!
    
    @return: List of dicts containing attribs of devices
    """
    return [
        {'devicefile':p.device, 'mountpath':p.mountpoint,}
        for p in psutil.disk_partitions()
        if '/media' in p.mountpoint
    ]

def mount( device_file, label ):
    """Mounts specified device at the label; returns mount_path.
    
    TODO FIX THIS HORRIBLY UNSAFE COMMAND!!!
    
    @param device_file: Device file (ex: '/dev/sdb1')
    @param label: Human-readable name of the drive (ex: 'mydrive')
    @return: Mount path (ex: '/media/mydrive')
    """
    mount_path = None
    cmd = 'pmount --read-write --umask 022 {} {}'.format(device_file, label)
    logger.debug(cmd)
    r = envoy.run(cmd, timeout=60)
    for d in mounted_devices():
        if label in d['mountpath']:
            mount_path = d['mountpath']
    logger.debug('mount_path: %s' % mount_path)
    return mount_path

def umount( device_file ):
    """Unmounts device at device_file.
    
    TODO FIX THIS HORRIBLY UNSAFE COMMAND!!!
    
    @param device_file: Device file (ex: '/dev/sdb1')
    @return: True/False
    """
    unmounted = 'error'
    cmd = 'pumount {}'.format(device_file)
    logger.debug(cmd)
    r = envoy.run(cmd, timeout=60)
    mounted = False
    for d in mounted_devices():
        if device_file in d['devicefile']:
            mounted = True
    if not mounted:
        unmounted = 'unmounted'
    logger.debug(unmounted)
    return unmounted

def remount( device_file, label ):
    unmounted = umount(device_file)
    mount_path = mount(device_file, label)
    return mount_path

def link(target):
    """Create symlink to Store from MEDIA_BASE.
    
    @param target: absolute path to link target
    """
    link = MEDIA_BASE
    link_parent = os.path.split(link)[0]
    logger.debug('link: %s -> %s' % (link, target))
    if target and link and link_parent:
        s = []
        if os.path.exists(target):          s.append('1')
        else:                               s.append('0')
        if os.path.exists(link_parent):     s.append('1')
        else:                               s.append('0')
        if os.access(link_parent, os.W_OK): s.append('1')
        else:                               s.append('0')
        s = ''.join(s)
        logger.debug('s: %s' % s)
        if s == '111':
            logger.debug('symlink target=%s, link=%s' % (target, link))
            os.symlink(target, link)

def unlink():
    """Remove symlink to Store from MEDIA_BASE.
    """
    link = MEDIA_BASE
    s = []
    if os.path.exists(link):     s.append('1')
    else:                        s.append('0')
    if os.path.islink(link):     s.append('1')
    else:                        s.append('0')
    if os.access(link, os.W_OK): s.append('1')
    else:                        s.append('0')
    codes = ''.join(s)
    if codes in ['111', '010']:
        logger.debug('removing %s (-> %s): %s' % (link, os.path.realpath(link), codes))
        os.remove(link)
    else:
        logger.debug('could not remove %s (-> %s): %s' % (link, os.path.realpath(link), codes))

def _make_drive_label( storagetype, mountpath ):
    """Make a drive label based on inputs.
    NOTE: Separated from .drive_label() for easier testing.
    """
    if storagetype in ['mounted', 'removable']:
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

def device_type( path ):
    """Indicates whether path points to internal drive, removable storage, etc.
    
    Per Filesystem Hierarchy Standard v2.3, /media is the mount point for
    removeable media.
    
    @param path: str A file path
    @returns: str 'usb', 'vhd', or 'unknown'
    """
    mountpath = mount_path(path)
    for device in devices():
        if device.get('mountpath',None) == mountpath:
            return device['device_type']
    return 'unknown'

def status( path ):
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
    """Returns disk usage in bytes for the mounted drive.
    
    @param mountpath
    @returns: OrderedDict total, used, free, percent
    """
    return psutil.disk_usage(mountpath)._asdict()
