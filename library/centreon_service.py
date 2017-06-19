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
    "host": {"required": True, "type": "str"},
    "poller": {"required": True, "type": "str"},
    "reload_conf": {"required": True, "type": "bool"},
    "macros": {"required": False, "type": "list"},
    "service_template": {"required": True, "type": "str"}
}

module = AnsibleModule(argument_spec=fields)

# On récupère les valeurs de chaque option
state = module.params['state']
name = module.params['name']
username = module.params['username']
password = module.params['password']
host = module.params['host']
poller = module.params['poller']
service_template = module.params['service_template']
reload_conf = module.params['reload_conf']
macros = module.params['macros']


# On set body à rien
body = ""


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
    # On génère le token, les headers et le body pour ajouter le service
    token_gen = generate_token(body, username, password)
    token = (token_gen['authToken']).encode('utf-8')
    headers = {
        'centreon-auth-token': '%s' % (token)
    }
    body = '{"action": "add", "object": "service", "values": "%s;%s;%s"}' % (
        host, name, service_template)
    # On lance la commande pour créer le service
    try:
        r = requests.post(target, headers=headers, data=body)
        # On dump la réponse au format json et on la store dans out
        out = json.loads(r.text)
        if "already" in out:
            # Si le message already apparaît dans out, cela signifie que le service existe déjà.
            # On renvoit un change false
            print json.dumps({
                "changed": False,
                "action": "Service already exist"
            })
            sys.exit(0)

        elif not out["result"]:
            # Si la réponse contient une clé result vide, le service a été créé. On définit les macros.
            if macros:
                for macro in macros:
                    body = '{"action": "setmacro", "object": "service", "values" : "%s;%s;%s;0;"}' % (
                        host, name, macro)
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
                "action": "Service created"
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
    # On génère le token, les headers et le body pour supprimer le service
    token_gen = generate_token(body, username, password)
    token = (token_gen['authToken']).encode('utf-8')
    headers = {
        'centreon-auth-token': '%s' % (token)
    }
    body = '{"action": "del", "object": "service", "values": "%s;%s"}' % (
        host, name)
    # On lance la commande pour supprimer le service
    try:
        r = requests.post(target, headers=headers, data=body)
        # On dump la réponse au format json et on la store dans out
        out = json.loads(r.text)
        if "not found" in out:
            # Si le message not found apparaît dans out, cela signifie que le service est déjà supprimmé.
            # On renvoit un change false
            print json.dumps({
                "changed": False,
                "action": "Service already absent | %s" % out
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
                "action": "Service deleted" % out
            })
            sys.exit(0)

    except KeyError:
        # En cas d'erreur
        print json.dumps({
            "failed": True,
            "msg": "Unexpected failure"
        })
        sys.exit(1)

# On entre dans la boucle si l'état demandé est setmacros
if state == "setmacros":
    # La target est hardcodée pour éviter de rajouter une variable qui n'a pas vocation à changer
    # Cette dernière ne peut être récupérée depuis l'inventaire
    target = "http://CHANGEME/centreon/api/index.php?action=action&object=centreon_clapi"
    # On génère le token, les headers et le body pour modifier les macros
    token_gen = generate_token(body, username, password)
    token = (token_gen['authToken']).encode('utf-8')
    headers = {
        'centreon-auth-token': '%s' % (token)
    }
    # On définit le body pour récupérer les macros existantes
    body = '{"action": "getmacro", "object": "service", "values": "%s;%s"}' % (
        host, name)
    # On lance la commande pour supprimer toutes les macros
    try:
        r = requests.post(target, headers=headers, data=body)
        out = json.loads(r.text)["result"]
        for macro in out:
            body = '{"action": "delmacro", "object": "service", "values" : "%s;%s;%s"}' % (
                host, name, macro["macro name"])
            r = requests.post(target, headers=headers, data=body)
    except KeyError:
        # En cas d'erreur
        print json.dumps({
            "failed": True,
            "msg": "Unexpected failure"
        })
        sys.exit(1)
    # On lance la commande pour setter les macros si elles ont été définies
    try:
        if macros:
            for macro in macros:
                body = '{"action": "setmacro", "object": "service", "values" : "%s;%s;%s;0;"}' % (
                    host, name, macro)
                r = requests.post(target, headers=headers, data=body)
                # On dump la réponse au format json et on la store dans out
                out = json.loads(r.text)
        # On renvoit un changed true (systématique car le flush des macros n'est pas conditionnel)
        print json.dumps({
            "changed": True,
            "action": "Macros updated" % out
        })
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
        sys.exit(0)
        # Il n'y a pas de changed false car l'api répond la même chose si la macro est
        # existante. Dans tous les cas on flush les macros au préalable.

    except KeyError:
        # En cas d'erreur
        print json.dumps({
            "failed": True,
            "msg": "Unexpected failure"
        })
        sys.exit(1)
