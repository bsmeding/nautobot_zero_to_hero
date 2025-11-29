#!/bin/sh

sudo apt -y install bash-completion
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/bin
export PATH="$PATH:$HOME/bin"
eval "$(~/bin/task --completion bash)"
echo ""
echo "Run this now manually:"
echo ""
echo '  export PATH="$PATH:$HOME/bin"'
echo ""