#!/usr/bin/env bash

sudo apt update

# apt essentials

sudo apt install -y xorg lazygit redshift qalc dunst feh picom qutebrowser python3 make clang gcc ninja-build gettext cmake curl build-essential

# cmatrix

if command -v cmatrix &> /dev/null; then
else
  sudo curl -L https://raw.githubusercontent.com/will8211/unimatrix/master/unimatrix.py -o /usr/local/bin/unimatrix
  sudo chmod a+rx /usr/local/bin/unimatrix
fi

# dwm

git clone https://github.com/Denis-Pe/dwm.git ~/sources/dwm && \
  cd ~/sources/dwm && \
  sudo make clean install && \
  echo "dwm installed" && \
  sleep 5s

# dmenu

git clone https://github.com/Denis-Pe/dmenu.git ~/sources/dmenu && \
  cd ~/sources/dmenu && \
  sudo make clean install && \
  echo "dmenu installed" && \
  sleep 5s

# neovim

git clone https://github.com/neovim/neovim.git ~/sources/neovim && \
  cd ~/sources/neovim &&  \
  make CMAKE_BUILD_TYPE=RelWithDebInfo && \
  cd build && cpack -G DEB && sudo dpkg -i nvim-linux-x86_64.deb
