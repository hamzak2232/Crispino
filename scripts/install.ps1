param(
  [Parameter(Mandatory=$true)]
  [string]$ExePath
)

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "Crispino POS.lnk"

Write-Host "Creating desktop shortcut to $ExePath ..."
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($ShortcutPath)
$sc.TargetPath = $ExePath
$sc.WorkingDirectory = Split-Path $ExePath
$sc.IconLocation = $ExePath
$sc.Description = "Crispino POS"
$sc.Save()
Write-Host "Shortcut created: $ShortcutPath"