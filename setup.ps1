# One-time setup on a student PC (Windows, Python 3.12, Git).
# Run from the repository folder:
#   powershell -ExecutionPolicy Bypass -File setup.ps1
# Creates .venv, clones LeRobot at the tested commit, applies the small SO-101 follower patch, installs packages.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$LEROBOT_COMMIT = "9db9c35cb473afe3d9bf7b54fa5fd44576974f75"   # LeRobot 0.5.2 dev, tested with this project

if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip

if (-not (Test-Path lerobot)) {
    git clone -c core.autocrlf=false https://github.com/huggingface/lerobot.git lerobot   # LF files so the patch applies
    git -C lerobot checkout $LEROBOT_COMMIT
    git -C lerobot apply ..\patches\lerobot_so_follower.patch
}

# CUDA build of PyTorch (NVIDIA GPU). Without an NVIDIA GPU, delete "--index-url ..." to get the CPU build.
& $py -m pip install "torch==2.11.0" "torchvision==0.26.0" --index-url https://download.pytorch.org/whl/cu128
& $py -m pip install -e ".\lerobot[feetech,training]" pynput opencv-python
& $py -c "import torch, lerobot, cv2, pynput; print('OK  torch', torch.__version__, 'cuda', torch.cuda.is_available())"
