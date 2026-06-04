# Auto-start the installer on live boot
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    bash /root/.automated_script.sh
fi
