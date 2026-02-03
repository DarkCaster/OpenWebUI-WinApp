REM add local uv.exe path to the end, will prefer system uv.exe if present
set "PATH=%PATH%;%script_dir%tools"

REM UV settings
set "UV_CONCURRENT_DOWNLOADS=4"
set "UV_CONCURRENT_INSTALLS=2"

REM launcher settings, persistent storage for webview cache
set "WEB_STORAGE=%base_dir%webview_cache"
set "SHUTDOWN_TIMEOUT=10"
set "MAX_CONSOLE_LINES=1000"
set "WINDOW_WIDTH=1200"
set "WINDOW_HEIGHT=960"
set "OPEN_EXTERNAL_LINKS_IN_BROWSER=True"
REM set "TEST_PAGE=https://www.whatismybrowser.com/detect/what-is-my-user-agent"

REM open-webui settings
REM NOTE: in order to allow use of microphone/webcam, you need to set OpenWebUI address to localhost, like 127.0.0.1.
set "HOST=127.0.0.10"
set "PORT=58080"
set "DATA_DIR=%base_dir%open_webui"
set "ENV=prod"
set "WEBUI_AUTH=False"
set "ENABLE_COMMUNITY_SHARING=False"
set "HF_HOME=%base_dir%huggingface"
set "HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1"
set "HF_HUB_DISABLE_TELEMETRY=1"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"


REM proxy server, UV will use it to download packages and python dist
REM set "ALL_PROXY=socks5://user:password@127.0.0.1:1080"

REM custom directory for pyc files
REM set "PYTHONPYCACHEPREFIX=%base_dir%cache"

REM set "HF_HUB_OFFLINE=1"
