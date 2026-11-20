param(
  [string]$Path = 'C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui',
  [string]$OutDir = 'e:\works\Aidev\AddOn\acmepchi\.tmp\zhres'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class RD3 {
  public static List<string> Names = new List<string>();
  public static List<byte[]> Datas = new List<byte[]>();
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
  public static void Dump (string path) {
    Names.Clear(); Datas.Clear();
    IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
    ET tc = (hm, t, l) => {
      string ts = t.ToInt64() <= 0xFFFF ? ("#" + t.ToInt64()) : Marshal.PtrToStringAnsi(t);
      EN nc = (hm2, t2, n, l2) => {
        string ns = n.ToInt64() <= 0xFFFF ? ("#" + n.ToInt64()) : Marshal.PtrToStringAnsi(n);
        EL lc = (hm3, t3, n3, la, l3) => {
          IntPtr info = FindResource(hm3, n3, t3);
          uint sz = info == IntPtr.Zero ? 0 : SizeofResource(hm3, info);
          if (info != IntPtr.Zero && sz > 0) {
            IntPtr d = LockResource(LoadResource(hm3, info));
            if (d != IntPtr.Zero) {
              byte[] b = new byte[sz]; Marshal.Copy(d, b, 0, (int)sz);
              Names.Add(ts + "_" + ns); Datas.Add(b);
            }
          }
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
[RD3]::Dump($Path)
for ($i = 0; $i -lt [RD3]::Datas.Count; $i++) {
  $name = [RD3]::Names[$i]
  $b = [RD3]::Datas[$i]
  $fn = Join-Path $OutDir ($name + '.bin')
  [System.IO.File]::WriteAllBytes($fn, $b)
  $head = ($b[0..([Math]::Min(15, $b.Length-1))] | ForEach-Object { $_.ToString('X2') }) -join ' '
  Write-Output ("$name size=$($b.Length) head=$head")
}
