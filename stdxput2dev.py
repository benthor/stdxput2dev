import sys
import struct
import fcntl
from subprocess import call

def error(*args):
    sys.stderr.write(" ".join([str(arg) for arg in args])+"\n")
    sys.stderr.flush()

def create_tunnel_interface(name):
    name = str(name)
    if not name.isalnum():
        error("name %s not a legal name for tunnel interface", %name)
        sys.exit(1)
    TUNSETIFF = 0x400454ca
    IFF_TUN = 0x0001
    IFF_TAP = 0x0002
    IFF_NO_PI = 0x1000

    # TODO: how does this work under *BSD?
    tun = open('/dev/net/tun', 'r+b')
    
    try:
        ifr = struct.pack('16sH', name, IFF_TUN | IFF_NO_PI)
        fcntl.ioctl(tun, TUNSETIFF, ifr)
    except IOError, e:
        error("""Could not create tunnel device '%s'.
                 Are you root?
                 Error message: %s """ % (name,e))
        sys.exit(2)

    return tun

def tunnel_between(ifacename, ip_local, ip_remote):
    """non-platform-independent way to configure point2point tunnel"""
    cmd = 'ifconfig %s promisc %s pointopoint %s up' % (ifacename, ip_local, ip_remote)
    retcode = call(cmd)
    if retcode:
        error('executing\n%s\nFAILED. Please run manually to find out why' % cmd)
        sys.exit(3)

def fpipe(fromfile, tofile, blocksize=0):
    if not blocksize: 
        from select import select
        for fd in [fromfile.fileno(), tofile.fileno()]:
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    while not fromfile.closed and not tofile.closed:
        if not blocksize:
            r = select([fromfile], [],[])[0][0]
            select([],[tofile],[])[1][0].write(r.read())
            tofile.flush()
        else:
            tofile.write(fromfile.read(blocksize))
            tofile.flush()

if __name__ == '__main__':
    from multiprocessing import Process
    if len(sys.argv) < 4:
        error("usage: python %s DEVICE LOCALIP REMOTEIP" % sys.argv[0])
        sys.exit(4)
    tun = create_tunnel_interface(sys.argv[1])
    tunnel_between(sys.argv[1], sys.argv[2], sys.argv[3])
    # copy stdin to the device:
    stdin2dev = Process(target=fpipe, args=(sys.stdin,tun))
    stdin2dev.start()
    # read dev to stdout
    stdout2dev = Process(target=fpipe, args=(tun,sys.stdout))
    stdout2dev.start()

    stdin2dev.join()
    stdout2dev.join()
