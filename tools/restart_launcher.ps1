$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$runtime = Join-Path $root 'state\launcher\runtime.json'
if (Test-Path $runtime) {
    $info = Get-Content $runtime -Raw | ConvertFrom-Json
    if ($info.pid) { Stop-Process -Id $info.pid -Force -ErrorAction SilentlyContinue }
}
$client = 'D:\艾尔之光-客户端\艾尔之光-客户端\data\x2_dx11.exe'
if (-not (Test-Path $client) -and (Test-Path 'D:\艾尔之光-朋友服\data\x2_dx11.exe')) {
    $client = 'D:\艾尔之光-朋友服\data\x2_dx11.exe'
}
Start-Process -FilePath (Join-Path $root 'python\pythonw.exe') -ArgumentList '-B', (Join-Path $root '本地测试启动器.pyw'), '--client', $client -WorkingDirectory $root