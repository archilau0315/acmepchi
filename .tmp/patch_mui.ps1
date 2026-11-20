param(
  [string]$MuiPath = 'C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui'
)

$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public static class ResMgr
{
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern IntPtr LoadLibraryEx(string lpFileName, IntPtr hFile, uint dwFlags);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool FreeLibrary(IntPtr hModule);

    public delegate bool EnumResTypeProc(IntPtr hModule, IntPtr lpszType, IntPtr lParam);
    public delegate bool EnumResNameProc(IntPtr hModule, IntPtr lpszType, IntPtr lpszName, IntPtr lParam);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EnumResourceTypes(IntPtr hModule, EnumResTypeProc lpEnumFunc, IntPtr lParam);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EnumResourceNames(IntPtr hModule, IntPtr lpszType, EnumResNameProc lpEnumFunc, IntPtr lParam);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr FindResource(IntPtr hModule, IntPtr lpName, IntPtr lpType);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr LoadResource(IntPtr hModule, IntPtr hResInfo);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr LockResource(IntPtr hResData);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SizeofResource(IntPtr hModule, IntPtr hResInfo);

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern IntPtr BeginUpdateResource(string pFileName, bool bDeleteExistingResources);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool UpdateResource(IntPtr hUpdate, IntPtr lpType, IntPtr lpName, ushort wLanguage, byte[] lpData, uint cbData);
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool EndUpdateResource(IntPtr hUpdate, bool fDiscard);

    public class ResEntry
    {
        public IntPtr Type;
        public IntPtr Name;
        public byte[] Data;
    }

    public static List<ResEntry> ReadAll(string path)
    {
        var list = new List<ResEntry>();
        IntPtr h = LoadLibraryEx(path, IntPtr.Zero, 0x00000002 | 0x00000020); // LOAD_LIBRARY_AS_DATAFILE | AS_IMAGE_RESOURCE
        if (h == IntPtr.Zero) throw new Exception("LoadLibraryEx failed: " + Marshal.GetLastWin32Error());
        try
        {
            EnumResTypeProc typeCb = (hm, type, lp) =>
            {
                EnumResNameProc nameCb = (hm2, t2, name, lp2) =>
                {
                    IntPtr info = FindResource(hm2, name, t2);
                    if (info == IntPtr.Zero) return true;
                    uint size = SizeofResource(hm2, info);
                    IntPtr data = LockResource(LoadResource(hm2, info));
                    if (data == IntPtr.Zero || size == 0) return true;
                    byte[] buf = new byte[size];
                    Marshal.Copy(data, buf, 0, (int)size);
                    list.Add(new ResEntry { Type = t2, Name = name, Data = buf });
                    return true;
                };
                EnumResourceNames(hm, type, nameCb, IntPtr.Zero);
                return true;
            };
            EnumResourceTypes(h, typeCb, IntPtr.Zero);
        }
        finally { FreeLibrary(h); }
        return list;
    }
}
'@

$src = [ResMgr]::ReadAll($MuiPath)
Write-Output "resources=$($src.Count)"

$enc = New-Object System.Text.UTF8Encoding($false)

$map = [ordered]@{
  'Duct Route'                = '风管路线'
  'Duct Flexible Segment'     = '风管软管段'
  'Duct Rigid Segment'        = '风管刚性段'
  'Duct Branch'               = '风管分支'
  'Duct Take-Off'             = '风管支管'
  'Duct Fitting'              = '风管配件'
  'Duct Terminal'             = '风管末端'
  'Duct Accessory'            = '风管附件'
  'Pipe Route'                = '管道路线'
  'Pipe Flexible Segment'     = '管道软管段'
  'Pipe Rigid Segment'        = '管道刚性段'
  'Pipe Branch'               = '管道分支'
  'Pipe Fitting'              = '管道配件'
  'Pipe Terminal'             = '管道末端'
  'Pipe Accessory'            = '管道附件'
  'Cable Carrier Route'       = '桥架路线'
  'Cable Carrier Branch'      = '桥架分支'
  'Cable Carrier Fitting'     = '桥架配件'
  'Equipment'                 = '设备'
  'Electrical Panel'          = '电气配电盘'
  'Electrical Device'         = '电气设备'
}

$pending = @()
$totalReplaced = 0
foreach ($r in $src) {
  $text = $enc.GetString($r.Data)
  if ($text.IndexOf('"text": "') -lt 0) { continue }
  $new = $text
  $cnt = 0
  foreach ($k in $map.Keys) {
    $old = '"text": "' + $k + '"'
    $rep = '"text": "' + $map[$k] + '"'
    if ($new.Contains($old)) { $new = $new.Replace($old, $rep); $cnt++ }
  }
  if ($cnt -gt 0) {
    $pending += [pscustomobject]@{ Type = $r.Type; Name = $r.Name; Data = $enc.GetBytes($new); Hits = $cnt }
    $totalReplaced += $cnt
  }
}

Write-Output "entriesToUpdate=$($pending.Count) totalHits=$totalReplaced"
if ($pending.Count -eq 0) { Write-Output 'nothing to update'; exit 0 }

Copy-Item -LiteralPath $MuiPath -Destination ($MuiPath + '.bak') -Force
$h = [ResMgr]::BeginUpdateResource($MuiPath, $false)
if ($h -eq [IntPtr]::Zero) { throw "BeginUpdateResource failed: $([ComponentModel.Win32Exception]::new([Runtime.InteropServices.Marshal]::GetLastWin32Error()).Message)" }
try {
  foreach ($p in $pending) {
    $ok = [ResMgr]::UpdateResource($h, $p.Type, $p.Name, 0, $p.Data, [uint32]$p.Data.Length)
    Write-Output ("update name={0} ok={1} bytes={2}" -f $p.Name, $ok, $p.Data.Length)
  }
}
finally {
  $done = [ResMgr]::EndUpdateResource($h, $false)
  Write-Output "EndUpdateResource=$done"
}
