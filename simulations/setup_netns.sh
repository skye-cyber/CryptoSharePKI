#!/usr/bin/env bash

set -e  # Stop on error

# Define variables
BRIDGE="br0"
SUBNET="192.168.1"
GATEWAY="$SUBNET.1"
NUM_NS=5  # Change this to set the number of namespaces

# Enable IP forwarding on the host
sudo sysctl -w net.ipv4.ip_forward=1

# Create bridge if it doesn't exist
if ! ip link show "$BRIDGE" &>/dev/null; then
    echo "Creating bridge: $BRIDGE..."
    sudo ip link add name "$BRIDGE" type bridge
    sudo ip addr add "$GATEWAY/24" dev "$BRIDGE"
    sudo ip link set "$BRIDGE" up
else
    echo "Bridge $BRIDGE already exists, skipping creation."
fi

# Create namespaces and veth pairs
for i in $(seq 1 "$NUM_NS"); do
    NS="dev$i"
    VETH_HOST="veth$i"
    VETH_NS="brveth$i"
    NS_IP="$SUBNET.$((100 + i))"
    NS_LOOPBACK="127.0.$i.1"  # Unique loopback per namespace

    echo "Configuring namespace: $NS with IP $NS_IP and loopback $NS_LOOPBACK"

    # Create namespace if it doesn't exist
    if ! ip netns list | grep -q "$NS"; then
        sudo ip netns add "$NS"
    else
        echo "Namespace $NS already exists, skipping."
    fi

    # Create veth pair if it doesn't exist
    if ! ip link show "$VETH_HOST" &>/dev/null; then
        sudo ip link add "$VETH_HOST" type veth peer name "$VETH_NS"
    else
        echo "Interface $VETH_HOST already exists, skipping."
    fi

    # Move one end of veth to namespace
    sudo ip link set "$VETH_NS" netns "$NS"

    # Attach the host end to bridge
    sudo ip link set "$VETH_HOST" master "$BRIDGE"
    sudo ip link set "$VETH_HOST" up

    # Configure namespace network
    sudo ip netns exec "$NS" ip addr flush dev "$VETH_NS"  # Prevent conflicts
    sudo ip netns exec "$NS" ip addr add "$NS_IP/24" dev "$VETH_NS"
    sudo ip netns exec "$NS" ip link set "$VETH_NS" up
    sudo ip netns exec "$NS" ip route add default via "$GATEWAY"

    # Configure loopback IP for namespace
    sudo ip netns exec "$NS" ip addr add "$NS_LOOPBACK/8" dev lo
    sudo ip netns exec "$NS" ip link set lo up

    # Configure host side of veth
    sudo ip addr add "$NS_IP/24" dev "$VETH_HOST"
    sudo ip link set "$VETH_HOST" up

    echo "Namespace $NS configured with IP $NS_IP and loopback $NS_LOOPBACK."
done

# Setup NAT for external network access
EXT_IFACE=$(ip route | grep default | awk '{print $5}')
if ! sudo iptables -t nat -C POSTROUTING -s "$SUBNET.0/24" -o "$EXT_IFACE" -j MASQUERADE 2>/dev/null; then
    sudo iptables -t nat -A POSTROUTING -s "$SUBNET.0/24" -o "$EXT_IFACE" -j MASQUERADE
    echo "NAT enabled for network namespaces."
else
    echo "NAT rule already exists, skipping."
fi

echo "✅ Network setup complete. Run 'sudo ip netns list' to verify."
