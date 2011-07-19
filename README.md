# stdxput2dev #

This is a pretty neat Python tool that creates a Linux tunnel device. Everything that is read from stdin is sent to the tunnel device, and everything that is read from the tunnel is written to stdout. This allows for an el-cheapo VPN-like tunnel over ssh or possibly plain netcat for instance. For this, the tool is invoked on both sides of the intended tunnel.

## Invocation ##

    usage: python stdxput2dev.py DEVICE LOCALIP REMOTEIP

DEVICE is the name you want to give to the tunnel device (tun0 is a reasonable example)
LOCALIP is the IP the DEVICE is to be configured with on the local side
REMOTEIP is the IP the DEVICE is to be configured with for the remote endpoint

It goes without saying that LOCALIP is the remote side's REMOTEIP and the other way around. See example usage below if this is unclear.

## IMPORTANT ##

If you decide to try this using netcat as a transport, be sure to *set the MTU of the created interface to 1024*. Like so:

    ifconfig DEVICE mtu 1024

## Example Usage: SSH-based VPN tunnel ##

Copy the script to the remote host:

    scp stdxput2dev.py root@remote.host:.

Create a named pipes
    
    mkfifo /tmp/fromremote
    mkfifo /tmp/toremote

As _root_:

    cat /tmp/fromremote | python stdxput2dev.py ssh0 10.0.0.1 10.0.0.2 > /tmp/toremote

Finally, (in a second shell) establish the tunnel on the remote side:

    cat /tmp/toremote | ssh root@remote.host "python stdxput2dev.py ssh0 10.0.0.2 10.0.0.1" > /tmp/fromremote 

Now test the tunnel by:

    ping 10.0.0.2

Or possibly:

    ssh 10.0.0.2

Obviously, you have to be root on the remote host. (Alternatively, you might do some magic with sudo.) Also, if you want to use the remote host for browsing the internet, you need to setup routing and masquerading, which is not within the scope of this README

I sometimes use the following contraction, which only uses a single shell window at a time:

    mkdir sshfifo; cat sshfifo | sudo python stdxput2dev.py ssh0 10.0.0.1 10.0.0.2 | ssh root@remote.host "python /tmp/stdxput2dev.py ssh0 10.0.0.2 10.0.0.1" > sshfifo

If none of the above work for you, make sure you are

 * root on both hosts
 * have a passwordless root login on the remote host

## Example Usage: CurveCP-based VPN tunnel ##

__Note that you *have* to set the MTU to 1024, because this is the maximum payload in bytes which fit inside a single CurveCP packet__

Here is how you might try to establish a CurveCP-based tunnel. Adapted from the CurveCP README:

    curvecpmakekey serverkey
    curvecpprintkey serverkey > serverkey.hex
    curvecpserver this.machine.name serverkey 127.0.0.1 10000 31415926535897932384626433832795 curvecpmessage sh -c "python stdxput2dev.py ccp0 10.0.0.2 10.0.0.1" 
    ifconfig ccp0 mtu 1024

In another terminal, do:

    curvecpclient this.machine.name `cat serverkey.hex` 127.0.0.1 10000 31415926535897932384626433832795 curvecpmessage -c sh -c "python stxput2dev.py ccp0 10.0.0.1 10.0.0.2 <&6 >&7"

Take care that the "serverkey.hex" is accessible from the second terminal.

Now test the tunnel by:

    ping 10.0.0.2        


## Known Bugs And Problems ##

_LOADS. I am serious, this is very immature software, by any reasonable standard_

  * My file-descriptor/tunnel magic doesn't work on FreeBSD. Fork me!
  * In the above example, if the process executing in a ptty is aborted, the client is sent into a busyloop and will only terminate if the server dies as well. Yes this is a bug, which I have yet failed to resolve. Fork me!
  * You need to be root on both local and the remote host to establish the tunnels.
  * The throughput speeds possible here are quite slow. On a host that achieves 10MB/s over plain HTTP, the same transfer over an ssh-based tunnel only about 1.4MB/s. (SSH-based file copy also achieves 10MB/s)
  * Proper error handling is missing in many cases, mostly due to my own ignorance about what needs to be checked. Fork me!
