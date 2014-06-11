from datetime import datetime
import os

import storage


"""
NOTE: Some of the functions in DDR.storage are impossible to test reliably
because they report on removable drives which may or may not be present
in the test system.
"""


# mount

# umount

# remount

def test_parse_removables():
    """
    NOTE: This test uses sample output of 'udisks --dump'.
    """
    out = storage._parse_removables(input_removables)
    assert out == expected_removables

def test_parse_removables_mounted():
    """
    NOTE: This test uses sample output of 'df -h'.
    PARTIAL: Does not actually test removable devices.
    """
    out = storage._parse_removables_mounted(input_removables_mounted)
    assert out == expected_removables_mounted

def test_make_drive_label():
    assert storage._make_drive_label('internal', '/media/ddrworkbench') == None
    assert storage._make_drive_label('removable', '/media/mylabel') == 'mylabel'

def test_is_writable():
    assert storage.is_writable('/tmp') == True
    assert storage.is_writable('/etc') == False

def test_mount_path():
    """
    PARTIAL: only matches paths resolving to '/'
    NOTE: Test uses dirs as proxies for dirs on removable storage.
    """
    assert storage.mount_path('/tmp') == '/'

def test_guess_storage_type():
    """
    NOTE: Test uses dirs as proxies for dirs on removable storage.
    """
    assert storage._guess_storage_type('/') == 'internal'
    assert storage._guess_storage_type('/media/mydrive') == 'removable'
    assert storage._guess_storage_type('/some/other/path') == 'unknown'

def test_storage_status():
    """
    NOTE: Test uses dirs as proxies for dirs on removable storage.
    """
    exists_writable = '/tmp'
    exists_notwritable = '/etc'
    exists_notlistable = '/root'
    nonexistent = os.path.join('tmp', datetime.now().strftime('%Y%m%d%H%m%s'))
    assert storage.storage_status(exists_writable) == 'ok'
    assert storage.storage_status(exists_notwritable) == 'unknown'
    assert storage.storage_status(exists_notlistable) == 'unmounted'
    assert storage.storage_status(nonexistent) == 'unknown'

DF_OUTPUT = """Filesystem                Size  Used Avail Use% Mounted on
rootfs                    7.3G  3.5G  3.5G  50% /
udev                       10M     0   10M   0% /dev
tmpfs                     406M  320K  406M   1% /run
/dev/mapper/partner-root  7.3G  3.5G  3.5G  50% /
tmpfs                     5.0M     0  5.0M   0% /run/lock
tmpfs                     811M     0  811M   0% /run/shm
/dev/sda1                 228M   19M  197M   9% /boot
/dev/sdb1                 126G  591M  120G   1% /media/ddrworkstation
none                      927G  603G  325G  66% /media/sf_ddrshared
/dev/sdc1                 466G  272G  195G  59% /media/WD5000BMV-2
"""
DF_PATH0 = '/'
DF_PATH1 = '/media/ddrworkstation'
DF_PATH2 = '/media/WD5000BMV-2'
DF_EXPECTED0 = None
DF_EXPECTED1 = {'total': '120G', 'mount': '/media/ddrworkstation', 'used': '591M', 'percent': '1', 'size': '126G'}
DF_EXPECTED2 = {'total': '195G', 'mount': '/media/WD5000BMV-2', 'used': '272G', 'percent': '59', 'size': '466G'}

# disk_space
def test_parse_df():
    assert storage._parse_diskspace(DF_OUTPUT, DF_PATH0) == DF_EXPECTED0
    assert storage._parse_diskspace(DF_OUTPUT, DF_PATH1) == DF_EXPECTED1
    assert storage._parse_diskspace(DF_OUTPUT, DF_PATH2) == DF_EXPECTED2

# sample udisks output
input_removables = """
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
expected_removables = [
    {
        'devicefile': '/dev/sdb1',
        'mountpaths': '/media/ddrworkstation',
        'uuid': '8fe7bd87-5896-402c-8606-bb367f0c3b25',
        'isreadonly': '0', 'ismounted': '1', 'type': 'ext4',
    },
    {
        'devicefile': '/dev/sdc1',
        'mountpaths': '/media/WD5000BMV-2',
        'label': 'WD5000BMV-2',
        'uuid': '408A51BE8A51B160',
        'isreadonly': '0', 'ismounted': '1',
        'type': 'ntfs',
    }
]


input_removables_mounted = """
Filesystem                Size  Used Avail Use% Mounted on
rootfs                    7.3G  3.5G  3.5G  50% /
udev                       10M     0   10M   0% /dev
tmpfs                     406M  320K  406M   1% /run
/dev/mapper/partner-root  7.3G  3.5G  3.5G  50% /
tmpfs                     5.0M     0  5.0M   0% /run/lock
tmpfs                     811M     0  811M   0% /run/shm
/dev/sda1                 228M   19M  197M   9% /boot
"""
expected_removables_mounted = []
