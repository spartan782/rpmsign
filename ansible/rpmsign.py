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
    default = null
  key:
    description:
      - Name of the key that should be used for signing
    required: false
    default = null
  packages:
    description:
      - List of packages to sign using key
      required: True
  directory:
    description:
      - Full path to directory containing packages needing signed
      required: True
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
# Remove signature from packages
- rpmsign:
    directory:
      - /tmp/packages/
    packages:
      - package-version.rpm
    state:
      - absent
'''

try:
    import rpm
    HAS_RPM = True
except ImportError:
    HAS_RPM = False

from ansible.module_utiles.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            passphrase=dict(type='str', required=False, default=None),
            key=dict(type='str', required=False, default=None),
            packages=dict(type='list', required=True),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            directory=dict(type='str', required=True)
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
        if module.params['passphrase'] or module.params['key']:
            module.fail_json(rc=1, msg='Error: Both passphrase and key are required when signing an rpm')
        else:
            for package in module.params['packages']:
                rpm.addSign(
                    '{dir}/{package}'.format(
                        dir=module.params['directory'],
                        package=package
                    ), module.params['passphrase'], module.params['key']
                )
                # need to be able to hook the c code for the warning to test if actual change occurred
                results['changes'].append('{}'.format(package))
                results['results'].append('{} was signed'.format(package))
                if not results['changed']:
                    results['changed'] = True

                # need to be able to hook the c code to dectect the warning
                results['results'].append('{} skipped, already signed')
            module.exit_json(
                changed=results['changed'],
                results=results['results'],
                changes=dict(signed=results['changes'])
            )
    else:
        for package in module.params['packages']:
            rpm.delSign('{dir}/{package}'.format(dir=module.params['directory'], package=package))
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
