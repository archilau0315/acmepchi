param(
  [Parameter(Mandatory=$true)][string]$Mui,
  [Parameter(Mandatory=$true)][string]$Data,
  [string]$Type = 'JSNL',
  [int]$Id = 2002,
  [int]$Lang = 0x0409
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class UPD {
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] public static extern IntPtr BeginUpdateResource(string p, bool del);
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] public static extern bool UpdateResourceW(IntPtr h, IntPtr t, IntPtr n, ushort la, byte[] d, uint sz);
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] public static extern bool EndUpdateResourceW(IntPtr h, bool discard);
}
'@
$bytes = [System.IO.File]::ReadAllBytes($Data)
$h = [UPD]::BeginUpdateResource($Mui, $false)
if ($h -eq [IntPtr]::Zero) { throw ("BeginUpdateResource failed err=" + [Runtime.InteropServices.Marshal]::GetLastWin32Error()) }
$typePtr = [Runtime.InteropServices.Marshal]::StringToHGlobalUni($Type)
try {
  $ok = [UPD]::UpdateResourceW($h, $typePtr, [IntPtr]$Id, [uint16]$Lang, $bytes, [uint32]$bytes.Length)
  $err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
  $end = [UPD]::EndUpdateResourceW($h, $false)
  $endErr = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
} finally {
  [Runtime.InteropServices.Marshal]::FreeHGlobal($typePtr)
}
Write-Output ("update ok=$ok err=$err | end=$end err=$endErr")
