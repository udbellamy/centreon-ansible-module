# Centreon Ansible Module

## Intro

This module operates on a remote centreon server (hardcoded for now) for simple host ans services management

## Requirements

Tested ok with :

`ansible 2.2.0.0`
`python 3.5.1`
`centreon 2.8.4`

## Setup

You must put `centreon_host.py` and `centreon_service.py` in a folder called `library` where your task is called (role or playbook level)

## Centreon host

| Variable                          | Mandatory                         | Comments                                                                                        |
| :---                                   | :---                                      | :---                                                                                                     |
| `state`                            | `yes`                                 | `present` or `absent`                                                                      |
| `name`                           | `yes`                                 | hostname as it will appear in centreon                                            |
| `host_ip`                         | `yes`                                 | host ip. Should work with fqdn                                                        |
| `poller`                           | `yes`                                  | Poller to associate and reload in case of change                           |
| `reload_conf`                 | `yes`                                  | `boolean` Yes or No to reload after a change                                |
| `host_templates`           | `yes`                                  | `list` Host Templates to set AND apply. Services will be created  |
| `hostgroups`                  | `no`                                   | `list` Hostgroups to associate                                                          |
| `username`                    | `yes`                                  | Username with appropriates rights (api access and ACLs)            | 
| `password`                     | `yes`                                  | Associated password. Should be vaulted                                       |

This role let you create a host if it does not exist or ensure it doesn't.
You cannot change existing hostgroups with this task, you need to delete the host with the `absent` setting and recreate it.
Your changes wont be applied until `reload_conf` is set to `yes`, make sure the proper poller is reloaded. Reload will run ONLY is there is a change.
There no option to update host macros yet.

### Example of use

```yaml
- hosts: all
  connection: local
  tasks:
    - name: Create host smtp.adm
      centreon_host:
        state: present
        name: smtp.adm
        poller: Central
        host_ip: 10.69.0.75
        username: admin
        hostgroups:
          - All
          - All-System
        host_templates:
          - Generic
          - Generic-Linux
          - Generic-Linux-SMTP
        password: "{{ admin_centreon_pass }}"
        reload_conf: yes
```
The `connection: local` is important as the api calls are initiated by the host running the playbook.

## Centreon service

| Variable                          | Mandatory                         | Comments                                                                                        |
| :---                                   | :---                                      | :---                                                                                                     |
| `state`                            | `yes`                                 | `present` `absent` or `setmacros`                                                 |
| `name`                           | `yes`                                 | service name as it will appear in centreon  (name & description) |
| `host`                             | `yes`                                 | host associated with the service                                                     |
| `poller`                           | `yes`                                  | Poller to associate and reload in case of change                           |
| `reload_conf`                 | `yes`                                  | `boolean` Yes or No to reload after a change                                |
| `service_template`        | `yes`                                  |  Service Template to set AND apply.                                               |
| `macros`                        | `no`                                   | `list` Macros to set. Unspecified macros will be deleted, format `macroname;macrovalue`     |

This role let you create, delete a service or update its macros.
Your changes wont be applied until `reload_conf` is set to `yes`, make sure the proper poller is reloaded. Reload will run ONLY is there is a change, or if the `setmacros` state is selected.

```yaml
- hosts: all
  connection: local
  tasks:
    - name: Create service Memory for host smtp.adm
      centreon_service:
        state: present
        host: smtp.adm
        name: Memory
        poller: Central
        service_template: NRPE-Linux-Memory
        macros:
          - CRITICAL;80
          - WARNING;70
        username: admin
        password: "{{ admin_centreon_pass }}"
        reload_conf: no
```

## Toto

### Centreon Host
- [ ] Add hostgroup update
- [ ] Add macro update
- [ ] Add simple option settings

### Centreon Service
- [ ] Add servicegroup update
- [ ] Add simple option settings
- [ ] Change the `setmacros` from state option to its own boolean variable.