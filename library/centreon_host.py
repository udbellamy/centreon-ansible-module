#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Module ansible pour création des hosts centreon."""

import json
import sys

from ansible.module_utils.basic import AnsibleModule

import requests

# On commence par déclarer les options que l'on veut passer au module ansible
fields = {
    "state": {"required": True, "type": "str"},
    "name": {"required": True, "type": "str"},
    "username": {"required": True, "type": "str"},
    "password": {"required": True, "type": "str"},
    "host_ip": {"required": True, "type": "str"},
    "poller": {"required": True, "type": "str"},
    "reload_conf": {"required": True, "type": "bool"},
    "host_templates": {"required": True, "type": "list"},
    "hostgroups": {"required": False, "type": "list"},
}

module = AnsibleModule(argument_spec=fields)

# On récupère les valeurs de chaque option
state = module.params['state']
name = module.params['name']
username = module.params['username']
password = module.params['password']
host_ip = module.params['host_ip']
poller = module.params['poller']
host_templates = module.params['host_templates']
hostgroups = module.params['hostgroups']
reload_conf = module.params['reload_conf']


# On set body à rien et on convertit les listes host template et hostgroups au bon format
body = ""
host_templates = "|".join(host_templates)
if hostgroups:
    hostgroups = "|".join(hostgroups)
if not hostgroups:
    hostgroups = ""


def generate_token(body, username, password):
    """On génère le token."""
    target = "http://CHANGEME/centreon/api/index.php?action=authenticate"
    body = {
        'username': "%s" % (username),
        'password': "%s" % (password)
    }
    r_token = requests.post(target, data=body)
    return json.loads(r_token.text)
    return None

# On entre dans la boucle si l'état demandé est present
if state == "present":
    # La target est hardcodée pour éviter de rajouter une variable qui n'a pas vocation à changer
    # Cette dernière ne peut être récupérée depuis l'inventaire
    target = "http://CHANGEME/centreon/api/index.php?action=action&object=centreon_clapi"
    # On génère le token, les headers et le body pour ajouter le host
    token_gen = generate_token(body, username, password)
    token = (token_gen['authToken']).encode('utf-8')
    headers = {
        'centreon-auth-token': '%s' % (token)
    }
    body = '{"action": "add", "object": "host", "values": "%s;%s;%s;%s;%s;%s"}' % (
        name, name, host_ip, host_templates, poller, hostgroups)
    # On lance la commande pour créer le host
    try:
        r = requests.post(target, headers=headers, data=body)
        # On dump la réponse au format json et on la store dans out
        out = json.loads(r.text)
        if "already" in out:
            # Si le message already apparaît dans out, cela signifie que le host existe déjà. On renvoit un change false
            print json.dumps({
                "changed": False,
                "action": "Host already exist"
            })
            sys.exit(0)

        elif not out["result"]:
            # Si la réponse contient une clé result vide, le host a été créé. On applique les templates.
            body = '{"action": "applytpl", "object": "host", "values" : "%s"}' % name
            requests.post(target, headers=headers, data=body)
            # Si nous avons spécifié une demande de reload de poller, on exécute les étapes
            if reload_conf:
                body = '{"action": "pollergenerate", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
                body = '{"action": "pollertest", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
                body = '{"action": "cfgmove", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
                body = '{"action": "pollerreload", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
            # On renvoit un changed true
            print json.dumps({
                "changed": True,
                "action": "Host created"
            })
            sys.exit(0)

    except KeyError:
        # En cas d'erreur
        print json.dumps({
            "failed": True,
            "msg": "Unexpected failure"
        })
        sys.exit(1)

# On entre dans la boucle si l'état demandé est absent
if state == "absent":
    # La target est hardcodée pour éviter de rajouter une variable qui n'a pas vocation à changer
    # Cette dernière ne peut être récupérée depuis l'inventaire
    target = "http://CHANGEME/centreon/api/index.php?action=action&object=centreon_clapi"
    # On génère le token, les headers et le body pour supprimer le host
    token_gen = generate_token(body, username, password)
    token = (token_gen['authToken']).encode('utf-8')
    headers = {
        'centreon-auth-token': '%s' % (token)
    }
    body = '{"action": "del", "object": "host", "values": "%s"}' % (
        name)
    # On lance la commande pour supprimer le host
    try:
        r = requests.post(target, headers=headers, data=body)
        # On dump la réponse au format json et on la store dans out
        out = json.loads(r.text)
        if "not found" in out:
            # Si le message not found apparaît dans out, cela signifie que le host est déjà supprimé.
            # On renvoit un change false
            print json.dumps({
                "changed": False,
                "action": "Host already absent | %s" % out
            })
            sys.exit(0)

        elif not out["result"]:
            # Si nous avons spécifié une demande de reload de poller, on exécute les étapes
            if reload_conf:
                body = '{"action": "pollergenerate", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
                body = '{"action": "pollertest", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
                body = '{"action": "cfgmove", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
                body = '{"action": "pollerreload", "values": "%s"}' % poller
                requests.post(target, headers=headers, data=body)
            # On renvoit un changed true
            print json.dumps({
                "changed": True,
                "action": "Host deleted" % out
            })
            sys.exit(0)

    except KeyError:
        # En cas d'erreur
        print json.dumps({
            "failed": True,
            "msg": "Unexpected failure"
        })
        sys.exit(1)
