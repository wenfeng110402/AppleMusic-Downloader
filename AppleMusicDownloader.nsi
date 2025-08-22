; Apple Music Downloader NSIS Installer Script
!define APPNAME "AppleMusicDownloader"
!define COMPANYNAME "wenfeng110402"
!define DESCRIPTION "A Python CLI app for downloading Apple Music songs, music videos and post videos."
!define VERSIONMAJOR 3
!define VERSIONMINOR 1
!define VERSIONBUILD 0
!define HELPURL "https://github.com/wenfeng110402/AppleMusic-Downloader"
!define UPDATEURL "https://github.com/wenfeng110402/AppleMusic-Downloader/releases"
!define ABOUTURL "https://github.com/wenfeng110402/AppleMusic-Downloader"

; Main Install settings
Name "${APPNAME}"
InstallDir "C:\AppleMusicDownloader"
InstallDirRegKey HKLM "Software\${APPNAME}" ""
OutFile "AppleMusicDownloader_Setup.exe"

; Use compression
SetCompressor /SOLID LZMA

; Modern interface settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\AppleMusicDownloader.exe"
!define MUI_FINISHPAGE_RUN_TEXT "立即启动 Apple Music Downloader"
!define MUI_FINISHPAGE_RUN_NOTCHECKED

; Icons
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; Interface settings
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM" 
!define MUI_LANGDLL_REGISTRY_KEY "Software\${APPNAME}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

; License page
!define MUI_LICENSEPAGE_TEXT_TOP "请仔细阅读以下许可协议"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "如果您接受协议条款，请单击“我接受”继续安装。"
!define MUI_LICENSEPAGE_BUTTON "&下一步 >"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;Languages
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"

; Installer section
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  
  ; Add files
  SetOverwrite ifnewer
  File "AppleMusicDownloader.exe"
  File "LICENSE"
  File "__main__.exe.manifest"
  File "icon.ico"
 
  
  ; Create tools directory and add tools
  SetOutPath "$INSTDIR\tools"
  File "tools\N_m3u8DL-RE.exe"
  File "tools\ffmpeg.exe"
  File "tools\mp4box.exe"
  File "tools\mp4decrypt.exe"
  
  ; Create gamdl directory and add Python files
  SetOutPath "$INSTDIR\gamdl"
  File "gamdl\__main__.py"
  
  ; Return to main directory
  SetOutPath "$INSTDIR"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write to registry
  WriteRegStr HKLM "Software\${APPNAME}" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\AppleMusicDownloader.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
  
  ; Create start menu shortcuts
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Apple Music Downloader.lnk" "$INSTDIR\AppleMusicDownloader.exe" "" "$INSTDIR\AppleMusicDownloader.exe" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Apple Music Downloader (UAC).lnk" "$INSTDIR\run_with_uac.bat" "" "$INSTDIR\run_with_uac.bat" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\卸载 Apple Music Downloader.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\README.lnk" "$INSTDIR\README.md" "" "" 0
  
SectionEnd

; Desktop shortcut section (optional)
Section "Desktop Shortcut" SEC02
  CreateShortCut "$DESKTOP\Apple Music Downloader.lnk" "$INSTDIR\AppleMusicDownloader.exe" "" "$INSTDIR\AppleMusicDownloader.exe" 0
SectionEnd

; Section descriptions
LangString DESC_SEC01 ${LANG_ENGLISH} "Main application files"
LangString DESC_SEC01 ${LANG_SIMPCHINESE} "主程序文件"
LangString DESC_SEC02 ${LANG_ENGLISH} "Create desktop shortcut"
LangString DESC_SEC02 ${LANG_SIMPCHINESE} "创建桌面快捷方式"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SEC01} $(DESC_SEC01)
!insertmacro MUI_DESCRIPTION_TEXT ${SEC02} $(DESC_SEC02)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller section
Section "Uninstall"
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
  DeleteRegKey HKLM "Software\${APPNAME}"
  
  ; Remove files and directories
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$INSTDIR\AppleMusicDownloader.exe"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\__main__.exe.manifest"
  Delete "$INSTDIR\icon.ico"
  Delete "$INSTDIR\run_with_uac.bat"
  Delete "$INSTDIR\gamdl\__main__.py"
  
  ; Remove tools
  Delete "$INSTDIR\tools\N_m3u8DL-RE.exe"
  Delete "$INSTDIR\tools\ffmpeg.exe"
  Delete "$INSTDIR\tools\mp4box.exe"
  Delete "$INSTDIR\tools\mp4decrypt.exe"
  
  ; Remove directories
  RMDir "$INSTDIR\tools"
  RMDir "$INSTDIR\gamdl"
  RMDir "$INSTDIR"
  
  ; Remove start menu shortcuts
  Delete "$SMPROGRAMS\${APPNAME}\Apple Music Downloader.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Apple Music Downloader (UAC).lnk"
  Delete "$SMPROGRAMS\${APPNAME}\卸载 Apple Music Downloader.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\README.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  
  ; Remove desktop shortcut if it exists
  Delete "$DESKTOP\Apple Music Downloader.lnk"
  
SectionEnd

; Installer functions
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd