Ansible Role: Kali
=========

An Ansible role to configure Kali.

Requirements
------------

None.

Role Variables
--------------

See `defaults/main.yml`.

```yml
# Login shell of ansible_user, for example /usr/bin/zsh. zsh is never removed.
kali_shell: /bin/bash
# GitHub user whose dotfiles repo chezmoi applies (github.com/<user>/dotfiles).
kali_chezmoi_user: xbufu
```

Inside a VM, the role installs guest tools on its own: `qemu-guest-agent` and
`spice-vdagent` on Proxmox/KVM, `open-vm-tools`, `open-vm-tools-desktop` and `fuse3` on
VMware, with shared folders mounted at `/mnt/hgfs` on boot (needs the
`ansible.posix` collection). Bare-metal installs skip this.

Dependencies
------------

None.

Example Playbook
----------------

```yml
```

License
-------

MIT / BSD

Author Information
------------------

Created by xbufu.
