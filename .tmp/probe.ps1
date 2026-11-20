$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @"
using System;using System.Runtime.InteropServices;
public static class U{
 public static byte[] Res; public static string TypeName; public static int NameId; public static int Lang;
 [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] public static extern IntPtr LoadLibraryEx(string f,IntPtr h,uint fl);
 [DllImport("kernel32.dll")] public static extern bool FreeLibrary(IntPtr h);
 public delegate bool ET(IntPtr h,IntPtr t,IntPtr l);
 public delegate bool EN(IntPtr h,IntPtr t,IntPtr n,IntPtr l);
 public delegate bool EL(IntPtr h,IntPtr t,IntPtr n,ushort la,IntPtr l);
 [DllImport("kernel32.dll")] public static extern bool EnumResourceTypes(IntPtr h,ET cb,IntPtr l);
 [DllImport("kernel32.dll")] public static extern bool EnumResourceNames(IntPtr h,IntPtr t,EN cb,IntPtr l);
 [DllImport("kernel32.dll")] public static extern bool EnumResourceLanguages(IntPtr h,IntPtr t,IntPtr n,EL cb,IntPtr l);
 [DllImport("kernel32.dll")] public static extern IntPtr FindResource(IntPtr h,IntPtr n,IntPtr t);
 [DllImport("kernel32.dll")] public static extern IntPtr LoadResource(IntPtr h,IntPtr i);
 [DllImport("kernel32.dll")] public static extern IntPtr LockResource(IntPtr d);
 [DllImport("kernel32.dll")] public static extern uint SizeofResource(IntPtr h,IntPtr i);
 [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode)] public static extern IntPtr BeginUpdateResource(string f,bool d);
 [DllImport("kernel32.dll",SetLastError=true,CharSet=CharSet.Unicode,EntryPoint="UpdateResourceW")] public static extern bool UpdateResource(IntPtr h,IntPtr t,IntPtr n,ushort l,byte[] b,uint s);
 [DllImport("kernel32.dll",SetLastError=true)] public static extern bool EndUpdateResource(IntPtr h,bool d);
 public static void Get(string path){
   Res=null;TypeName=null;NameId=0;Lang=0;
   IntPtr h=LoadLibraryEx(path,IntPtr.Zero,0x22);
   ET tc=(hm,t,l)=>{ EN nc=(hm2,t2,n,l2)=>{ EL lc=(hm3,t3,n3,la,l3)=>{
      IntPtr info=FindResource(hm3,n,t); if(info==IntPtr.Zero) return true;
      uint sz=SizeofResource(hm3,info); IntPtr d=LockResource(LoadResource(hm3,info));
      if(d==IntPtr.Zero||sz==0) return true; byte[] b=new byte[sz]; Marshal.Copy(d,b,0,(int)sz);
      var txt=System.Text.Encoding.UTF8.GetString(b);
      if(txt.Contains("\"#id\"")){ Res=b; long tv=t.ToInt64(); TypeName = tv<=0xFFFF? null : Marshal.PtrToStringAnsi(t); long nv=n.ToInt64(); NameId=(int)nv; Lang=la; }
      return true; };
      EnumResourceLanguages(hm2,t,n,lc,IntPtr.Zero); return true; };
     EnumResourceNames(hm,t,nc,IntPtr.Zero); return true; };
   EnumResourceTypes(h,tc,IntPtr.Zero); FreeLibrary(h);
 }
}
"@
$f='C:\Program Files\GRAPHISOFT\MEP Designer 30\zh-CN\MEPPluginUI.dll.mui'
$tmp='e:\works\Aidev\AddOn\acmepchi\.tmp\probe.mui'
Copy-Item -LiteralPath $f -Destination $tmp -Force
[U]::Get($tmp)
$bytes=[U]::Res
Write-Output "bytes=$($bytes.Length) type=$([U]::TypeName) name=$([U]::NameId) lang=$([U]::Lang)"
$h=[U]::BeginUpdateResource($tmp,$false)
$tp=[Runtime.InteropServices.Marshal]::StringToHGlobalUni('MUI')
$np=[IntPtr]([U]::NameId)
$r1=[U]::UpdateResource($h,$tp,$np,[uint16]([U]::Lang),$bytes,[uint32]$bytes.Length)
Write-Output "same ok=$r1 err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
$enc=New-Object System.Text.UTF8Encoding($false)
$txt=$enc.GetString($bytes)
$new=$txt.Replace('"text": "Duct Route"','"text": "风管路线"')
$nb=$enc.GetBytes($new)
$r2=[U]::UpdateResource($h,$tp,$np,[uint16]([U]::Lang),$nb,[uint32]$nb.Length)
Write-Output "zh ok=$r2 err=$([Runtime.InteropServices.Marshal]::GetLastWin32Error()) size=$($nb.Length)"
[void][U]::EndUpdateResource($h,$false)
Write-Output 'done'