# Setup
The following steps describe the setup needed to setup the zookeeper container.

## Installing dependencies:
Ensure you have docker on your system and then proceed to run the following commands to bring up the docker container.

```bash
docker build -t my-zookeeper .
docker run -d --name zookeeper-server -p 2181:2181 -p 2888:2888 -p 3888:3888 my-zookeeper

```
You should now see the docker dashboard running a new container with the zookeeper server running.

In order to run the app.py in the gameWebsite folder, you will have to update the IP address to your host machine IP address, run the following command to detect the host machine's IP address.

```bash
ifconfig | grep inet
```

You will see some entries like the following:

```bash
	inet 127.0.0.1 netmask 0xff000000
	inet6 ::1 prefixlen 128
	inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1
	inet6 fe80::e889:f3ff:feb9:19fd%ap1 prefixlen 64 scopeid 0xe
	inet6 fe80::10be:914f:e6f5:6c93%en0 prefixlen 64 secured scopeid 0xf
	inet 10.0.0.13 netmask 0xffffff00 broadcast 10.0.0.255
	inet6 2601:646:8b00:e8d0:43c:2d58:c82f:c8f prefixlen 64 autoconf secured
	inet6 2601:646:8b00:e8d0:910:9801:99be:9978 prefixlen 64 autoconf temporary
	inet6 2601:646:8b00:e8d0::ebcc prefixlen 64 dynamic
	inet6 fe80::b839:81ff:fee2:ef1f%awdl0 prefixlen 64 scopeid 0x10
	inet6 fe80::b839:81ff:fee2:ef1f%llw0 prefixlen 64 scopeid 0x11
	inet6 fe80::1355:d8df:4fd1:d34b%utun0 prefixlen 64 scopeid 0x12
	inet6 fe80::e232:c361:198b:8787%utun1 prefixlen 64 scopeid 0x13
	inet6 fe80::e125:c15c:1d93:41cd%utun2 prefixlen 64 scopeid 0x14
	inet6 fe80::ce81:b1c:bd2c:69e%utun3 prefixlen 64 scopeid 0x15
	inet6 fe80::34c8:17de:3a2b:77f2%utun4 prefixlen 64 scopeid 0x17
	inet6 fe80::73e4:2d5f:138d:57ef%utun5 prefixlen 64 scopeid 0x18
	inet6 fe80::9228:c119:2dc3:9c6%utun6 prefixlen 64 scopeid 0x19
	inet6 fe80::5956:e984:ef89:232b%utun7 prefixlen 64 scopeid 0x1a
	inet6 fe80::ca89:f3ff:feb9:19fd%ipsec0 prefixlen 64 scopeid 0x16
	inet6 2607:fb91:2cf0:8c7b:c5ac:bacb:9382:6daf prefixlen 64
	inet 192.168.64.1 netmask 0xffffff00 broadcast 192.168.64.255
```

Use the 10.0.0.13 as the IP address because the other two are localhost and gateway IP addresses.

## License

[MIT](https://choosealicense.com/licenses/mit/)