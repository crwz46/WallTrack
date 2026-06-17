import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import List


SHELL_COMPLETION = """
_walltrack_completion() {
    local cur prev words cword
    _init_completion || return

    case $prev in
        --chain|-c)
            COMPREPLY=($(compgen -W "ethereum bsc polygon arbitrum" -- "$cur"))
            return
            ;;
        --export)
            COMPREPLY=($(compgen -W "json csv" -- "$cur"))
            return
            ;;
        walltrack|main.py)
            COMPREPLY=($(compgen -W "--chain --export --html --interactive --help gas flash history" -- "$cur"))
            return
            ;;
    esac

    if [[ $cur == -* ]]; then
        COMPREPLY=($(compgen -W "--chain --export --html --interactive --help" -- "$cur"))
    fi
} &&
complete -F _walltrack_completion walltrack main.py
"""


POWERSHELL_COMPLETION = """
Register-ArgumentCompleter -Native -CommandName walltrack,main.py -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)
    $commands = @('--chain', '--export', '--html', '--interactive', '--help', 'gas', 'flash', 'history')
    $chains = @('ethereum', 'bsc', 'polygon', 'arbitrum')
    $formats = @('json', 'csv')

    if ($wordToComplete -like '--chain*') { return $chains }
    if ($wordToComplete -like '--export*') { return $formats }
    return $commands | Where-Object { $_ -like "$wordToComplete*" }
}
"""


def install_bash_completion():
    bashrc = Path.home() / ".bashrc"
    marker = "# walltrack completion"
    content = f"\n{marker}\n{SHELL_COMPLETION}\n"

    if bashrc.exists():
        existing = bashrc.read_text()
        if marker in existing:
            print("Bash completion already installed")
            return

    with open(bashrc, "a") as f:
        f.write(content)
    print("Bash completion installed! Run: source ~/.bashrc")


def install_zsh_completion():
    zshrc = Path.home() / ".zshrc"
    zsh_comp = SHELL_COMPLETION.replace(
        "complete -F _walltrack_completion",
        "compdef _walltrack_completion",
    )
    marker = "# walltrack completion"
    content = f"\n{marker}\n{zsh_comp}\n"

    if zshrc.exists():
        existing = zshrc.read_text()
        if marker in existing:
            print("Zsh completion already installed")
            return

    with open(zshrc, "a") as f:
        f.write(content)
    print("Zsh completion installed! Run: source ~/.zshrc")


def install_powershell_completion():
    docs = [
        Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        Path.home() / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
    ]

    profile = None
    for p in docs:
        if p.exists():
            profile = p
            break

    if not profile:
        profile = docs[0]
        profile.parent.mkdir(parents=True, exist_ok=True)

    marker = "# walltrack completion"
    content = f"\n{marker}\n{POWERSHELL_COMPLETION}\n"

    existing = profile.read_text() if profile.exists() else ""
    if marker in existing:
        print("PowerShell completion already installed")
        return

    with open(profile, "a") as f:
        f.write(content)
    print(f"PowerShell completion installed for {profile}")


def install(shell: str = None):
    if not shell:
        shell = os.path.basename(os.environ.get("SHELL", "powershell"))

    shell_map = {
        "bash": install_bash_completion,
        "zsh": install_zsh_completion,
        "powershell": install_powershell_completion,
        "pwsh": install_powershell_completion,
    }

    installer = shell_map.get(shell)
    if installer:
        installer()
    else:
        print(f"Unsupported shell: {shell}")
        print(f"Supported: {', '.join(shell_map.keys())}")
