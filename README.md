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
