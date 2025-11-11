# Order Status Display

External customer-facing display for the fast food cashier system. Shows completed order numbers so customers know when their order is ready.

## Overview

This lightweight application runs on a Raspberry Pi connected to an external monitor, displaying order numbers received from the main cashier station.

## Features

- **Order Number Display** - Shows completed orders in real-time
- **Dual Connectivity** - Receives data via Tailscale (WiFi) or Bluetooth
- **Automatic Failover** - Switches connection method automatically

## Hardware

- Raspberry Pi (any model with HDMI output)
- External monitor/TV

## Technical Stack

- **Language**: Python
- **GUI Framework**: Qt5 (PyQt5)
- **Networking**: Tailscale, Bluetooth

## Usage

The display automatically connects to the main cashier station and updates when orders are completed. No manual interaction required.

## Integration

This application is designed to work with the [Fast Food Cashier System](https://github.com/MagnusVdr/Kitchen_Manager/tree/main). It receives order completion notifications and displays them for customers.
