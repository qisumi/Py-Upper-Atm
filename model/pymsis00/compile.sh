#!/bin/bash
# build_msis00.sh (Ubuntu 版本)
# - 参考 pymsis2 的最佳实践
# - 解决 .mod 路径与编译顺序

# 0) 错误处理设置
set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时退出

# 1) 工具链
if ! command -v gfortran >/dev/null 2>&1; then
    echo "错误: 未找到 gfortran 编译器" >&2
    exit 1
fi
gfortran_path=$(command -v gfortran)
echo "Using gfortran: $gfortran_path"

# 2) 目录
Root="$(dirname "$(readlink -f "$0")")"
cd "$Root"
OutDir="$Root/build"
mkdir -p "$OutDir"

# 3) 编译参数
CommonFFLAGS=("-O3")
ModOut=("-J" "$OutDir")
ModIncl=("-I" "$OutDir")

# 4) 源码依赖顺序
SourcesInOrder=(
    "msis00.f"
    "msis00_cshim.F90"
)

# 过滤存在的文件
ExistingSources=()
for src in "${SourcesInOrder[@]}"; do
    full_path="$Root/$src"
    if [ -f "$full_path" ]; then
        ExistingSources+=("$full_path")
    fi
done

if [ ${#ExistingSources[@]} -eq 0 ]; then
    echo "错误: 未找到库源码；请检查文件名/路径。" >&2
    exit 1
fi

# 5) 编译
echo "Compiling modules/objects (with -J $OutDir, -I $OutDir)..."
objs=()
for src in "${ExistingSources[@]}"; do
    name=$(basename "$src")
    
    # 5.1 特殊处理 msis00.f (需要 legacy 标准和禁用范围检查)
    if [ "$name" = "msis00.f" ]; then
        echo "Compiling $name with legacy standard..."
        obj="$OutDir/msis00.o"
        "$gfortran_path" "${CommonFFLAGS[@]}" "-std=legacy" "-fno-range-check" "${ModOut[@]}" "${ModIncl[@]}" -c "$src" -o "$obj"
    else
        echo "Compiling $name..."
        obj="$OutDir/$(basename "$src" .F90).o"
        "$gfortran_path" "${CommonFFLAGS[@]}" "${ModOut[@]}" "${ModIncl[@]}" -c "$src" -o "$obj"
    fi
    objs+=("$obj")
done

if [ ${#objs[@]} -eq 0 ]; then
    echo "错误: 没有可链接的对象文件（.o）。确认未把全部文件排空。" >&2
    exit 1
fi

# 6) 链接共享库
soPath="$OutDir/libmsis00.so"
echo "Linking shared library..."
"$gfortran_path" -shared "${objs[@]}" -o "$soPath" \
    -static-libgcc -static-libgfortran -static-libquadmath

# 7) 清理临时文件
echo "Cleaning up temporary files..."
rm -f "$OutDir"/*.mod "$OutDir"/*.o

echo ""
echo "✅ 成功："
echo "  共享库: $soPath"