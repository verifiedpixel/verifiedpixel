#!/bin/sh
script_dir=$(readlink -e $(dirname "$0"))
$script_dir/server/doc-doc.py $script_dir/server/Dockerfile > $script_dir/server/INSTALL.md
$script_dir/server/doc-doc.py $script_dir/client/Dockerfile > $script_dir/client/INSTALL.md
