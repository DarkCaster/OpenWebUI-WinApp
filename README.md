TODO: Proper readme

## System Requirements

- Windows 11 with MS Edge WebView2 components installed (it should be already installed by-default, normally).
- PowerShell v5 and up for downloading ffmpeg binaries.

NOTE: Other Windows OSes (pre Windows 11) and engines was not tested, this app probably will not work on non-windows OS. You can also download runtime manually if missing from [this link](https://developer.microsoft.com/en-us/microsoft-edge/webview2)

## Installing and running

1. Clone this repo to local directory with GIT (or simply download ZIP file).
2. Run `init.bat` - it will download and install python with all needed packages by using UV (bundled, will prefer system-wide UV util if found). Also it will download ffmpeg binaries from github if missing. All python packages and downloads will be installed locally inside current workdir.
3. Run `run.bat` - it will launch application in a window + system tray icon.

NOTE: all python packages, persistent data and caches will be stored at workdir, so keep this in mind when creating a link to the `run.bat` file.
