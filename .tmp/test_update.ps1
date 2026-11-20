$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @"
using System;using System.Runtime.InteropServices;
public static class T{
 [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] public static extern IntPtr BeginUpdateResource(string f,bool d);
 [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode,EntryPoint="UpdateResourceW")] public static extern bool UpdateResource(IntPtr h,IntPtr t,IntPtr n,ushort l,byte[] b,uint s);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool EndUpdateResource(IntPtr h,bool d);
 public static int LastErr(){return Marshal.GetLastWin32Error();}
}
"@
$f='e:\works\Aidev\AddOn\acmepchi\.tmp\MEPPluginUI.dll.mui'
$h=[T]::BeginUpdateResource($f,$false)
Write-Output "h=$h"
$tp=[Runtime.InteropServices.Marshal]::StringToHGlobalUni('MUI')
$data=[System.Text.Encoding]::UTF8.GetBytes('x')
$r=[T]::UpdateResource($h,$tp,[IntPtr]2002,0x0409,$data,1)
$e=[T]::LastErr()
Write-Output "tinyUpdate=$r err=$e"
$d2=[T]::EndUpdateResource($h,$true)
Write-Output "endDiscard=$d2"