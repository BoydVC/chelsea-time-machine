#!/usr/bin/env bash
# Screenshots of the running app (headless Chrome). Usage: ./screenshot.sh
cd "$(dirname "$0")"
PORT=${CHELSEA_TM_PORT:-4247}
shot() {  # name query [WxH]
  rm -rf /tmp/chelsea-tm-chrome
  google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=${3:-1440,900} --virtual-time-budget=4000 --user-data-dir=/tmp/chelsea-tm-chrome \
    --screenshot="screenshots/$1.png" "http://127.0.0.1:$PORT/?$2" 2>/dev/null
  echo "screenshots/$1.png"
}
shot 01-timeline "tab=timeline"
shot 02-league-chart "tab=chart&season=2004%E2%80%9305"
shot 03-this-day "tab=today"
shot 04-finals-legends "tab=finals"
shot 05-quiz "tab=quiz"
shot 06-sources "tab=sources"
shot 07-phone-this-day "tab=today" 390,844
shot 08-phone-chart "tab=chart&season=2011%E2%80%9312" 390,844
