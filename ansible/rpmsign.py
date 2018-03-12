#!/usr/bin/python

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
version_added: "0.0"
module: rpmsign
short_description: Sign rpm(s) given a pass phrase and key
description:
   - Sign rpm(s) given a pass phrase and key
options:
  passphrase:
    description:
      - Pass phrase to use with key
    required: false
    default: null
  key:
    description:
      - Name of the key that should be used for signing
    required: false
    default = null
  rpms:
    description:
      - List of full path rpms to sign using key
      required: True
  macros:
    description:
      - Dictionary of macros to define
      required: False
      default: null
  state:
    description:
      - Present adds a signature, absent will remove a signature
    required: false
    default: "present"

# informational: requirements for nodes
requirements:
    - rpm 
author: "Johnathon Hall"
'''

EXAMPLES = '''
# Sign packages
- rpmsign:
    directory:
      - /tmp/packages/
    packages:
      - package-version.rpm
    passphrase:
      - "secret"
    key:
      - "key name"
    marcos:
      _signature: gpg
      _gpg_name: gpg key name
      
# Remove signature from packages
- rpmsign:
    directory:
      - /tmp/packages/
    packages:
      - package-version.rpm
    state:
      - absent
'''
import os

try:
    import rpm
    HAS_RPM = True
except ImportError:
    HAS_RPM = False

from ansible.module_utiles.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            passphrase=dict(type='str', required=False, default=None, no_log=True),
            key=dict(type='str', required=False, default=None),
            rpms=dict(type='list', required=True),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            macros=dict(type='dict', required=False, default=None)
        ),
        supports_check_mode=True
    )

    if not HAS_RPM:
        module.fail_json(rc=1, msg='Error: python2 rpm module is needed for this ansible module')

    results = {
        "changed": False,
        "results": [],
        "changes": []
    }

    if module.params['state'] == "present":
        if not module.params['passphrase'] and not module.params['key']:
            module.fail_json(rc=1, msg='Error: Both passphrase and key are required when signing an rpm')
        else:
            if module.params['macros']:
                for macro, value in module.params['macros'].items():
                    rpm.addMacro(macro, value)
            for package in module.params['packages']:
                r, w = os.pipe()
                w = os.fdopen(w, 'w')
                rpm.setLogFile(w)
                result = rpm.addSign(
                    '{rpm}'.format(rpm=package),
                    module.params['passphrase'], module.params['key']
                )
                w.close()
                r = os.fdopen(r)
                msg = r.readline()
                r.close()
                
                if not result:
                    module.fail_json(rc=1, msg='Error: Failed to sign {rpm}'.format(package))
                
                if not msg:
                    results['changes'].append('{}'.format(package))
                    results['results'].append('{} was signed'.format(package))
                    if not results['changed']:
                        results['changed'] = True
                else:
                    results['results'].append('{} skipped, already signed'.format(package))
            module.exit_json(
                changed=results['changed'],
                results=results['results'],
                changes=dict(signed=results['changes'])
            )
    else:
        for package in module.params['rpms']:
            rpm.delSign('{rpm}'.format(rpm=package))
            results['changes'].append('{}'.format(package))
            results['results'].append('removed signature from {}'.format(package))
            if not results['changed']:
                results['changed'] = True
        module.exit_json(
            changed=results['changed'],
            results=results['results'],
            changes=dict(removed=results['changes'])
        )

if __name__ == "__main__":
    main()
