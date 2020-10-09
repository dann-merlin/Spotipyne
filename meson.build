project('spotipyne',
          version: '0.1.0',
    meson_version: '>= 0.51.0',
  default_options: [ 'warning_level=2',
                   ],
)

python = import('python')
pyinst = python.find_installation('python3', modules: [ 'spotipy', 'xdg', 'gi.repository' ] )

dependency('libhandy-1', version: '>= 0.80.0')

i18n = import('i18n')


subdir('data')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
