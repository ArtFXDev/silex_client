param([parameter(mandatory=$false)] [string]$rez_dir = "")

function Receive-GithubRelease {
    param(
        [parameter(mandatory=$true)] [string]$repo,
        [parameter(mandatory=$false)] [string]$file = ""
    )

    $releases = "https://api.github.com/repos/$repo/releases"
    # determining the latest release
    $tag = (Invoke-WebRequest $releases -UseBasicParsing | ConvertFrom-Json)[0].tag_name

    if ($file -eq "") {
        $file = "$tag.zip"
        $download = "https://github.com/$repo/archive/refs/tags/$file"
        $name = "$($repo.split("/")[1])-$tag"
    }
    else {
        $download = "https://github.com/$repo/releases/download/$tag/$file"
        $name = $file.split(".")[0]
    }

    if ($file.split(".")[-1] -ne "zip") {
        Invoke-WebRequest $download -Out $file -UseBasicParsing
        return $file
    }

    $zip = "$name-$tag.zip"
    $dir = "$name-$tag"

    Invoke-WebRequest $download -Out $zip -UseBasicParsing
    Expand-Archive $zip -Force

    # moving from temp dir to target dir
    Move-Item $dir\$name -Destination $name -Force

    # removing temp files
    Remove-Item $zip -Force
    Remove-Item $dir -Recurse -Force

    return $name
}

function Install-Rez {
    if($null -ne $(Get-Command "rez" -ErrorAction SilentlyContinue)) {
        return
    }
    Write-Output "downloading rez..."
    # set a default rez dir if not provided
    if ($rez_dir -eq "") {
        $rez_dir = "$home\rez"
    }
    $rez_source = Receive-GithubRelease -Repo "nerdvegas/rez"

    # install rez
    invoke-expression "python $(resolve-path $rez_source)\install.py `"$rez_dir`""
    $env:PATH=$env:PATH + ";$rez_dir\scripts\rez"
    [environment]::SetEnvironmentVariable('PATH', $env:PATH, 'User')
    if($env:CI) {Add-Content $env:GITHUB_PATH "$rez_dir\scripts\rez"}
    Remove-Item $rez_source -Recurse -Force
    $env:REZ=$rez_dir
    [environment]::SetEnvironmentVariable('REZ', $env:REZ, 'User')
    if($env:CI) {Add-Content $env:GITHUB_ENV "REZ=$env:REZ"}
    $env:PYTHONPATH=$env:PYTHONPATH + ";$rez_dir\lib\site-packages"
    [environment]::SetEnvironmentVariable('PYTHONPATH', $env:PYTHONPATH, 'User')
    if($env:CI) {Add-Content $env:GITHUB_ENV "PYTHONPATH=$env:PYTHONPATH"}
}

function Initialize-Rez {
    # create some default packages
    Write-Output "binding default rez packages..."
    rez-bind --quickstart

    # run the install_dependencies script
    Write-Output "installing silex's dependencies..."
    $install_dependencies = Join-Path -path $((Get-Item $PSCommandPath).Directory.FullName) -childPath "install_dependencies.py"
    rez-env rez python-3.7 -- "python $install_dependencies"
}

# start the installation
Install-Rez
Initialize-Rez
