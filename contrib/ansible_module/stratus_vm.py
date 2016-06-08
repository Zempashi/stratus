#!/usr/bin/python
import sys
import time
import operator

try:
    import argparse
    HAS_ARGPARSE = True
except ImportError:
    HAS_ARGPARSE = False

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

USER_AGENT = "ansible-stratus-vm/0.0.1"

# some code of the six module
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


def _add_doc(func, doc):
    """Add documentation to a function."""
    func.__doc__ = doc

if PY3:
    def iterkeys(d, **kw):
        return iter(d.keys(**kw))

    def itervalues(d, **kw):
        return iter(d.values(**kw))

    def iteritems(d, **kw):
        return iter(d.items(**kw))

    viewkeys = operator.methodcaller("keys")
    viewvalues = operator.methodcaller("values")
    viewitems = operator.methodcaller("items")
else:
    def iterkeys(d, **kw):
        return d.iterkeys(**kw)

    def itervalues(d, **kw):
        return d.itervalues(**kw)

    def iteritems(d, **kw):
        return d.iteritems(**kw)

    viewkeys = operator.methodcaller("viewkeys")
    viewvalues = operator.methodcaller("viewvalues")
    viewitems = operator.methodcaller("viewitems")

_add_doc(iterkeys, "Return an iterator over the keys of a dictionary.")
_add_doc(itervalues, "Return an iterator over the values of a dictionary.")
_add_doc(iteritems,
         "Return an iterator over the (key, value) pairs of a dictionary.")


class StratusVMAnsible(object):

    def __init__(self, dry_run, module):
        self.dry_run = dry_run
        self.module = module

    def execute(self, http_agent, vm_list, api_endpoint, state, **kwargs):
        self.api_root = self.normalize_url(api_endpoint)
        vm_dict = create_vm_dict(vm_list)
        self.find_api_root()
        vm_found = self.existing_vm(vm_dict)
        vm_processed = self.action_vm()
        changed = bool(vm_processed)

    def create_vm_dict(self, vm_list):
        parser = argparse.ArgumentParser()
        parser.add_argument('-n', dest='name')
        vm_dict = {}
        for vm_input in vm_list:
            vm = vm_input.strip()
            if vm == vm.split()[0]:  # Not a command, only a name
                vm_dict[vm] = None   # It's ok if you delete VM
            else:
                args, _ = parser.parse_known_args(vm.split())
                if args.name is None:
                    raise StratusVMAnsibleError('Malformed VM (without name)')
                else:
                    vm_dict[args.name] = vm
        return vm_dict

    def existing_vm(self, vm_dict):
        vm_found = dict()
        # vms_endpoint = urlparse.join(self.api_root, 'vms')
        for vm_name in vm_dict.iterkeys():
            vm_url = urlparse.join(self.api_root, 'vms', vm_name)
            resp, status = fetch_url(self.module, vm_url)
            if status['status'] == 200:
                try:
                    found_vm[vm] = json.loads(resp.read())
                except ValueError:
                    continue
        return vm_found

    def action_vm(self, vm_dict, vm_found, state):
        vm_processed = dict()
        if state == 'absent':
            vm_action = viewkeys(vm_dict) & viewkeys(vm_found)

            def action(vm): self.delete_vm(vm)
        elif state == 'present':
            vm_action = viewkeys(vm_dict) - viewkeys(vm_found)

            def action(vm): self.create_vm(vm_dict[vm])
        for vm in vm_action:
            vm_processed[vm] = action(vm) or vm_found[vm]
        return vm_processed

    def delete_vm(vm_id=None, vm_name=None):
        if not vm_id and not vm_name:
            raise ValueError('Please provide a \'vm_id\' or \'vm_name\'')
        vm_url = urlparse.join(self.api_root, 'vms', vm_id or vm_name)
        resp, status = fetch_url(self.module, vm_url, method='DELETE')
        if status['status'] not in [200, 204]:
            raise ValueError('Error deleting VM \'%s\'' % (vm_id or vm_name))

    def create_vm(vm_spec):
        if vm_spec is not None:
            vm_data = json.dumps(dict(args=vm_spec))
        else:
            raise StratusVMAnsibleError('You need to provide complete'
                                        'install line for creating vm')
        post_vm_url = urlparse.join(self.api_root, 'vms')
        resp, status = fetch_url(self.module, post_vm_url, data=vm_data)
        if status['status'] in [200, 204]:
            try:
                return json.loads(resp.read())
            except ValueError:
                pass
        raise ValueError('Error creating VM \'%s\'' % (vm_id or vm_name))

    def poll_result(vm_processed, state):
        max_error = 10
        if state == 'absent':
            target_status = ['DELETED']
        elif state == 'present':
            target_status = ['STARTED', 'STOPPED']
        while max_error > 0:
            i = -1
            for i, (vm_name, vm_info) in enumerate(viewitems(vm_processed)):
                vm_url = urlparse.join(self.api_root, 'vms', vm_info['id'])
                resp, status = fetch_url(self.module, api_root)
                if status['status'] == 200:
                    try:
                        j = json.loads(resp)
                    except ValueError:
                        max_error -= 1
                        continue
                    else:
                        if j['status'] in target_status:
                            vm_processed.pop(vm_name)
            if i < 0:
                break
            else:
                time.sleep(5)
        if vm_processed:  # Due to error, there is some VM left
            raise ValueError

    @staticmethod
    def normalize_url(url):
        url_parts = urlparse.urlparse(url)
        if not url_parts.netloc:
            url = 'http://{}'.format(url)
            url_parts = urlparse.urlparse(url)
        if not url_parts.path:
            url = '{}/'.format(url)
        return url

    def find_api_root(self):
        api_list = [lambda: self.api_root,
                    lambda: urlparse.join(self.api_root, 'v1')]
        insert_count = 10  # Prevent infinite redirection loop
        for i, api in enumerate(api_list):
            api_root = api()
            resp, status = fetch_url(self.module, api_root)
            try:
                j = json.loads(r.read())
            except ValueError:
                continue
            else:
                if j.hasattr('vms') and j.hasattr('hkvms') and\
                        status['status'] == 200:
                    break
                else:
                    try:
                        new_root = j['api_root']
                        insert_count -= 1
                        # We have possibly found an indication were api_root is
                        # Insert it in next position in the list of possibility
                        if insert_count > 0:
                            api_list.insert(i, lambda: new_root)
                    except KeyError:
                        continue
        else:
            raise ValueError('Cannot found correct Api Root')
        self.api_root = api_root


class StratusVMAnsibleError(Exception):

    def __init__(self, msg):
        self.msg = msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            http_agent=dict(default=USER_AGENT),
            vm_list=dict(required=False, default=[], type='list'),
            # force_basic_auth=dict(default=True),
            api_endpoint=dict(default='localhost'),
            state=dict(default='present', choices=['absent', 'present',
                                                   'started', 'stopped']),
        ),
        supports_check_mode=True,
    )
    m = StratusVMAnsible(dry_run=bool(module.check_mode), module=module)
    if not HAS_ARGPARSE:
        module.fail_json(msg="Please install argparse")
    try:
        res_dict = m.execute(**module.params)
    except StratusVMAnsibleError, exc:
        module.fail_json(msg=exc.msg)
    except Exception:
        import traceback
        module.fail_json(msg=traceback.format_exc().splitlines())
    else:
        module.exit_json(**res_dict)

from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
