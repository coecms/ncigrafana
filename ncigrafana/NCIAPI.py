import pymunge
from typing import Dict

def prep_auth_header() -> Dict[str,str]:

    ### Derived from nci-files-report client (auth.py)
    return {'Authorization':f'Munge {pymunge.encode().decode("ascii")}'}