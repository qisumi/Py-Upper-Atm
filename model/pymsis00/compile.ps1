<# build_msis00.ps1（优化版）
   - 参考 pymsis2 的最佳实践
   - 增加错误处理和输出目录管理
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
$CommonFFLAGS = @("-O3")
$ModOut = @("-J", $OutDir)
$ModIncl = @("-I", $OutDir)

# 3) 源码依赖顺序
$SourcesInOrder = @(
  "msis00.f",
  "msis00_cshim.F90"
) | ForEach-Object { Join-Path $Root $_ } | Where-Object { Test-Path $_ }

if (-not $SourcesInOrder) { throw "未找到库源码；请检查文件名/路径。" }

# 4) 编译
Write-Host "Compiling modules/objects (with -J $OutDir, -I $OutDir)..."
$objs = @()
foreach ($src in $SourcesInOrder) {
  $name = [IO.Path]::GetFileName($src)
  
  # 4.1 特殊处理 msis00.f (需要 legacy 标准和禁用范围检查)
  if ($name -eq "msis00.f") {
    Write-Host "Compiling $name with legacy standard..."
    $obj = Join-Path $OutDir "msis00.o"
    & $gfortran @CommonFFLAGS "-std=legacy" "-fno-range-check" @ModOut @ModIncl -c $src -o $obj
  } else {
    Write-Host "Compiling $name..."
    $obj = Join-Path $OutDir ("{0}.o" -f ([IO.Path]::GetFileNameWithoutExtension($src)))
    & $gfortran @CommonFFLAGS @ModOut @ModIncl -c $src -o $obj
  }
  $objs += $obj
}

if (-not $objs) { throw "没有可链接的对象文件（.o）。确认未把全部文件排空。" }

# 5) 链接 DLL + import lib（MinGW）
$dllPath = Join-Path $OutDir "msis00.dll"
$implibPath = Join-Path $OutDir "msis00.a"
Write-Host "Linking DLL..."
& $gfortran -shared @objs -o $dllPath "-Wl,--out-implib,$implibPath" `
  -static-libgcc -static-libgfortran -static-libquadmath

# 6) 清理临时文件
Write-Host "Cleaning up temporary files..."
Remove-Item "$OutDir\*.mod" -ErrorAction SilentlyContinue
Remove-Item "$OutDir\*.o" -ErrorAction SilentlyContinue

Write-Host "`n✅ 成功："
Write-Host "  DLL:    $dllPath"
Write-Host "  Implib: $implibPath"