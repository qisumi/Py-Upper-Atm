# HWM93 编译脚本
# 编译 HWM93 Fortran 源代码为 Windows 共享库

Write-Host "开始编译 HWM93..." -ForegroundColor Green

# 检查源文件是否存在
if (-not (Test-Path "hwm93.f")) {
    Write-Error "错误: 找不到 hwm93.f 文件"
    exit 1
}

if (-not (Test-Path "hwm93_cshim.F90")) {
    Write-Error "错误: 找不到 hwm93_cshim.F90 文件"
    exit 1
}

# 编译源文件为目标文件
Write-Host "正在编译 hwm93.f..." -ForegroundColor Yellow
$compileResult1 = gfortran -O3 -c hwm93.f
if ($LASTEXITCODE -ne 0) {
    Write-Error "编译 hwm93.f 失败"
    exit 1
}

Write-Host "正在编译 hwm93_cshim.F90..." -ForegroundColor Yellow
$compileResult2 = gfortran -O3 -c hwm93_cshim.F90
if ($LASTEXITCODE -ne 0) {
    Write-Error "编译 hwm93_cshim.F90 失败"
    exit 1
}

# 链接为共享库
Write-Host "正在链接生成 hwm93.dll..." -ForegroundColor Yellow
$linkResult = gfortran -shared -o hwm93.dll hwm93.o hwm93_cshim.o "-Wl,--out-implib,hwm93.a" -static-libgcc -static-libgfortran -static-libquadmath
if ($LASTEXITCODE -ne 0) {
    Write-Error "链接生成 hwm93.dll 失败"
    exit 1
}

# 清理临时文件
Write-Host "正在清理临时文件..." -ForegroundColor Yellow
Remove-Item *.mod -ErrorAction SilentlyContinue
Remove-Item *.o -ErrorAction SilentlyContinue

Write-Host "HWM93 编译完成!" -ForegroundColor Green