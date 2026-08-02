#!/usr/bin/env bash

sudo apt update

# apt essentials

sudo apt install -y xorg lazygit redshift qalc dunst feh picom qutebrowser python3 make clang gcc ninja-build gettext cmake curl build-essential libx11-dev libxft-dev libxinerama-dev unzip

# cmatrix

if ! command -v cmatrix &> /dev/null; then
  sudo curl -L https://raw.githubusercontent.com/will8211/unimatrix/master/unimatrix.py -o /usr/local/bin/unimatrix
  sudo chmod a+rx /usr/local/bin/unimatrix
fi

# dwm

if ! command -v dwm &> /dev/null; then
  git clone https://github.com/Denis-Pe/dwm.git ~/sources/dwm && \
    cd ~/sources/dwm && \
    sudo make clean install && \
    echo "dwm freshly installed" && \
    sleep 5s
fi

# dmenu

if ! command -v dmenu &> /dev/null; then
  sudo rm -rf ~/sources/dmenu
  git clone https://github.com/Denis-Pe/dmenu.git ~/sources/dmenu && \
    cd ~/sources/dmenu && \
    sudo make clean install && \
    echo "dmenu freshly installed" && \
    sleep 5s
fi

# st

if ! command -v st &> /dev/null; then
  sudo rm -rf ~/sources/st
  git clone https://github.com/Denis-Pe/st.git ~/sources/st && \
    cd ~/sources/st && \
    sudo make clean install && \
    echo "st freshly installed" && \
    sleep 5s
fi

# neovim

if ! command -v nvim &> /dev/null  ||  ! nvim -v | grep 0.11 &> /dev/null; then
  sudo rm -rf ~/sources/neovim/
  git clone -b release-0.11 --single-branch https://github.com/neovim/neovim.git ~/sources/neovim && \
    cd ~/sources/neovim &&  \
    make CMAKE_BUILD_TYPE=RelWithDebInfo && \
    cd build && cpack -G DEB && sudo dpkg -i nvim-linux-x86_64.deb
fi

# fonts

mkdir ~/.fonts
cd ~/.fonts

if ! ls | grep JetBrainsMonoNerdFont; then
  curl https://github.com/ryanoasis/nerd-fonts/releases/download/v3.4.0/JetBrainsMono.zip && \
    mkdir ~/.fonts && \
    unzip JetBrainsMono.zip .fonts && \
    echo "JetBrainsMono freshly installed" && \
    sleep 5s
fi
