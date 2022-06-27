def get_users():
    import tellet
    import os.path as op
    import json
    j = op.join(op.dirname(op.dirname(tellet.__file__)), 'web', 'data', 'users.json')
    users = json.load(open(j))
    return users
