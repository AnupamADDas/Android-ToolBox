param(
    [string]$SetupPath = "$PSScriptRoot\..\dist\installer\Android-Toolbox-Setup-1.2.0-x64.exe",
    [string]$ReviewRoot = "$env:LOCALAPPDATA\Temp\opencode\android-toolbox-installer-review"
)

$ErrorActionPreference = "Stop"
$registryKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\{D5A79D01-3F24-4D7E-9AE6-ABA95387B7C1}_is1"
if (Test-Path $registryKey) {
    throw "Android Toolbox is already installed. Run this review in a clean Windows account."
}
$installDir = Join-Path $ReviewRoot "Installed App"
if (Test-Path $installDir) {
    throw "Review installation directory already exists: $installDir"
}
New-Item -ItemType Directory -Force -Path $ReviewRoot | Out-Null
# The package deliberately hides the group-selection page and uses its default.
$group = "Android Toolbox"
$shortcutPath = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\$group\Android Toolbox.lnk"
if (Test-Path $shortcutPath) {
    throw "Review shortcut already exists: $shortcutPath"
}
$app = $null

try {
    $setupArgs = @(
        "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/NOCLOSEAPPLICATIONS",
        "/DIR=`"$installDir`"", "/TASKS=`"`"",
        "/LOG=`"$ReviewRoot\install.log`""
    )
    $setup = Start-Process -FilePath (Resolve-Path $SetupPath) -ArgumentList $setupArgs -Wait -PassThru
    if ($setup.ExitCode -ne 0) { throw "Setup failed: $($setup.ExitCode)" }
    $exe = Join-Path $installDir "Android_Toolbox.exe"
    foreach ($file in @(
        $exe,
        "$installDir\_internal\assets\icon.ico",
        "$installDir\_internal\assets\icons\ui-smartphone.png",
        "$installDir\_internal\bin\platform-tools\adb.exe",
        "$installDir\_internal\bin\platform-tools\fastboot.exe",
        "$installDir\unins000.exe",
        $shortcutPath
    )) {
        if (!(Test-Path $file)) { throw "Missing installed file: $file" }
    }
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcutPath)
    if ($shortcut.TargetPath -ne $exe) { throw "Start menu shortcut points to the wrong executable." }
    if (!$shortcut.IconLocation.StartsWith($exe)) { throw "Shortcut does not use the application icon." }
    $uninstall = Get-ItemProperty $registryKey
    if (!$uninstall.DisplayIcon.StartsWith($exe)) { throw "Uninstall icon is incorrect." }
    Write-Output "PASS: installation, bundled assets, Start menu shortcut, and uninstall icon"

    $app = Start-Process -FilePath $exe -WorkingDirectory $installDir -PassThru
    $ready = $false
    for ($attempt = 0; $attempt -lt 100; $attempt++) {
        $app.Refresh()
        if ($app.HasExited) { throw "Installed application exited during startup: $($app.ExitCode)" }
        if ($app.MainWindowTitle -like "Android Toolbox v*") {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 200
    }
    if (!$ready) { throw "Installed application did not open its main window." }
    # Wait for Tk's first complete idle render before capturing this window.
    [void]$app.WaitForInputIdle(10000)
    Start-Sleep -Milliseconds 1000
    $app.Refresh()
    python -c "from PIL import ImageGrab; ImageGrab.grab(window=int('$($app.MainWindowHandle)')).save(r'$ReviewRoot\installed-app.png')"
    if ($LASTEXITCODE -ne 0) { throw "Installed application screenshot failed." }
    Write-Output "PASS: installed application launched ($($app.MainWindowTitle))"
}
finally {
    if ($app -and !$app.HasExited) {
        [void]$app.CloseMainWindow()
        if (!$app.WaitForExit(10000)) { Stop-Process -Id $app.Id }
    }
    # Only stop any ADB server launched from this review installation.
    Get-Process adb -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -and $_.Path.StartsWith("$installDir\", [StringComparison]::OrdinalIgnoreCase)
    } | Stop-Process
    $uninstaller = Join-Path $installDir "unins000.exe"
    if (Test-Path $uninstaller) {
        $remove = Start-Process -FilePath $uninstaller -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=`"$ReviewRoot\uninstall.log`"" -Wait -PassThru
        if ($remove.ExitCode -ne 0) { throw "Uninstall failed: $($remove.ExitCode)" }
    }
}
if (Test-Path "$installDir\Android_Toolbox.exe") { throw "Uninstall left the application executable." }
if (Test-Path $shortcutPath) { throw "Uninstall left the Start menu shortcut." }
if (Test-Path $registryKey) { throw "Uninstall left its registry entry." }
Write-Output "PASS: uninstall removed the app, shortcut, and registration"
Write-Output "INSTALLER REVIEW: PASS"
