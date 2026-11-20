param(
  [string]$Path = 'C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui'
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class RPROBE {
  public static List<string> Log = new List<string>();
  public static List<byte[]> Found = new List<byte[]>();
  public static List<int> FoundIds = new List<int>();
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
  public static void Probe (string path, string wantType) {
    Log.Clear(); Found.Clear(); FoundIds.Clear();
    IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
    ET tc = (hm, t, l) => {
      string ts = t.ToInt64() <= 0xFFFF ? ("#" + t.ToInt64()) : Marshal.PtrToStringAnsi(t);
      EN nc = (hm2, t2, n, l2) => {
        string ns = n.ToInt64() <= 0xFFFF ? ("#" + n.ToInt64()) : Marshal.PtrToStringAnsi(n);
        EL lc = (hm3, t3, n3, la, l3) => {
          IntPtr info = FindResource(hm3, n3, t3);
          uint sz = info == IntPtr.Zero ? 0 : SizeofResource(hm3, info);
          Log.Add(ts + " | " + ns + " | lang=0x" + la.ToString("X4") + " | size=" + sz);
          if (ts == wantType) {
            IntPtr d = LockResource(LoadResource(hm3, info));
            if (d != IntPtr.Zero && sz > 0) {
              byte[] b = new byte[sz]; Marshal.Copy(d, b, 0, (int)sz);
              Found.Add(b); FoundIds.Add((int)n3.ToInt64());
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

[RPROBE]::Probe($Path, 'JSNL')
$i = 0
foreach ($b in [RPROBE]::Found) {
  $id = [RPROBE]::FoundIds[$i]
  $i++
  $txt = (New-Object System.Text.UTF8Encoding($false)).GetString($b)
  $out = "e:\works\Aidev\AddOn\acmepchi\.tmp\JSNL_$id.json"
  [System.IO.File]::WriteAllBytes($out, $b)
  Write-Output ("=== JSNL/$id size=$($b.Length) ductRoute=$($txt.Contains('Duct Route')) ductFlex=$($txt.Contains('Duct Flexible Segment')) head=" + $txt.Substring(0, [Math]::Min(160, $txt.Length)))
  Write-Output ("    dumped=$out")
}
