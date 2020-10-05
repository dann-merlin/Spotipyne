#!/bin/sh

which dex || exit 1
which flatpak-builder || exit 1
which flatpak || exit 1

dir="$(dirname "$(readlink -f $0)")"
buildDir="${dir}/build"

flatpak-builder --force-clean "${buildDir}" xyz.merlinx.Spotipyne.json
dex "${buildDir}/export/share/applications/xyz.merlinx.Spotipyne.desktop"
