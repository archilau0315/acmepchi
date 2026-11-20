param(
  [string]$Path = 'C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui',
  [string]$Needle = 'Electrical'
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class RDUMP {
  public static List<string> Log = new List<string>();
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
    Log.Clear(); Names.Clear(); Datas.Clear();
    IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
    ET tc = (hm, t, l) => {
      string ts = t.ToInt64() <= 0xFFFF ? ("#" + t.ToInt64()) : Marshal.PtrToStringAnsi(t);
      EN nc = (hm2, t2, n, l2) => {
        string ns = n.ToInt64() <= 0xFFFF ? ("#" + n.ToInt64()) : Marshal.PtrToStringAnsi(n);
        EL lc = (hm3, t3, n3, la, l3) => {
          IntPtr info = FindResource(hm3, n3, t3);
          uint sz = info == IntPtr.Zero ? 0 : SizeofResource(hm3, info);
          Log.Add(ts + "/" + ns);
          if (info != IntPtr.Zero && sz > 0) {
            IntPtr d = LockResource(LoadResource(hm3, info));
            if (d != IntPtr.Zero) {
              byte[] b = new byte[sz]; Marshal.Copy(d, b, 0, (int)sz);
              Names.Add(ts + "/" + ns); Datas.Add(b);
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

[RDUMP]::Dump($Path)
Write-Output ('--- ' + $Path)
[RDump]::Log | ForEach-Object { Write-Output $_ }
$n0 = $Needle
for ($i = 0; $i -lt [RDUMP]::Datas.Count; $i++) {
  $b = [RDUMP]::Datas[$i]
  $u = [System.Text.Encoding]::UTF8.GetString($b)
  $a = [System.Text.Encoding]::Unicode.GetString($b)
  if ($u.Contains($n0) -or $a.Contains($n0)) {
    Write-Output ("HIT " + [RDUMP]::Names[$i] + " utf8=" + $u.Contains($n0) + " utf16=" + $a.Contains($n0))
    $safe = ([RDUMP]::Names[$i] -replace '[\\/:*?"<>|]', '_')
    [System.IO.File]::WriteAllBytes("e:\works\Aidev\AddOn\acmepchi\.tmp\res_$safe.bin", $b)
  }
}
