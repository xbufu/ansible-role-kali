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
# Desktop user. root and this user both get the login shell, dotfiles and
# xfce power settings. Set it when Ansible connects as root.
kali_user: '{{ ansible_user }}'
# Login shell of root and kali_user, for example /usr/bin/zsh. zsh is never removed.
kali_shell: /bin/bash
# Keyboard layouts (first is the default) and the switch shortcut (Super+Space).
kali_keyboard_layouts: us,de
kali_keyboard_switch: grp:win_space_toggle
# QTerminal [General] settings for root and kali_user.
kali_qterminal_settings:
  fontSize: 12
  TerminalTransparency: 0
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
