import json
import logging
logger = logging.getLogger(__name__)

from bs4 import BeautifulSoup
import requests

from DDR import config
from DDR import identifier


class IDServiceClient():
    """Client for interacting with ddr-idservice REST API
    
    >>> from DDR import identifier
    >>> from DDR import idservice
    >>> ic = idservice.IDServiceClient()
    >>> ic.login(username, password)
    200
    >>> ic.username
    'USERNAME'
    >>> ic.token
    u'8df7a4b117edcdc8ca1ae318a403bacfa3cf8133'
    >>> oidentifier = identifier.Identifier('ddr-test')
    >>> ic.next_id(oidentifier, 'collection')
    201,'ddr-test-123'
    >>> cidentifier = identifier.Identifier('ddr-test-123')
    >>> ic.next_id(cidentifier, 'entity')
    201,'ddr-test-123-1'
    >>> ic.next_id(cidentifier, 'entity')
    201,'ddr-test-123-1'
    """
    debug = False
    username = None
    token = None
    
    def _auth_headers(self):
        return {'Authorization': 'Token %s' % self.token}

    def login(self, username, password):
        """Initiate a session.
        
        @param username: str
        @param password: str
        @return: int,str (status_code,reason)
        """
        self.username = username
        logging.debug('idservice.IDServiceClient.login(%s)' % (self.username))
        r = requests.post(
            config.IDSERVICE_LOGIN_URL,
            data = {'username':username, 'password':password,},
        )
        self.token = r.json().get('key')
        return r.status_code,r.reason
    
    def resume(self, username, token):
        """Resume a session without logging in.
        
        @param username: str
        @param token: str
        """
        self.username = username
        self.token = token
    
    def logout(self):
        """End a session.
        
        @return: int,str (status_code,reason)
        """
        logging.debug('idservice.IDServiceClient.logout() %s' % (self.username))
        r = requests.post(
            config.IDSERVICE_LOGOUT_URL,
            headers=self._auth_headers(),
        )
        return r.status_code,r.reason
    
    def user_info(self):
        """Get user information (username, first/last name, email)
        
        @return: int,str,dict (status code, reason, userinfo dict)
        """
        r = requests.get(
            config.IDSERVICE_USERINFO_URL,
            headers=self._auth_headers(),
        )
        return r.status_code,r.reason,json.loads(r.content)
    
    def next_object_id(self, oidentifier, model):
        """Get the next object ID of the specified type
        
        @param oidentifier: identifier.Identifier
        @param model: str
        @return: int,str,str (status code, reason, object ID string)
        """
        logging.debug('idservice.IDServiceClient.next_object_id(%s, %s)' % (oidentifier, model))
        r = requests.post(
            config.IDSERVICE_NEXT_OBJECT_URL.format(objectid=oidentifier.id, model=model),
            headers=self._auth_headers(),
        )
        objectid = None
        if r.status_code == 201:
            objectid = r.json()['id']
            logging.debug(objectid)
        return r.status_code,r.reason,objectid
    
    def check_eids(self, cidentifier, entity_ids):
        """Given list of EIDs, indicates which are registered,unregistered.
        
        @param cidentifier: identifier.Identifier object
        @param entity_ids: list of Entity IDs!
        @returns: (status_code,reason,registered,unregistered)
        """
        logging.debug('idservice.IDServiceClient.check_eids(%s, %s entity_ids)' % (cidentifier, len(entity_ids)))
        r = requests.post(
            config.IDSERVICE_CHECKIDS_URL.format(objectid=cidentifier.id),
            headers=self._auth_headers(),
            data={'object_ids': entity_ids},
        )
        data = json.loads(r.text)
        #logging.debug(data)
        return r.status_code,r.reason,data['registered'],data['unregistered']
    
    def register_eids(self, cidentifier, entity_ids):
        """Register the specified entity IDs with the ID service
        
        @param cidentifier: identifier.Identifier object
        @param entity_ids: list of unregistered Entity IDs to add
        @returns: (status_code,reason,added_ids_list)
        """
        logging.debug('idservice.IDServiceClient.register_eids(%s, %s)' % (cidentifier, entity_ids))
        r = requests.post(
            config.IDSERVICE_REGISTERIDS_URL.format(objectid=cidentifier.id),
            headers=self._auth_headers(),
            data={'object_ids': entity_ids},
        )
        data = json.loads(r.text)
        logging.debug(data)
        return r.status_code,r.reason,data['created']
