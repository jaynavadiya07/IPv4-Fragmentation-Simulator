# NetVista 3D — IPv4 Fragmentation Simulator

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ipv4-simulator.streamlit.app/)
[![Deployment Status](https://img.shields.io/badge/Deployment-Live%20Online-brightgreen?style=flat&logo=streamlit)](https://ipv4-simulator.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![RFC](https://img.shields.io/badge/RFC-791%20Compliant-orange)](https://datatracker.ietf.org/doc/html/rfc791)

> **Student ID:** 25CS052 | **Learner Group:** Advanced  
> **Course:** ITUC201 – Fundamentals of Computer Networks 2026-27  
> **Topic:** IPv4 fragmentation across unequal MTUs

---

## 🌐 Live Application

The simulator is deployed and live on Streamlit Community Cloud:  
👉 **[Open IPv4 Fragmentation Simulator Live App](https://ipv4-simulator.streamlit.app/)**

You can test and visualize IPv4 fragmentation, unequal MTU paths, and hole-descriptor reassembly directly in your browser with zero installation.

---

## Overview

An interactive browser-based IPv4 fragmentation simulator built with Python and Streamlit.  
Demonstrates how IPv4 packets are fragmented across network paths with varying MTUs,  
following RFC 791 rules (20-byte header, 8-byte offset alignment, MF/DF flags).

## Features

1. **Interactive Configuration** — Set payload size and MTU path via sidebar controls
2. **Animated Fragmentation** — Visual network topology showing hop-by-hop fragmentation
3. **Detailed Fragment Inspector** — Full breakdown of every fragment's fields
4. **Destination Reassembly Simulator** — RFC 791 hole-descriptor reassembly with simulated packet drops, interactive step playback, and ICMP Type 11 Code 1 timeout generation
5. **Experiment Dashboard** — Charts plotting fragment count and overhead vs MTU
6. **Validation Suite** — Automated checks for payload coverage, offsets, MF flags, and DF handling

## Quick Start

### Local Setup

```bash
# Clone the repository
git clone https://github.com/jaynavadiya07/IPv4-Fragmentation-Simulator.git
cd IPv4-Fragmentation-Simulator

# Install dependencies
pip3 install -r requirements.txt

# Run the simulator (browser)
streamlit run app.py

# Run terminal-mode validation
python3 fragmentation_engine.py
```

## Project Structure

```
IPv4-Fragmentation-Simulator/
├── app.py                    # Streamlit web application (main entry point)
├── fragmentation_engine.py   # Core IPv4 fragmentation simulation engine
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation & live links
├── .gitignore                # Clean Git ignore rules
└── .streamlit/
    └── config.toml           # Streamlit theme configuration (light mode)
```

## Technical Details

- **IPv4 Header:** 20 bytes (no options)
- **Fragment Offset:** Measured in 8-byte units
- **MF Flag:** Set to 1 on all fragments except the last
- **DF Flag:** When set, packet is dropped if MTU < packet size (ICMP Type 3 Code 4)
- **Minimum MTU:** 68 bytes (RFC 791)

## Dependencies

- Python 3.9+
- Streamlit ≥ 1.30.0
- Plotly ≥ 5.18.0
- Pandas ≥ 2.0.0
- NumPy ≥ 1.24.0
