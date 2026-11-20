param(
  [string]$MuiPath = 'C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui'
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class ResMgr3
{
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern IntPtr LoadLibraryEx(string lpFileName, IntPtr hFile, uint dwFlags);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool FreeLibrary(IntPtr hModule);
    public delegate bool EnumTypeProc(IntPtr h, IntPtr type, IntPtr lp);
    public delegate bool EnumNameProc(IntPtr h, IntPtr type, IntPtr name, IntPtr lp);
    public delegate bool EnumLangProc(IntPtr h, IntPtr type, IntPtr name, ushort lang, IntPtr lp);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EnumResourceTypes(IntPtr h, EnumTypeProc cb, IntPtr lp);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EnumResourceNames(IntPtr h, IntPtr type, EnumNameProc cb, IntPtr lp);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EnumResourceLanguages(IntPtr h, IntPtr type, IntPtr name, EnumLangProc cb, IntPtr lp);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr FindResource(IntPtr h, IntPtr name, IntPtr type);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr LoadResource(IntPtr h, IntPtr info);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr LockResource(IntPtr data);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SizeofResource(IntPtr h, IntPtr info);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern IntPtr BeginUpdateResource(string f, bool del);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode, EntryPoint = "UpdateResourceW")]
    public static extern bool UpdateResource(IntPtr h, IntPtr type, IntPtr name, ushort lang, byte[] data, uint size);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EndUpdateResource(IntPtr h, bool discard);

    public class Entry { public long TypeId; public string TypeStr; public long NameId; public string NameStr; public ushort Lang; public byte[] Data; }

    public static List<Entry> Read(string path)
    {
        var list = new List<Entry>();
        IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x22);
        if (h == IntPtr.Zero) throw new Exception("load failed " + Marshal.GetLastWin32Error());
        try
        {
            EnumTypeProc tc = (hm, type, lp) =>
            {
                long tId; string tStr;
                SplitKey(type, out tId, out tStr);
                EnumNameProc nc = (hm2, t2, name, lp2) =>
                {
                    long nId; string nStr;
                    SplitKey(name, out nId, out nStr);
                    EnumLangProc lc = (hm3, t3, n3, lang, lp3) =>
                    {
                        IntPtr info = FindResource(hm3, name, type);
                        if (info == IntPtr.Zero) return true;
                        uint sz = SizeofResource(hm3, info);
                        IntPtr d = LockResource(LoadResource(hm3, info));
                        if (d == IntPtr.Zero || sz == 0) return true;
                        byte[] buf = new byte[sz];
                        Marshal.Copy(d, buf, 0, (int)sz);
                        list.Add(new Entry { TypeId = tId, TypeStr = tStr, NameId = nId, NameStr = nStr, Lang = lang, Data = buf });
                        return true;
                    };
                    EnumResourceLanguages(hm2, type, name, lc, IntPtr.Zero);
                    return true;
                };
                EnumResourceNames(hm, type, nc, IntPtr.Zero);
                return true;
            };
            EnumResourceTypes(h, tc, IntPtr.Zero);
        }
        finally { FreeLibrary(h); }
        return list;
    }

    static void SplitKey(IntPtr p, out long id, out string str)
    {
        long v = p.ToInt64();
        if (v <= 0xFFFF) { id = v; str = null; }
        else { id = 0; str = Marshal.PtrToStringAnsi(p); }
    }
}
'@

$res = [ResMgr3]::Read($MuiPath)
Write-Output "totalResources=$($res.Count)"
$res | Group-Object { if ($_.TypeStr) { 'str:' + $_.TypeStr } else { 'id:' + $_.TypeId } } | ForEach-Object { Write-Output ("  type {0} count={1}" -f $_.Name, $_.Count) }

$enc = New-Object System.Text.UTF8Encoding($false)
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

$targets = @()
foreach ($r in $res) {
  $text = $enc.GetString($r.Data)
  if ($text.IndexOf('"text": "') -lt 0) { continue }
  $new = $text; $cnt = 0
  foreach ($k in $map.Keys) {
    $old = '"text": "' + $k + '"'
    if ($new.Contains($old)) { $new = $new.Replace($old, ('"text": "' + $map[$k] + '"')); $cnt++ }
  }
  if ($cnt -gt 0) { $targets += [pscustomobject]@{ Entry=$r; Data=$enc.GetBytes($new); Hits=$cnt } }
}
Write-Output "targets=$($targets.Count)"
foreach ($t in $targets) { Write-Output ("  name={0}/{1} lang=0x{2:X4} hits={3} bytes {4}->{5}" -f $t.Entry.NameId,$t.Entry.NameStr,$t.Entry.Lang,$t.Hits,$t.Entry.Data.Length,$t.Data.Length) }
if ($targets.Count -eq 0) { exit 0 }

$h = [ResMgr3]::BeginUpdateResource($MuiPath, $false)
if ($h -eq [IntPtr]::Zero) { throw ("BeginUpdateResource failed: " + [ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error()).Message) }
$allocs = @()
try {
  foreach ($t in $targets) {
    if ($t.Entry.TypeStr) { $tp = [Runtime.InteropServices.Marshal]::StringToHGlobalUni($t.Entry.TypeStr); $allocs += $tp } else { $tp = [IntPtr]$t.Entry.TypeId }
    if ($t.Entry.NameStr) { $np = [Runtime.InteropServices.Marshal]::StringToHGlobalUni($t.Entry.NameStr); $allocs += $np } else { $np = [IntPtr]$t.Entry.NameId }
    $ok = [ResMgr3]::UpdateResource($h, $tp, $np, [uint16]$t.Entry.Lang, $t.Data, [uint32]$t.Data.Length)
    $err = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
    Write-Output ("UpdateResource name={0} ok={1} err={2}" -f $t.Entry.NameId, $ok, $err)
  }
}
finally {
  $done = [ResMgr3]::EndUpdateResource($h, $false)
  Write-Output "EndUpdateResource=$done"
  foreach ($a in $allocs) { [Runtime.InteropServices.Marshal]::FreeHGlobal($a) }
}
