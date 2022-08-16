#!/bin/bash

LXD_VERSION="4.0"
LXD_CLOUD=~/lxd-cloud.yaml
LXD_CREDENTIALS=~/lxd-credentials.yaml
LXD_PROD_CONF=~/lxd-production.conf
LXD_PROD_PRESEED=~/lxd-preseed.conf
DEFAULT_IF=`ip route list match 0.0.0.0 | awk '{print $5; exit}'`
DEFAULT_IP=`ip -o -4 a |grep ${DEFAULT_IF}|awk '{split($4,a,"/"); print a[1]; exit}'`
LXDENDPOINT=$DEFAULT_IP
CONTROLLER_NAME="osm-vca"

cat << EOF > $LXD_PROD_CONF
# Sysctl values for LXD in production
fs.inotify.max_queued_events=1048576
fs.inotify.max_user_instances=1048576
fs.inotify.max_user_watches=1048576
vm.max_map_count=262144
kernel.dmesg_restrict=1
net.ipv4.neigh.default.gc_thresh3=8192
net.ipv6.neigh.default.gc_thresh3=8192
net.core.bpf_jit_limit=3000000000
kernel.keys.maxkeys=2000
kernel.keys.maxbytes=2000000
EOF

cat << EOF > $LXD_PROD_PRESEED
config: {}
networks:
- config:
    ipv4.address: auto
    ipv6.address: none
  description: ""
  managed: false
  name: lxdbr0
  type: ""
storage_pools:
- config:
    size: 100GB
  description: ""
  name: default
  driver: btrfs
profiles:
- config: {}
  description: ""
  devices:
    eth0:
      name: eth0
      nictype: bridged
      parent: lxdbr0
      type: nic
    root:
      path: /
      pool: default
      type: disk
  name: default
cluster: null
EOF

# Apply sysctl production values for optimal performance
sudo cp $LXD_PROD_CONF /etc/sysctl.d/60-lxd-production.conf
sudo sysctl --system
# Install LXD snap
sudo apt-get remove --purge -y liblxc1 lxc-common lxcfs lxd lxd-client
sudo snap install lxd --channel $LXD_VERSION/stable
# Configure LXD
sudo usermod -a -G lxd `whoami`
cat $LXD_PROD_PRESEED | sed 's/^config: {}/config:\n  core.https_address: '$LXDENDPOINT':8443/' | sg lxd -c "lxd init --preseed"
sg lxd -c "lxd waitready"
DEFAULT_MTU=$(ip addr show $DEFAULT_IF | perl -ne 'if (/mtu\s(\d+)/) {print $1;}')
sg lxd -c "lxc profile device set default eth0 mtu $DEFAULT_MTU"
sg lxd -c "lxc network set lxdbr0 bridge.mtu $DEFAULT_MTU"

cat << EOF > $LXD_CLOUD
clouds:
  lxd-cloud:
    type: lxd
    auth-types: [certificate]
    endpoint: "https://$LXDENDPOINT:8443"
    config:
      ssl-hostname-verification: false
EOF
openssl req -nodes -new -x509 -keyout ~/client.key -out ~/client.crt -days 365 -subj "/C=FR/ST=Nice/L=Nice/O=ETSI/OU=OSM/CN=osm.etsi.org"
server_cert=$(awk '{print "        "$0}' /var/snap/lxd/common/lxd/server.crt)
client_cert=$(awk '{print "        "$0}' ~/client.crt)
client_key=$(awk '{print "        "$0}' ~/client.key)

cat << EOF > $LXD_CREDENTIALS
credentials:
  lxd-cloud:
    lxd-cloud:
      auth-type: certificate
      server-cert: |
$server_cert
      client-cert: |
$client_cert
      client-key: |
$client_key
EOF

lxc config trust add local: ~/client.crt
juju add-cloud -c $CONTROLLER_NAME lxd-cloud $LXD_CLOUD --force
juju add-credential -c $CONTROLLER_NAME lxd-cloud -f $LXD_CREDENTIALS
sg lxd -c "lxd waitready"
juju controller-config features=[k8s-operators]
