param(
  [string]$MuiPath = 'C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui'
)
$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class MUIR {
  public static byte[] Res; public static int Lang;
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] public static extern IntPtr LoadLibraryEx(string f, IntPtr h, uint fl);
  [DllImport("kernel32.dll")] public static extern bool FreeLibrary(IntPtr h);
  public delegate bool ET(IntPtr h, IntPtr t, IntPtr l);
  public delegate bool EN(IntPtr h, IntPtr t, IntPtr n, IntPtr l);
  public delegate bool EL(IntPtr h, IntPtr t, IntPtr n, ushort la, IntPtr l);
  [DllImport("kernel32.dll")] public static extern bool EnumResourceTypes(IntPtr h, ET cb, IntPtr l);
  [DllImport("kernel32.dll")] public static extern bool EnumResourceNames(IntPtr h, IntPtr t, EN cb, IntPtr l);
  [DllImport("kernel32.dll")] public static extern bool EnumResourceLanguages(IntPtr h, IntPtr t, IntPtr n, EL cb, IntPtr l);
  [DllImport("kernel32.dll")] public static extern IntPtr FindResource(IntPtr h, IntPtr n, IntPtr t);
  [DllImport("kernel32.dll")] public static extern IntPtr LoadResource(IntPtr h, IntPtr i);
  [DllImport("kernel32.dll")] public static extern IntPtr LockResource(IntPtr d);
  [DllImport("kernel32.dll")] public static extern uint SizeofResource(IntPtr h, IntPtr i);
  public static void Load(string path) {
    Res = null; Lang = 0;
    IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
    ET tc = (hm, t, l) => {
      EN nc = (hm2, t2, n, l2) => {
        EL lc = (hm3, t3, n3, la, l3) => {
          long tv = t.ToInt64();
          string ts = tv <= 0xFFFF ? null : Marshal.PtrToStringAnsi(t);
          if (ts != "MUI") return true;
          IntPtr info = FindResource(hm3, n, t);
          if (info == IntPtr.Zero) return true;
          uint sz = SizeofResource(hm3, info);
          IntPtr d = LockResource(LoadResource(hm3, info));
          if (d == IntPtr.Zero || sz == 0) return true;
          byte[] b = new byte[sz]; Marshal.Copy(d, b, 0, (int)sz);
          if (System.Text.Encoding.UTF8.GetString(b).Contains("Duct Route")) { Res = b; Lang = la; }
          return true;
        };
        EnumResourceLanguages(hm2, t, n, lc, IntPtr.Zero);
        return true;
      };
      EnumResourceNames(hm, t, nc, IntPtr.Zero);
      return true;
    };
    EnumResourceTypes(h, tc, IntPtr.Zero);
    FreeLibrary(h);
  }
}
'@

$map = [ordered]@{
  'Duct Route'            = '风管路线'
  'Duct Flexible Segment' = '风管软管段'
  'Duct Rigid Segment'    = '风管刚性段'
  'Duct Branch'           = '风管分支'
  'Duct Take-Off'         = '风管支管'
  'Duct Fitting'          = '风管配件'
  'Duct Terminal'         = '风管末端'
  'Duct Accessory'        = '风管附件'
  'Pipe Route'            = '管道路线'
  'Pipe Flexible Segment' = '管道软管段'
  'Pipe Rigid Segment'    = '管道刚性段'
  'Pipe Branch'           = '管道分支'
  'Pipe Fitting'          = '管道配件'
  'Pipe Terminal'         = '管道末端'
  'Pipe Accessory'        = '管道附件'
  'Cable Carrier Route'   = '桥架路线'
  'Cable Carrier Branch'  = '桥架分支'
  'Cable Carrier Fitting' = '桥架配件'
  'Equipment'             = '设备'
  'Electrical Panel'      = '电气配电盘'
  'Electrical Device'     = '电气设备'
}

[MUIR]::Load($MuiPath)
$res = [MUIR]::Res
if ($null -eq $res) { throw 'MUI resource not found' }
Write-Output "resourceSize=$($res.Length) lang=0x$('{0:X4}' -f [MUIR]::Lang)"

$enc = New-Object System.Text.UTF8Encoding($false)
$text = $enc.GetString($res)

$hits = 0
foreach ($k in $map.Keys) {
  $old = '"text": "' + $k + '"'
  $rep = '"text": "' + $map[$k] + '"'
  $n = ([regex]::Matches($text, [regex]::Escape($old))).Count
  if ($n -gt 0) { $text = $text.Replace($old, $rep); $hits += $n }
}
Write-Output "replacedOccurrences=$hits"

$newBytes = $enc.GetBytes($text)
$delta = $res.Length - $newBytes.Length
Write-Output "delta=$delta (positive = need padding)"

if ($delta -lt 0) { throw "new content larger than original by $(-$delta) bytes; shorten translations" }

if ($delta -gt 0) {
  $pad = ' ' * $delta
  $idx = $text.LastIndexOf('}')
  if ($idx -lt 0) { throw 'cannot locate closing brace for padding' }
  $text = $text.Substring(0, $idx) + $pad + $text.Substring($idx)
  $newBytes = $enc.GetBytes($text)
}
if ($newBytes.Length -ne $res.Length) { throw "length mismatch $($newBytes.Length) vs $($res.Length)" }

try { [void]($text | ConvertFrom-Json) ; Write-Output 'json=valid' } catch { throw ("json invalid: " + $_.Exception.Message) }

$file = [System.IO.File]::ReadAllBytes($MuiPath)
# locate resource start by unique marker
$markerLen = 48
$marker = New-Object byte[] $markerLen
[Array]::Copy($res, 0, $marker, 0, $markerLen)
$positions = New-Object System.Collections.ArrayList
for ($i = 0; $i -le $file.Length - $markerLen; $i++) {
  if ($file[$i] -eq $marker[0]) {
    $ok = $true
    for ($j = 1; $j -lt $markerLen; $j++) { if ($file[$i+$j] -ne $marker[$j]) { $ok = $false; break } }
    if ($ok) { [void]$positions.Add($i) }
  }
}
Write-Output "markerMatches=$($positions.Count)"
if ($positions.Count -ne 1) { throw 'marker not unique, aborting' }
$start = $positions[0]
# verify the whole region matches
for ($j = 0; $j -lt $res.Length; $j++) {
  if ($file[$start + $j] -ne $res[$j]) { throw "region mismatch at offset $j" }
}
Copy-Item -LiteralPath $MuiPath -Destination ($MuiPath + '.bak-inplace') -Force
[Array]::Copy($newBytes, 0, $file, $start, $newBytes.Length)
[System.IO.File]::WriteAllBytes($MuiPath, $file)
Write-Output "written start=$start size=$($file.Length)"
