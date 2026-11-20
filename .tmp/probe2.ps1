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
  public static byte[] OutBytes = null;
  public static int FoundLang = 0;
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
  public static void Probe (string path, string wantType, int wantId) {
    Log.Clear(); OutBytes = null; FoundLang = 0;
    IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
    ET tc = (hm, t, l) => {
      string ts = t.ToInt64() <= 0xFFFF ? ("#" + t.ToInt64()) : Marshal.PtrToStringAnsi(t);
      EN nc = (hm2, t2, n, l2) => {
        string ns = n.ToInt64() <= 0xFFFF ? ("#" + n.ToInt64()) : Marshal.PtrToStringAnsi(n);
        EL lc = (hm3, t3, n3, la, l3) => {
          IntPtr info = FindResource(hm3, n3, t3);
          uint sz = info == IntPtr.Zero ? 0 : SizeofResource(hm3, info);
          Log.Add(ts + " | " + ns + " | lang=0x" + la.ToString("X4") + " | size=" + sz);
          if (ts == wantType && n3.ToInt64() == wantId && OutBytes == null) {
            IntPtr d = LockResource(LoadResource(hm3, info));
            if (d != IntPtr.Zero && sz > 0) {
              byte[] b = new byte[sz]; Marshal.Copy(d, b, 0, (int)sz);
              OutBytes = b; FoundLang = la;
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

[RPROBE]::Probe($Path, 'MUI', 2002)
Write-Output ('--- resource table of ' + $Path)
[RPROBE]::Log | ForEach-Object { Write-Output $_ }
$b = [RPROBE]::OutBytes
if ($null -eq $b) { Write-Output 'MUI/2002 NOT FOUND'; exit 1 }
Write-Output ('--- MUI 2002 size=' + $b.Length + ' lang=0x' + ('{0:X4}' -f [RPROBE]::FoundLang))
$txt = (New-Object System.Text.UTF8Encoding($false)).GetString($b)
Write-Output ('head=' + $txt.Substring(0, [Math]::Min(300, $txt.Length)))
Write-Output ('containsDuctRoute=' + $txt.Contains('Duct Route'))
Write-Output ('containsDuctFlex=' + $txt.Contains('Duct Flexible Segment'))
$out = 'e:\works\Aidev\AddOn\acmepchi\.tmp\MEPPluginUI.mui.2002.json'
[System.IO.File]::WriteAllBytes($out, $b)
Write-Output ('dumped=' + $out)
