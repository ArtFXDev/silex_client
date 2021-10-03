param([parameter(mandatory=$false)] [string]$rez_dir = "")

function download-githubrelease {
    param(
        [parameter(mandatory=$true)] [string]$repo,
        [parameter(mandatory=$false)] [string]$file = ""
    )

    $releases = "https://api.github.com/repos/$repo/releases"
    # determining the latest release
    $tag = (invoke-webrequest $releases -usebasicparsing | convertfrom-json)[0].tag_name

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
        invoke-webrequest $download -out $file -usebasicparsing
        return $file
    }

    $zip = "$name-$tag.zip"
    $dir = "$name-$tag"

    invoke-webrequest $download -out $zip -usebasicparsing
    expand-archive $zip -force

    # moving from temp dir to target dir
    move-item $dir\$name -destination $name -force

    # removing temp files
    remove-item $zip -force
    remove-item $dir -recurse -force

    return $name
}

function install-rez {
    if($null -ne $(get-command "rez" -erroraction silentlycontinue)) {
        return
    }
    write-output "downloading rez..."
    # set a default rez dir if not provided
    if ($rez_dir -eq "") {
        $rez_dir = "$home\rez"
    }
    $rez_source = download-githubrelease -repo "nerdvegas/rez"

    # install rez
    write-output "installing rez..."
    invoke-expression "python $(resolve-path $rez_source)\install.py `"$rez_dir`""
    $env:path=$env:path + ";$rez_dir\scripts\rez"
    [environment]::setenvironmentvariable('path', $env:path, 'user')
    if($CI) {add-content $env:GITHUB_PATH $env:path}
    remove-item $rez_source -recurse -force
    $env:rez=$rez_dir
    [environment]::setenvironmentvariable('rez', $env:rez, 'user')
    if($CI) {add-content $env:GITHUB_ENV "REZ=$env:rez"}
    $env:pythonpath=$env:pythonpath + ";$rez_dir\lib\site-packages"
    [environment]::setenvironmentvariable('pythonpath', $env:pythonpath, 'user')
    if($CI) {add-content $env:GITHUB_ENV "PYTHONPATH=$env:pythonpath"}
}

function setup-rez {
    # create some default packages
    write-output "binding default rez packages..."
    rez-bind --quickstart

    # run the install_dependencies script
    $install_dependencies = Join-Path -path $((Get-Item $PSCommandPath).Directory.FullName) -childPath "install_dependencies.py"
    rez-env rez -- "python $install_dependencies"
}

# start the installation
install-rez
setup-rez
