#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018, Milan Ilic <milani@nordeus.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: one_image
short_description: Manages OpenNebula images
description:
  - Manages OpenNebula images
requirements:
  - pyone
extends_documentation_fragment:
  - community.general.attributes
attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
options:
  api_url:
    description:
      - URL of the OpenNebula RPC server.
      - It is recommended to use HTTPS so that the username/password are not
      - transferred over the network unencrypted.
      - If not set then the value of the E(ONE_URL) environment variable is used.
    type: str
  api_username:
    description:
      - Name of the user to login into the OpenNebula RPC server. If not set
      - then the value of the E(ONE_USERNAME) environment variable is used.
    type: str
  api_password:
    description:
      - Password of the user to login into OpenNebula RPC server. If not set
      - then the value of the E(ONE_PASSWORD) environment variable is used.
    type: str
  id:
    description:
      - A O(id) of the image you would like to manage.
    type: int
  name:
    description:
      - A O(name) of the image you would like to manage.
    type: str
  state:
    description:
      - V(present) - state that is used to manage the image
      - V(absent) - delete the image
      - V(cloned) - clone the image
      - V(renamed) - rename the image to the O(new_name)
    choices: ["present", "absent", "cloned", "renamed"]
    default: present
    type: str
  enabled:
    description:
      - Whether the image should be enabled or disabled.
    type: bool
  new_name:
    description:
      - A name that will be assigned to the existing or new image.
      - In the case of cloning, by default O(new_name) will take the name of the origin image with the prefix 'Copy of'.
    type: str
author:
    - "Milan Ilic (@ilicmilan)"
'''

EXAMPLES = '''
- name: Fetch the IMAGE by id
  community.general.one_image:
    id: 45
  register: result

- name: Print the IMAGE properties
  ansible.builtin.debug:
    var: result

- name: Rename existing IMAGE
  community.general.one_image:
    id: 34
    state: renamed
    new_name: bar-image

- name: Disable the IMAGE by id
  community.general.one_image:
    id: 37
    enabled: false

- name: Enable the IMAGE by name
  community.general.one_image:
    name: bar-image
    enabled: true

- name: Clone the IMAGE by name
  community.general.one_image:
    name: bar-image
    state: cloned
    new_name: bar-image-clone
  register: result

- name: Delete the IMAGE by id
  community.general.one_image:
    id: '{{ result.id }}'
    state: absent
'''

RETURN = '''
id:
    description: image id
    type: int
    returned: success
    sample: 153
name:
    description: image name
    type: str
    returned: success
    sample: app1
group_id:
    description: image's group id
    type: int
    returned: success
    sample: 1
group_name:
    description: image's group name
    type: str
    returned: success
    sample: one-users
owner_id:
    description: image's owner id
    type: int
    returned: success
    sample: 143
owner_name:
    description: image's owner name
    type: str
    returned: success
    sample: ansible-test
state:
    description: state of image instance
    type: str
    returned: success
    sample: READY
used:
    description: is image in use
    type: bool
    returned: success
    sample: true
running_vms:
    description: count of running vms that use this image
    type: int
    returned: success
    sample: 7
'''

try:
    import pyone
    HAS_PYONE = True
except ImportError:
    HAS_PYONE = False

from ansible.module_utils.basic import AnsibleModule
import os


def get_image(module, client, predicate):
    # Filter -2 means fetch all images user can Use
    pool = client.imagepool.info(-2, -1, -1, -1)

    for image in pool.IMAGE:
        if predicate(image):
            return image

    return None


def get_image_by_name(module, client, image_name):
    return get_image(module, client, lambda image: (image.NAME == image_name))


def get_image_by_id(module, client, image_id):
    return get_image(module, client, lambda image: (image.ID == image_id))


def get_image_instance(module, client, requested_id, requested_name):
    if requested_id:
        return get_image_by_id(module, client, requested_id)
    else:
        return get_image_by_name(module, client, requested_name)


IMAGE_STATES = ['INIT', 'READY', 'USED', 'DISABLED', 'LOCKED', 'ERROR', 'CLONE', 'DELETE', 'USED_PERS', 'LOCKED_USED', 'LOCKED_USED_PERS']


def get_image_info(image):
    info = {
        'id': image.ID,
        'name': image.NAME,
        'state': IMAGE_STATES[image.STATE],
        'running_vms': image.RUNNING_VMS,
        'used': bool(image.RUNNING_VMS),
        'user_name': image.UNAME,
        'user_id': image.UID,
        'group_name': image.GNAME,
        'group_id': image.GID,
    }

    return info


def wait_for_state(module, client, image_id, wait_timeout, state_predicate):
    import time
    start_time = time.time()

    while (time.time() - start_time) < wait_timeout:
        image = client.image.info(image_id)
        state = image.STATE

        if state_predicate(state):
            return image

        time.sleep(1)

    module.fail_json(msg="Wait timeout has expired!")


def wait_for_ready(module, client, image_id, wait_timeout=60):
    return wait_for_state(module, client, image_id, wait_timeout, lambda state: (state in [IMAGE_STATES.index('READY')]))


def wait_for_delete(module, client, image_id, wait_timeout=60):
    return wait_for_state(module, client, image_id, wait_timeout, lambda state: (state in [IMAGE_STATES.index('DELETE')]))


def enable_image(module, client, image, enable):
    image = client.image.info(image.ID)
    changed = False

    state = image.STATE

    if state not in [IMAGE_STATES.index('READY'), IMAGE_STATES.index('DISABLED'), IMAGE_STATES.index('ERROR')]:
        if enable:
            module.fail_json(msg="Cannot enable " + IMAGE_STATES[state] + " image!")
        else:
            module.fail_json(msg="Cannot disable " + IMAGE_STATES[state] + " image!")

    if ((enable and state != IMAGE_STATES.index('READY')) or
       (not enable and state != IMAGE_STATES.index('DISABLED'))):
        changed = True

    if changed and not module.check_mode:
        client.image.enable(image.ID, enable)

    result = get_image_info(image)
    result['changed'] = changed

    return result


def clone_image(module, client, image, new_name):
    if new_name is None:
        new_name = "Copy of " + image.NAME

    tmp_image = get_image_by_name(module, client, new_name)
    if tmp_image:
        result = get_image_info(tmp_image)
        result['changed'] = False
        return result

    if image.STATE == IMAGE_STATES.index('DISABLED'):
        module.fail_json(msg="Cannot clone DISABLED image")

    if not module.check_mode:
        new_id = client.image.clone(image.ID, new_name)
        wait_for_ready(module, client, new_id)
        image = client.image.info(new_id)

    result = get_image_info(image)
    result['changed'] = True

    return result


def rename_image(module, client, image, new_name):
    if new_name is None:
        module.fail_json(msg="'new_name' option has to be specified when the state is 'renamed'")

    if new_name == image.NAME:
        result = get_image_info(image)
        result['changed'] = False
        return result

    tmp_image = get_image_by_name(module, client, new_name)
    if tmp_image:
        module.fail_json(msg="Name '" + new_name + "' is already taken by IMAGE with id=" + str(tmp_image.ID))

    if not module.check_mode:
        client.image.rename(image.ID, new_name)

    result = get_image_info(image)
    result['changed'] = True
    return result


def delete_image(module, client, image):

    if not image:
        return {'changed': False}

    if image.RUNNING_VMS > 0:
        module.fail_json(msg="Cannot delete image. There are " + str(image.RUNNING_VMS) + " VMs using it.")

    if not module.check_mode:
        client.image.delete(image.ID)
        wait_for_delete(module, client, image.ID)

    return {'changed': True}


def get_connection_info(module):

    url = module.params.get('api_url')
    username = module.params.get('api_username')
    password = module.params.get('api_password')

    if not url:
        url = os.environ.get('ONE_URL')

    if not username:
        username = os.environ.get('ONE_USERNAME')

    if not password:
        password = os.environ.get('ONE_PASSWORD')

    if not (url and username and password):
        module.fail_json(msg="One or more connection parameters (api_url, api_username, api_password) were not specified")
    from collections import namedtuple

    auth_params = namedtuple('auth', ('url', 'username', 'password'))

    return auth_params(url=url, username=username, password=password)


def main():
    fields = {
        "api_url": {"required": False, "type": "str"},
        "api_username": {"required": False, "type": "str"},
        "api_password": {"required": False, "type": "str", "no_log": True},
        "id": {"required": False, "type": "int"},
        "name": {"required": False, "type": "str"},
        "state": {
            "default": "present",
            "choices": ['present', 'absent', 'cloned', 'renamed'],
            "type": "str"
        },
        "enabled": {"required": False, "type": "bool"},
        "new_name": {"required": False, "type": "str"},
    }

    module = AnsibleModule(argument_spec=fields,
                           mutually_exclusive=[['id', 'name']],
                           supports_check_mode=True)

    if not HAS_PYONE:
        module.fail_json(msg='This module requires pyone to work!')

    auth = get_connection_info(module)
    params = module.params
    id = params.get('id')
    name = params.get('name')
    state = params.get('state')
    enabled = params.get('enabled')
    new_name = params.get('new_name')
    client = pyone.OneServer(auth.url, session=auth.username + ':' + auth.password)

    result = {}

    if not id and state == 'renamed':
        module.fail_json(msg="Option 'id' is required when the state is 'renamed'")

    image = get_image_instance(module, client, id, name)
    if not image and state != 'absent':
        if id:
            module.fail_json(msg="There is no image with id=" + str(id))
        else:
            module.fail_json(msg="There is no image with name=" + name)

    if state == 'absent':
        result = delete_image(module, client, image)
    else:
        result = get_image_info(image)
        changed = False
        result['changed'] = False

        if enabled is not None:
            result = enable_image(module, client, image, enabled)
        if state == "cloned":
            result = clone_image(module, client, image, new_name)
        elif state == "renamed":
            result = rename_image(module, client, image, new_name)

        changed = changed or result['changed']
        result['changed'] = changed

    module.exit_json(**result)


if __name__ == '__main__':
    main()
