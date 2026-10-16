# Separate venv for the SmolVLA comparison model. The working teleop venv (.venv) is not touched.
# Downloads: torch/torchvision cu128 wheels (~3 GB), transformers + deps (~100 MB),
# and on first training run the lerobot/smolvla_base weights from the Hugging Face Hub (~0.9 GB).
# Run:  powershell -ExecutionPolicy Bypass -File autograsp\setup_smolvla_env.ps1
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .venv-smolvla)) { & .\.venv\Scripts\python.exe -m venv .venv-smolvla }
$py = ".\.venv-smolvla\Scripts\python.exe"
& $py -m pip install --upgrade pip
# same torch build as the working venv so GPU behaviour is comparable
& $py -m pip install "torch==2.11.0" "torchvision==0.26.0" --index-url https://download.pytorch.org/whl/cu128
& $py -m pip install -e ".\lerobot[smolvla,training,feetech]"
& $py -c "import torch, transformers, lerobot; print('torch', torch.__version__, torch.cuda.is_available(), 'transformers', transformers.__version__)"
