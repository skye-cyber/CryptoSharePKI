#!/usr/bin/bash

# Disable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=0

# Remove NAT rule (if it exists)
if sudo iptables -t nat -C POSTROUTING -s 192.168.1.0/24 -j MASQUERADE 2>/dev/null; then
    sudo iptables -t nat -D POSTROUTING -s 192.168.1.0/24 -j MASQUERADE
    echo "NAT rule removed."
else
    echo "NAT rule does not exist, skipping removal."
fi

# Loop to remove namespaces and interfaces
for i in {1..10}; do
    NS_NAME="dev$i"
    VETH_HOST="veth$i"
    VETH_NS="brveth$i"

    echo "Removing namespace: $NS_NAME"

    # Remove interfaces
    if ip link show $VETH_HOST &>/dev/null; then
        sudo ip link set $VETH_HOST down
        sudo ip link del $VETH_HOST
        echo "Removed interface: $VETH_HOST"
    else
        echo "Interface $VETH_HOST does not exist, skipping removal."
    fi

    if ip netns list | grep -q "$NS_NAME"; then
        sudo ip netns exec $NS_NAME ip link set $VETH_NS down
        sudo ip netns exec $NS_NAME ip link del $VETH_NS
        sudo ip netns del $NS_NAME
        echo "Removed namespace: $NS_NAME"
    else
        echo "Namespace $NS_NAME does not exist, skipping removal."
    fi
done

# Remove the bridge (if it exists)
if ip link show br0 &>/dev/null; then
    sudo ip link set br0 down
    sudo ip link del br0 type bridge
    echo "Removed bridge br0."
else
    echo "Bridge br0 does not exist, skipping removal."
fi

echo "Network cleanup complete."
