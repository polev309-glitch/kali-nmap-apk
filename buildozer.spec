[app]
title = Kali Hunter
package.name = kalihunter
package.domain = org.kali

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.include_patterns = kivymd/**,assets/**

version = 1.0

requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

android.build_tools_version = 33.0.0

[buildozer]
log_level = 2
warn_on_root = 1
