param([parameter(mandatory=$false)] [string]$rez_dir = "")

function Download-GithubRelease {
    param(
        [parameter(mandatory=$true)] [string]$repo,
        [parameter(mandatory=$false)] [string]$file = ""
    )

    $releases = "https://api.github.com/repos/$repo/releases"
    # Determining the latest release
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
        Invoke-WebRequest $download -out $file -usebasicparsing
        return $file
    }

    $zip = "$name-$tag.zip"
    $dir = "$name-$tag"

    Invoke-WebRequest $download -out $zip -usebasicparsing
    Expand-Archive $zip -force

    # Moving from temp dir to target dir
    Move-Item $dir\$name -destination $name -force

    # Removing temp files
    Remove-Item $zip -force
    Remove-Item $dir -recurse -force

    return $name
}

function Install-Rez {
    Write-Output "Installing Rez..."
    # Get install dir if not provided
    if ($rez_dir -eq "" -and $null -ne $install_root) {
        $rez_dir = "$install_root/rez"
    }

    # Prompt for install dir if not provided
    elseif ($rez_dir -eq "") {
        $rez_dir = Read-Host "rez install root directory : "
    }
    $rez_source = Download-GithubRelease -repo "nerdvegas/rez"

    # Install rez
    Invoke-Expression "python $(Resolve-Path $rez_source)\install.py $rez_dir"
    $env:PATH=$env:PATH + ";$rez_dir\scripts\rez"
    [environment]::SetEnvironmentVariable('path', $env:PATH, 'user')
    Remove-Item $rez_source -recurse -force
    $env:REZ=$rez_dir
    [environment]::SetEnvironmentVariable('REZ', $env:REZ, 'user')
    $env:PYTHONPATH=$env:PYTHONPATH + ";$rez_dir\lib\site-packages"
    [environment]::SetEnvironmentVariable('PYTHONPATH', $env:PYTHONPATH, 'user')

    # Install config
    $rez_config = Join-Path -path $((Get-Item $PSCommandPath).Directory.Parent.FullName) -childPath "config/rez/rezconfig.py"
    $rez_config = Copy-Item -path $rez_config -destination $(Join-Path -path $rez_dir -childPath "rezconfig.py")
    $env:REZ_CONFIG_FILE=$rez_config
    [environment]::SetEnvironmentVariable('REZ_CONFIG_FILE', $env:REZ_CONFIG_FILE, 'user')

    # Create some default packages
    rez-bind --quickstart
}

function Install-RezPackages {
    # TODO: Find a way to parse package.py and loop over the requires variable
    foreach($package in @("yapf", "pylint", "pytest", "PyYAML", "logzero", "websockets")) {
        Invoke-Expression("rez pip --install $package --python-version 3.7")
    }
}

# Start the installation
if (-not (Get-Command "rez")) {
    Install-Rez
}
Install-RezPackages
