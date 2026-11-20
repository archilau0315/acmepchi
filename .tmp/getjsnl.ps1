param(
  [Parameter(Mandatory=$true)][string]$Path,
  [int]$Id = 2002,
  [Parameter(Mandatory=$true)][string]$Out
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RDX {
  public static byte[] Out = null;
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
  public static void Get (string path, int id) {
    Out = null;
    IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
    ET tc = (hm, t, l) => {
      string ts = t.ToInt64() <= 0xFFFF ? ("#" + t.ToInt64()) : Marshal.PtrToStringAnsi(t);
      EN nc = (hm2, t2, n, l2) => {
        EL lc = (hm3, t3, n3, la, l3) => {
          if (ts == "JSNL" && n3.ToInt64() == id) {
            IntPtr info = FindResource(hm3, n3, t3);
            uint sz = SizeofResource(hm3, info);
            IntPtr d = LockResource(LoadResource(hm3, info));
            byte[] b = new byte[sz]; Marshal.Copy(d, b, 0, (int)sz);
            Out = b;
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
[RDX]::Get($Path, $Id)
if ($null -eq [RDX]::Out) { throw "JSNL/$Id not found" }
[System.IO.File]::WriteAllBytes($Out, [RDX]::Out)
$t = [System.Text.Encoding]::UTF8.GetString([RDX]::Out, 4, [RDX]::Out.Length - 4)
Write-Output ("size=" + [RDX]::Out.Length + " hasChinese=" + ($t -match '[\u4e00-\u9fff]') + " outline=" + $t.Substring(0, 200))
$i = $t.IndexOf('Duct Route Tool Strings')
if ($i -ge 0) { Write-Output ('ctx=' + $t.Substring($i, [Math]::Min(300, $t.Length - $i))) }
