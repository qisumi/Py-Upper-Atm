#!/bin/bash
# build_nrlmsis2.sh (Ubuntu 版本)
# - 解决 .mod 路径与编译顺序
# - 稳定的样例/程序单元剔除（文件名模式 + program 语法探测）

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
useDoublePrecision=false
defines=()
if [ "$useDoublePrecision" = true ]; then
    defines+=("-DDBLE")
fi
CommonFFLAGS=("-O3" "-cpp" "${defines[@]}")
ModOut=("-J" "$OutDir")
ModIncl=("-I" "$OutDir")

# 4) 源码依赖顺序
SourcesInOrder=(
    "msis_constants.F90"
    "msis_init.F90"
    "alt2gph.F90"
    "msis_gfn.F90"
    "msis_tfn.F90"
    "msis_dfn.F90"
    "msis_calc.F90"
    "msis_gtd8d.F90"
    "msis_cshim.F90"
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

# 5) 样例文件名规则
SampleNamePatterns=("hello.*" "*test*.F" "*test*.F90")
AllFortran=(*.F90 *.F)
SampleNames=()

# 获取匹配样例模式的文件名
for pattern in "${SampleNamePatterns[@]}"; do
    for file in "${AllFortran[@]}"; do
        if [[ "$file" == $pattern ]]; then
            SampleNames+=("$file")
        fi
    done
done

# 6) 编译
echo "Compiling modules/objects (with -J $OutDir, -I $OutDir)..."
objs=()
for src in "${ExistingSources[@]}"; do
    name=$(basename "$src")

    # 6.1 名称层面过滤
    if [[ " ${SampleNames[*]} " =~ " ${name} " ]]; then
        echo "Skip sample/program by name: $name"
        continue
    fi

    # 6.2 语法层面过滤：如果包含顶级 program，跳过
    if grep -E '^\s*program\s+[A-Za-z_]\w*\s*$' "$src" > /dev/null; then
        echo "Skip program unit detected: $name"
        continue
    fi

    # 6.3 编译
    obj="$OutDir/$(basename "$src" .F90).o"
    "$gfortran_path" "${CommonFFLAGS[@]}" "${ModOut[@]}" "${ModIncl[@]}" -c "$src" -o "$obj"
    objs+=("$obj")
done

if [ ${#objs[@]} -eq 0 ]; then
    echo "错误: 没有可链接的对象文件（.o）。确认未把全部文件排空。" >&2
    exit 1
fi

# 7) 链接共享库
soPath="$OutDir/libnrlmsis2.so"
echo "Linking shared library..."
"$gfortran_path" -shared "${objs[@]}" -o "$soPath" \
    -static-libgcc -static-libgfortran -static-libquadmath

# 8) 参数文件
parm="$Root/msis2.0.parm"
if [ -f "$parm" ]; then
    cp "$parm" "$OutDir/msis2.0.parm"
else
    echo "警告: 未找到 msis2.0.parm。运行时需保证它与共享库同目录或在工作目录可读。" >&2
fi

echo ""
echo "✅ 成功："
echo "  共享库: $soPath"