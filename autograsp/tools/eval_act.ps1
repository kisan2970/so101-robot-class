# Real-robot eval of an ACT checkpoint (fixed task "Move the dice to the left cell.").
# Usage: powershell -ExecutionPolicy Bypass -File autograsp\tools\eval_act.ps1 [-Scale 1.0] [-Trials 3] [-Ckpt <pretrained_model dir>]
param(
    [double]$Scale = 1.0,
    [int]$Trials = 3,
    [string]$Ckpt = (Join-Path $PSScriptRoot "..\..\outputs\train\act_left_p1\checkpoints\last\pretrained_model"),
    [string]$Condition = "act-dice-left",
    [string]$Executor = "async",   # async + smoothing hides the jump between action chunks
    [int]$Smooth = 8
)
& (Join-Path $PSScriptRoot "..\..\.venv\Scripts\python.exe") (Join-Path $PSScriptRoot "run_eval.py") `
    --policy $Ckpt --rename-map "{}" --left-task --trials $Trials --speed-scale $Scale --max-seconds 40 --condition $Condition `
    --executor $Executor --smooth $Smooth
