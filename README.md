# firefox-extension-unity-launcher-api-e10s
Unity LauncherAPI add-on for Firefox, compatible with e10s.

### Requirements
  - python3
  - gdbus
  - web-ext (npm module, just for trying addon)

### Try Add-on

```sh
# get the code
$ git clone https://github.com/kotelnik/firefox-extension-unity-launcher-api-e10s
$ cd firefox-extension-unity-launcher-api-e10s

# install app-side of add-on (into your home folder)
# Note: change YOUR_USERNAME to your linux username
$ mkdir -p ~/.mozilla/native-messaging-hosts/
$ cp -r app-side/* ~/.mozilla/native-messaging-hosts/
$ sed -i "s_/usr/lib/mozilla/_/home/YOUR_USERNAME/.mozilla/_" ~/.mozilla/native-messaging-hosts/launcher_api_firefox_stdin.py.json

# build & run test version of firefox with add-on
$ cd addon-side
$ web-ext run
```

### Install
  - Arch Linux (AUR) package: https://aur.archlinux.org/packages/firefox-extension-unity-launcher-api-e10s
