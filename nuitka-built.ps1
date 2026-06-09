param(
    [string]$OutputDir = "dist\nuitka",
    [string]$OutputName = "PCST.exe",
    [int]$Jobs = 2
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path $PSScriptRoot
$OutputPath = Join-Path $ProjectRoot $OutputDir

Push-Location $ProjectRoot
try {
    uv run --group build nuitka `
        --standalone `
        --windows-console-mode=disable `
        --enable-plugin=pyside6 `
        --include-qt-plugins=sensible,styles `
        --include-package-data=pypinyin `
        --include-package-data=pydicom `
        --include-package=pydicom.pixels `
        --include-module=pcst.models.mobile_sam `
        --include-data-dir="src\pcst\icons=icons" `
        --include-data-files="src\pcst\models\checkpoints\mobile_sam_encoder.onnx=models\checkpoints\mobile_sam_encoder.onnx" `
        --include-data-files="src\pcst\models\checkpoints\mobile_sam_decoder.onnx=models\checkpoints\mobile_sam_decoder.onnx" `
        --windows-icon-from-ico="src\pcst\icons\logo.ico" `
        --output-dir="$OutputPath" `
        --show-progress `
        --assume-yes `
        --lto=no `
        --jobs=$Jobs `
        --output-filename="$OutputName" `
        "src\pcst\main.py"
}
finally {
    Pop-Location
}
