<# build_nrlmsis2.ps1（稳健版）
   - 解决 .mod 路径与编译顺序
   - 稳定的样例/程序单元剔除（文件名模式 + program 语法探测）
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# 0) 工具链
$gfortran = (Get-Command gfortran -ErrorAction Stop).Source
Write-Host "Using gfortran: $gfortran"

# 1) 目录
$Root = Split-Path -Parent $PSCommandPath
Set-Location $Root
$OutDir = Join-Path $Root "build"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# 2) 编译参数
$useDoublePrecision = $false
$defines = @(); if ($useDoublePrecision) { $defines += "-DDBLE" }
$CommonFFLAGS = @("-O3","-cpp") + $defines
$ModOut  = @("-J", $OutDir)
$ModIncl = @("-I", $OutDir)

# 3) 源码依赖顺序（按你的仓库名实情改名）
$SourcesInOrder = @(
  "msis_constants.F90",
  "msis_init.F90",
  "alt2gph.F90",
  "msis_gfn.F90",
  "msis_tfn.F90",
  "msis_dfn.F90",
  "msis_calc.F90",
  "msis_gtd8d.F90",
  "msis_cshim.F90"
) | ForEach-Object { Join-Path $Root $_ } | Where-Object { Test-Path $_ }

if (-not $SourcesInOrder) { throw "未找到库源码；请检查文件名/路径。" }

# 4) 样例文件名规则 → 字符串数组
$SampleNamePatterns = @("hello.*","*test*.F","*test*.F90")
$AllFortran = Get-ChildItem -File -Include *.F90,*.F -Recurse:$false
$SampleNames = @()
foreach ($pat in $SampleNamePatterns) {
  $SampleNames += ($AllFortran | Where-Object { $_.Name -like $pat } | Select-Object -ExpandProperty Name)
}

# 5) 编译
Write-Host "Compiling modules/objects (with -J $OutDir, -I $OutDir)..."
$objs = @()
foreach ($src in $SourcesInOrder) {
  $name = [IO.Path]::GetFileName($src)

  # 5.1 名称层面过滤
  if ($SampleNames -contains $name) {
    Write-Host "Skip sample/program by name: $name"
    continue
  }

  # 5.2 语法层面过滤：如果包含顶级 program，跳过
  $hasProgram = Select-String -Path $src -Pattern '^\s*program\s+[A-Za-z_]\w*\s*$' -SimpleMatch:$false -Quiet
  if ($hasProgram) {
    Write-Host "Skip program unit detected: $name"
    continue
  }

  # 5.3 编译
  $obj = Join-Path $OutDir ("{0}.o" -f ([IO.Path]::GetFileNameWithoutExtension($src)))
  & $gfortran @CommonFFLAGS @ModOut @ModIncl -c $src -o $obj
  $objs += $obj
}

if (-not $objs) { throw "没有可链接的对象文件（.o）。确认未把全部文件排空。" }

# 6) 链接 DLL + import lib（MinGW）
$dllPath = Join-Path $OutDir "nrlmsis2.dll"
$implibPath = Join-Path $OutDir "libnrlmsis2.a"
Write-Host "Linking DLL..."
& $gfortran -shared @objs -o $dllPath "-Wl,--out-implib,$implibPath" `
  -static-libgcc -static-libgfortran -static-libquadmath

# 7) 参数文件
$parm = Join-Path $Root "msis2.0.parm"
if (Test-Path $parm) {
  Copy-Item $parm -Destination (Join-Path $OutDir "msis2.0.parm") -Force
} else {
  Write-Warning "未找到 msis2.0.parm。运行时需保证它与 DLL 同目录或在工作目录可读。"
}

Write-Host "`n✅ 成功："
Write-Host "  DLL:    $dllPath"
Write-Host "  Implib: $implibPath"
