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
OutFile "Setup.exe"

; Use compression
SetCompressor /SOLID LZMA

; Modern interface settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\AppleMusicDownloader.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Apple Music Downloader"
!define MUI_FINISHPAGE_RUN_NOTCHECKED

; Icons
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; Interface settings
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM" 
!define MUI_LANGDLL_REGISTRY_KEY "Software\${APPNAME}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

; License page
!define MUI_LICENSEPAGE_TEXT_TOP "Please read the following license agreement carefully"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "If you accept the terms of the agreement, click 'I Agree' to continue with the installation."
!define MUI_LICENSEPAGE_BUTTON "&Next >"

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
  
  ; Add only the executable from dist
  SetOverwrite ifnewer
  File "dist\AppleMusicDownloader.exe"
  
  ; Return to main directory
  SetOutPath "$INSTDIR"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write to registry
  WriteRegStr HKLM "Software\${APPNAME}" "Install_Dir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
  
  ; Create start menu shortcuts
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Apple Music Downloader.lnk" "$INSTDIR\AppleMusicDownloader.exe" "" "$INSTDIR\icon.ico" 0
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall Apple Music Downloader.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\icon.ico" 0
  
SectionEnd

; Desktop shortcut section (optional)
Section "Desktop Shortcut" SEC02
  CreateShortCut "$DESKTOP\Apple Music Downloader.lnk" "$INSTDIR\AppleMusicDownloader.exe" "" "$INSTDIR\icon.ico" 0
SectionEnd

; Section descriptions
LangString DESC_SEC01 ${LANG_ENGLISH} "Main application files"
LangString DESC_SEC01 ${LANG_SIMPCHINESE} "Main application files"
LangString DESC_SEC02 ${LANG_ENGLISH} "Create desktop shortcut"
LangString DESC_SEC02 ${LANG_SIMPCHINESE} "Create desktop shortcut"

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
  
  ; Remove directories
  RMDir "$INSTDIR"
  
  ; Remove start menu shortcuts
  Delete "$SMPROGRAMS\${APPNAME}\Apple Music Downloader.lnk"
  Delete "$SMPROGRAMS\${APPNAME}\Uninstall Apple Music Downloader.lnk"
  RMDir "$SMPROGRAMS\${APPNAME}"
  
  ; Remove desktop shortcut if it exists
  Delete "$DESKTOP\Apple Music Downloader.lnk"
  
SectionEnd

; Installer functions
Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd