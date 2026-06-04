#!/usr/bin/env bash
# Runs automatically on live ISO boot — launches the AIDA installer.
clear
echo ""
echo "  Welcome to AIDA OS Alpha"
echo "  AI-Native Operating System"
echo ""
echo "  Starting installer in 3 seconds…"
echo "  (Press Ctrl+C to drop to a shell)"
echo ""
sleep 3
aida-install
