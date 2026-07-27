param(
    [string]$Mode = "full",
    [string]$Match = "",
    [string]$AnnotatedDir = ""
)

$ErrorActionPreference = "Stop"
$dll = if ($env:TIA_OPENNESS_DLL) { $env:TIA_OPENNESS_DLL }
       elseif (Test-Path "$env:USERPROFILE\TIA_Openness\Siemens.Engineering.dll") { "$env:USERPROFILE\TIA_Openness\Siemens.Engineering.dll" }
       else { throw "TIA Openness DLL not found. Set TIA_OPENNESS_DLL env var or place at %USERPROFILE%\TIA_Openness\Siemens.Engineering.dll" }
[System.Reflection.Assembly]::LoadFrom($dll) | Out-Null

$baseDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path $MyInvocation.MyCommand.Path -Parent }
$exportDir = Join-Path $baseDir "scl_export"
$notedDir  = Join-Path $baseDir "scl_export_note"
$groupFile = Join-Path $baseDir "_block_groups.json"

function GetSvc {
    param($I, [Type]$T)
    $m = $I.GetType().GetMethods() | Where-Object { $_.Name -eq "GetService" -and $_.IsGenericMethodDefinition -and $_.GetParameters().Count -eq 0 } | Select-Object -First 1
    if (-not $m) { return $null }
    try { return $m.MakeGenericMethod($T).Invoke($I, $null) } catch { return $null }
}

function SearchPLC {
    param($Items, [Type]$CT)
    foreach ($item in $Items) {
        $svc = GetSvc $item $CT
        if ($svc -and $svc.Software -is [Siemens.Engineering.SW.PlcSoftware]) { return $svc.Software }
        $n = SearchPLC $item.DeviceItems $CT
        if ($n) { return $n }
    }
    return $null
}

function FindBlock {
    param($Group, $Name)
    $b = $Group.Blocks.Find($Name)
    if ($b) { return $b }
    foreach ($sub in $Group.Groups) {
        $b = FindBlock $sub $Name
        if ($b) { return $b }
    }
    return $null
}

function Get-BlockProp { param($B, $N) try {return $B.GetType().GetProperty($N).GetValue($B,$null)} catch {return $null} }

function ListBlocksWithGroups {
    param($Group, [string]$Path)
    $r = @()
    foreach ($b in $Group.Blocks) {
        $num = Get-BlockProp $b 'Number'
        $r += [PSCustomObject]@{
            Block = $b; Name = $b.Name; Type = $b.GetType().Name
            Lang = "$(Get-BlockProp $b 'ProgrammingLanguage')"
            GroupPath = $Path; Number = if ($num) { [int]$num } else { 0 }
        }
    }
    foreach ($sub in $Group.Groups) {
        $subPath = if ($Path) { "$Path/$($sub.Name)" } else { $sub.Name }
        $r += ListBlocksWithGroups $sub $subPath
    }
    return $r
}

function EnsureGroup {
    param($Group, [string]$Path)
    if (-not $Path) { return $null }
    $parts = $Path -split '/'
    $current = $Group
    foreach ($part in $parts) {
        if (-not $part) { continue }
        $found = $current.Groups.Find($part)
        if ($found) { $current = $found }
        else { try { $current = $current.Groups.Create($part) } catch { return $null } }
    }
    return $current
}

# ===== Attach =====
Write-Host "Attaching..."
$tp = $null
foreach ($p in [Siemens.Engineering.TiaPortal]::GetProcesses()) {
    if ($p.Mode -ne [Siemens.Engineering.TiaPortalMode]::WithUserInterface) { continue }
    $wp = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
    if ($wp.MainWindowTitle -match $Match) { $tp = $p; break }
}
if (-not $tp) { throw "TIA not found" }
$tia = $tp.Attach()
Write-Host "Connected"

try {
    $proj = $tia.Projects[0]
    Write-Host "Project: $($proj.Name)"
    $ct = [Siemens.Engineering.HW.Features.SoftwareContainer]

    # Find ALL PLCs
    $allPlcs = @()
    foreach ($device in $proj.Devices) {
        $plc = SearchPLC $device.DeviceItems $ct
        if ($plc) { $allPlcs += $plc }
    }
    if ($allPlcs.Count -eq 0) { throw "No PLC found" }
    Write-Host "Found $($allPlcs.Count) PLC(s):"
    foreach ($plc in $allPlcs) { Write-Host "  - $($plc.Name)" }

    # ===== EXPORT =====
    if ($Mode -eq "export" -or $Mode -eq "full") {
        Write-Host "`n=== EXPORT ==="
        if (Test-Path $exportDir) { Remove-Item $exportDir -Recurse -Force }
        New-Item -ItemType Directory -Path $exportDir -Force | Out-Null

        $allBlockInfo = @{}
        $totalOk = 0; $totalFail = 0
        $gs = [Siemens.Engineering.SW.ExternalSources.IGenerateSource]

        foreach ($plc in $allPlcs) {
            $plcName = $plc.Name
            $plcDir = Join-Path $exportDir (($plcName -replace '[\\/:*?"<>|]', '_'))
            New-Item -ItemType Directory -Path $plcDir -Force | Out-Null

            $all = @(ListBlocksWithGroups $plc.BlockGroup "")
            $scl = $all | Where-Object { $_.Lang -match "SCL" -and $_.Type -in @("FC","FB","OB") }
            Write-Host "$plcName : $($all.Count) total, $($scl.Count) SCL"

            foreach ($item in $scl) {
                $key = "$plcName`n$($item.Name)"
                $allBlockInfo[$key] = @{ Plc = $plcName; Group = $item.GroupPath; Number = $item.Number }
            }

            $esg = $plc.ExternalSourceGroup
            $ok = 0; $fail = 0
            foreach ($item in $scl) {
                if (-not ($item.Block -is $gs)) { $fail++; continue }
                try {
                    $f = Join-Path $plcDir "$($item.Name).scl"
                    $lst = New-Object "System.Collections.Generic.List[Siemens.Engineering.SW.ExternalSources.IGenerateSource]"
                    $lst.Add([Siemens.Engineering.SW.ExternalSources.IGenerateSource]$item.Block)
                    $esg.GenerateSource($lst, [System.IO.FileInfo]::new($f))
                    $ok++
                } catch { $fail++ }
            }
            $totalOk += $ok; $totalFail += $fail
        }
        $allBlockInfo | ConvertTo-Json -Depth 3 | Set-Content $groupFile -Encoding UTF8
        Write-Host "Exported: $totalOk ok, $totalFail fail"
    }

    # ===== COMMENT =====
    if ($Mode -eq "full") {
        Write-Host "`n=== COMMENT ==="
        $pyScript = Join-Path $baseDir "scl_commenter.py"
        if (Test-Path $notedDir) { Remove-Item $notedDir -Recurse -Force }
        $pyResult = & python $pyScript $exportDir $notedDir 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Host "Python error: $pyResult" }
        else { Write-Host "Comments added: $notedDir" }
    }

    # ===== IMPORT =====
    if ($Mode -eq "import" -or $Mode -eq "full") {
        Write-Host "`n=== IMPORT ==="
        $srcDir = if ($AnnotatedDir -and (Test-Path $AnnotatedDir)) { $AnnotatedDir } else { $notedDir }
        if (-not (Test-Path $srcDir)) {
            Write-Host "No SCL files in $srcDir"
        } else {
            # Load block info
            $blockInfo = @{}
            if (Test-Path $groupFile) {
                $json = (Get-Content $groupFile -Raw) | ConvertFrom-Json
                foreach ($prop in $json.PSObject.Properties) {
                    $val = $prop.Value
                    if ($val -is [string]) { $blockInfo[$prop.Name] = @{ Plc=""; Group=$val; Number=0 } }
                    else { $blockInfo[$prop.Name] = @{ Plc=$val.Plc; Group=$val.Group; Number=$val.Number } }
                }
                Write-Host "Block info loaded: $($blockInfo.Count)"
            }

            $totalOk = 0; $totalFail = 0

            foreach ($plc in $allPlcs) {
                $plcName = $plc.Name
                $plcDirName = ($plcName -replace '[\\/:*?"<>|]', '_')
                $plcSrcDir = Join-Path $srcDir $plcDirName
                if (-not (Test-Path $plcSrcDir)) { continue }

                $files = Get-ChildItem $plcSrcDir -Filter "*.scl"
                $esg = $plc.ExternalSourceGroup
                $ok = 0; $fail = 0

                foreach ($f in $files) {
                    $blockName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
                    $key = "$plcName`n$blockName"
                    $info = $blockInfo[$key]
                    $savedGroup = if ($info) { $info.Group } else { "" }
                    $savedNumber = if ($info -and $info.Number) { [int]$info.Number } else { 0 }
                    try {
                        $old = FindBlock $plc.BlockGroup $blockName
                        if ($old) { $old.Delete() }
                        $oldES = $esg.ExternalSources.Find($blockName)
                        if ($oldES) { $oldES.Delete() }
                        $es = $esg.ExternalSources.CreateFromFile($blockName, $f.FullName)
                        if ($savedGroup) {
                            $tg = EnsureGroup $plc.BlockGroup $savedGroup
                            if ($tg) { $es.GenerateBlocksFromSource($tg, [Siemens.Engineering.SW.ExternalSources.GenerateBlockOption]::None) }
                            else { $es.GenerateBlocksFromSource() }
                        } else { $es.GenerateBlocksFromSource() }
                        if ($savedNumber -gt 0) {
                            $nb = FindBlock $plc.BlockGroup $blockName
                            if ($nb) { try { $np=$nb.GetType().GetProperty('Number'); if($np-and$np.CanWrite){$np.SetValue($nb,$savedNumber)} } catch{} }
                        }
                        $ok++
                    } catch { $fail++ }
                }
                Write-Host "  $plcName : $ok/$($files.Count)"
                $totalOk += $ok; $totalFail += $fail

                # Compile
                try {
                    $cs = GetSvc $plc ([Siemens.Engineering.Compiler.ICompilable])
                    if ($cs) { $cr=$cs.GetType().GetMethod("Compile").Invoke($cs,$null); $s=$cr.GetType().GetProperty("State").GetValue($cr,$null).ToString(); $e=[int]$cr.GetType().GetProperty("ErrorCount").GetValue($cr,$null); Write-Host "  Compile: $s errors=$e" }
                } catch {}
            }
            Write-Host "Total: $totalOk ok, $totalFail fail"
        }
    }

    Write-Host "`nDONE"
} finally { $tia.Dispose() }
