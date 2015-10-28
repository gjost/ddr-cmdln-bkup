from datetime import datetime
import os

import storage


"""
NOTE: Some of the functions in DDR.storage are impossible to test reliably
because they report on removable drives which may or may not be present
in the test system.
"""


#def test_parse_removables():
#    """
#    NOTE: This test uses sample output of 'udisks --dump'.
#    """
#    out = storage._parse_removables(INPUT_REMOVABLES)
#    assert out == EXPECTED_REMOVABLES
#
#def test_parse_removables_mounted():
#    """
#    NOTE: This test uses sample output of 'df -h'.
#    PARTIAL: Does not actually test removable devices.
#    """
#    out = storage._parse_removables_mounted(INPUT_REMOVABLES_MOUNTED)
#    assert out == EXPECTED_REMOVABLES_MOUNTED

def test_device_actions():
    DEVICE_STATES = {
        'hdd': {
            '--': [],
            'm-': ['link'],
            'ml': ['unlink'],
            '-l': ['unlink'],
        },
        'unknown': {}
    }
    d0 = {'devicetype':'hdd', 'mounted':False, 'linked':False}
    d1 = {'devicetype':'hdd', 'mounted':True, 'linked':False}
    d2 = {'devicetype':'hdd', 'mounted':True, 'linked':True}
    d3 = {'devicetype':'hdd', 'mounted':False, 'linked':True}
    expected0 = []
    expected1 = ['link']
    expected2 = ['unlink']
    expected3 = ['unlink']
    assert storage.device_actions(d0, DEVICE_STATES) == expected0
    assert storage.device_actions(d1, DEVICE_STATES) == expected1
    assert storage.device_actions(d2, DEVICE_STATES) == expected2
    assert storage.device_actions(d3, DEVICE_STATES) == expected3

def test_parse_udisks_dump():
    assert storage._parse_udisks_dump(INPUT_REMOVABLES) == EXPECTED_REMOVABLES

# TODO local_devices
# TODO nfs_devices
# TODO find_store_dirs
# TODO local_stores
# TODO nfs_stores
# TODO devices
# TODO mounted_devices
# TODO mount
# TODO umount
# TODO remount
# TODO link
# TODO unlink

def test_make_drive_label():
    assert storage._make_drive_label('internal', '/media/ddrworkbench') == None
    assert storage._make_drive_label('removable', '/media/mylabel') == 'mylabel'

# TODO drive_label

def test_is_writable():
    assert storage.is_writable('/tmp') == True
    assert storage.is_writable('/etc') == False

def test_mount_path():
    """
    PARTIAL: only matches paths resolving to '/'
    NOTE: Test uses dirs as proxies for dirs on removable storage.
    """
    assert storage.mount_path(None) == '/'
    assert storage.mount_path('/') == '/'
    assert storage.mount_path('/tmp') == '/'
    assert storage.mount_path('/tmp/testing') == '/'

def test_guess_storage_type():
    """
    NOTE: Test uses dirs as proxies for dirs on removable storage.
    """
    assert storage._guess_storage_type('/') == 'internal'
    assert storage._guess_storage_type('/media/mydrive') == 'removable'
    assert storage._guess_storage_type('/some/other/path') == 'unknown'

# TODO storage_type

def test_status():
    """
    NOTE: Test uses dirs as proxies for dirs on removable storage.
    """
    exists_writable = '/tmp'
    exists_notwritable = '/etc'
    exists_notlistable = '/root'
    nonexistent = os.path.join('tmp', datetime.now().strftime('%Y%m%d%H%m%s'))
    assert storage.status(exists_writable) == 'ok'
    assert storage.status(exists_notwritable) == 'unknown'
    assert storage.status(exists_notlistable) == 'unmounted'
    assert storage.status(nonexistent) == 'unknown'

def test_disk_space():
    data = storage.disk_space('/')
    assert data.get('total')
    assert data.get('used')
    assert data.get('free')
    assert data.get('percent')

# sample udisks output
INPUT_REMOVABLES = """
========================================================================
Showing information for /org/freedesktop/UDisks/devices/sda1
  native-path:                 /sys/devices/pci0000:00/0000:00:0d.0/host
  device:                      8:1
  device-file:                 /dev/sda1
    presentation:              /dev/sda1
    by-id:                     /dev/disk/by-id/ata-VBOX_HARDDISK_VBfa7a1
    by-id:                     /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_V
    by-id:                     /dev/disk/by-uuid/dfee7d3a-4a38-418d-a22e
    by-path:                   /dev/disk/by-path/pci-0000:00:0d.0-scsi-0
  usage:                       filesystem
  type:                        ext2
  version:                     1.0
  uuid:                        dfee7d3a-4a38-418d-a22e-8bd1eb06c1ff
  label:                       

========================================================================
Showing information for /org/freedesktop/UDisks/devices/sdb
  native-path:                 /sys/devices/pci0000:00/0000:00:0d.0/host
  device:                      8:16
  device-file:                 /dev/sdb
    presentation:              /dev/sdb
    by-id:                     /dev/disk/by-id/ata-VBOX_HARDDISK_VB545f2
    by-id:                     /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_V
    by-path:                   /dev/disk/by-path/pci-0000:00:0d.0-scsi-1
  detected at:                 Tue 27 May 2014 10:33:21 AM PDT
  system internal:             1

========================================================================
Showing information for /org/freedesktop/UDisks/devices/sdb1
  native-path:                 /sys/devices/pci0000:00/0000:00:0d.0/host
  device:                      8:17
  device-file:                 /dev/sdb1
    presentation:              /dev/sdb1
    by-id:                     /dev/disk/by-id/ata-VBOX_HARDDISK_VB545f2
    by-id:                     /dev/disk/by-id/scsi-SATA_VBOX_HARDDISK_V
    by-id:                     /dev/disk/by-uuid/8fe7bd87-5896-402c-8606
    by-path:                   /dev/disk/by-path/pci-0000:00:0d.0-scsi-1
  system internal:             1
  removable:                   0
  is read only:                0
  is mounted:                  1
  mount paths:             /media/ddrworkstation
  usage:                       filesystem
  type:                        ext4
  version:                     1.0
  uuid:                        8fe7bd87-5896-402c-8606-bb367f0c3b25
  label:                       

========================================================================
Showing information for /org/freedesktop/UDisks/devices/sdc
  native-path:                 /sys/devices/pci0000:00/0000:00:0b.0/usb1
  device:                      8:32
  device-file:                 /dev/sdc
    presentation:              /dev/sdc
    by-id:                     /dev/disk/by-id/ata-WDC_WD5000BMVU-11A08S
    by-id:                     /dev/disk/by-id/scsi-SWD_5000BMV_ExternaW
    by-id:                     /dev/disk/by-id/wwn-0x50014ee2ad584d9d
    by-path:                   /dev/disk/by-path/pci-0000:00:0b.0-usb-0:
  system internal:             0
  removable:                   0
  is read only:                0
  is mounted:                  0
  mount paths:             
  usage:                       
  type:                        
  version:                     
  uuid:                        
  label:                       

========================================================================
Showing information for /org/freedesktop/UDisks/devices/sdc1
  native-path:                 /sys/devices/pci0000:00/0000:00:0b.0/usb1
  device:                      8:33
  device-file:                 /dev/sdc1
    presentation:              /dev/sdc1
    by-id:                     /dev/disk/by-id/ata-WDC_WD5000BMVU-11A08S
    by-id:                     /dev/disk/by-id/scsi-SWD_5000BMV_ExternaW
    by-id:                     /dev/disk/by-id/wwn-0x50014ee2ad584d9d-pa
    by-id:                     /dev/disk/by-uuid/408A51BE8A51B160
    by-path:                   /dev/disk/by-path/pci-0000:00:0b.0-usb-0:
  system internal:             0
  removable:                   0
  is read only:                0
  is mounted:                  1
  mount paths:             /media/WD5000BMV-2
  automount hint:              
  size:                        500096991232
  block size:                  512
  job underway:                no
  usage:                       filesystem
  type:                        ntfs
  version:                     
  uuid:                        408A51BE8A51B160
  label:                       WD5000BMV-2

========================================================================
Showing information for /org/freedesktop/UDisks/devices/sr0
  native-path:                 /sys/devices/pci0000:00/0000:00:01.1/host
  device:                      11:0
  device-file:                 /dev/sr0
    presentation:              /dev/sr0
    by-id:                     /dev/disk/by-id/ata-VBOX_CD-ROM_VB2-01700
    by-path:                   /dev/disk/by-path/pci-0000:00:01.1-scsi-1
  system internal:             0
  removable:                   1
  is read only:                0
  is mounted:                  0
  mount paths:             
  usage:                       
  type:                        
  version:                     
  uuid:                        
  label:                       

========================================================================
"""
EXPECTED_REMOVABLES = [
    {'mountpath': '/media/ddrworkstation', 'devicefile': '/dev/sdb1', 'mounting': 0, 'basepath': '/media/ddrworkstation/ddr', 'label': 'ddrworkstation', 'actions': [], 'fstype': 'ext4', 'devicetype': 'hdd', 'mounted': 1, 'linked': 0},
    {'mountpath': '/media/WD5000BMV-2', 'devicefile': '/dev/sdc1', 'mounting': 0, 'basepath': '/media/WD5000BMV-2/ddr', 'actions': [], 'label': 'WD5000BMV-2', 'devicetype': 'usb', 'fstype': 'ntfs', 'mounted': 1, 'linked': 0}
]

INPUT_REMOVABLES_MOUNTED = """
Filesystem                Size  Used Avail Use% Mounted on
rootfs                    7.3G  3.5G  3.5G  50% /
udev                       10M     0   10M   0% /dev
tmpfs                     406M  320K  406M   1% /run
/dev/mapper/partner-root  7.3G  3.5G  3.5G  50% /
tmpfs                     5.0M     0  5.0M   0% /run/lock
tmpfs                     811M     0  811M   0% /run/shm
/dev/sda1                 228M   19M  197M   9% /boot
"""
EXPECTED_REMOVABLES_MOUNTED = []
