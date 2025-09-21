import re
from pathlib import Path
from ppg import path
from ppg.installer import _generate_installer_resources
from subprocess import check_call, DEVNULL
from ppg._state import SETTINGS

def create_installer_windows(user_level: bool = False):
    _generate_installer_resources()

    nsi_path = Path(path('target/installer/Installer.nsi'))
    app_name = SETTINGS['app_name']

    if not nsi_path.exists():
        raise FileNotFoundError(f"NSIS template not found: {nsi_path}")

    with open(nsi_path, encoding="utf-8") as f:
        text = f.read()

    if user_level:
        replacement = (
            "Function .onInit\n"
            "  ; User-level installation\n"
            f"  StrCpy $InstDir \"$LOCALAPPDATA\\\\{app_name}\"\n"
            "FunctionEnd"
        )
    else:
        # MultiUser Installation
        replacement = (
            "Function .onInit\n"
            "  !insertmacro MULTIUSER_INIT\n"
            "  ${If} $InstDir == \"\"\n"
            "      ${If} $MultiUser.InstallMode == \"AllUsers\"\n"
            f"          StrCpy $InstDir \"$PROGRAMFILES\\\\{app_name}\"\n"
            "      ${Else}\n"
            f"          StrCpy $InstDir \"$LOCALAPPDATA\\\\{app_name}\"\n"
            "      ${EndIf}\n"
            "  ${EndIf}\n"
            "FunctionEnd"
        )
    text = re.sub(
        r'Function \.onInit.*?FunctionEnd',
        replacement,
        text,
        flags=re.DOTALL
    )

    with open(nsi_path, "w", encoding="utf-8") as f:
        f.write(text)

    try:
        check_call(
            ['makensis', 'Installer.nsi'],
            cwd=path('target/installer'),
            stdout=DEVNULL
        )
    except FileNotFoundError:
        raise FileNotFoundError(
            "ppg could not find executable 'makensis'. Please install NSIS and "
            "add its installation directory to your PATH environment variable."
        ) from None
