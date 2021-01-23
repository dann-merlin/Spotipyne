{ pkgs ? import <nixpkgs> {} }:
pkgs.callPackage 
({ python3
, meson
, ninja
, wrapGAppsHook
, pkg-config
, gettext
, appstream-glib
, desktop-file-utils
, gobject-introspection
, libhandy
, gtk3
}:

python3.pkgs.buildPythonApplication {
  pname = "spotipyne";
  version = "0.0";

  format = "other";

  src = builtins.filterSource
    (path: type: baseNameOf path != "build") ./.;

  nativeBuildInputs = [ 
    meson
    ninja
    wrapGAppsHook 
    pkg-config
    gettext
    appstream-glib
    desktop-file-utils
    gobject-introspection
  ];

  buildInputs = [
    libhandy
    gtk3
  ];

  propagatedBuildInputs = with python3.pkgs; [
    pygobject3
    pyxdg
    spotipy
  ];

  preBuild = ''
    substituteInPlace ../meson.build \
      --replace "meson.add_install_script('build-aux/meson/postinstall.py')" ""
  '';

  strictDeps = false;

}) { }
