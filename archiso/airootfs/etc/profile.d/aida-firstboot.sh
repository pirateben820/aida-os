#!/bin/bash
if [ ! -f "$HOME/.aida/profile.yaml" ]; then
    /opt/aida-os/.venv/bin/aida-setup
    rm -f /etc/profile.d/aida-firstboot.sh
    echo ""
    echo "  Setup complete. Starting AIDA..."
    echo ""
    /opt/aida-os/.venv/bin/aida-chat
else
    echo ""
    echo "  AIDA OS is running.  Type 'aida-chat' to talk to AIDA."
    echo ""
fi
