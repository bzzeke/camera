import os
import json
from pickledb import PickleDB

def load(location, auto_dump):
    return JDB(location, auto_dump, False)

class JDB(PickleDB):
    def dump(self):

        tmp_file = "{}.tmp".format(self.loco)
        json.dump(self.db, open(tmp_file, 'wt'))

        os.rename(tmp_file, self.loco)

        return True