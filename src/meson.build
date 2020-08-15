pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'spotipyne')
gnome = import('gnome')

gnome.compile_resources('spotipyne',
  'spotipyne.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'spotipyne.in',
  output: 'spotipyne',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

spotipyne_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'spotifyGuiBuilder.py',
  'coverArtLoader.py',
]

install_data(spotipyne_sources, install_dir: moduledir)
