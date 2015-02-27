import json
import logging

from bs4 import BeautifulSoup
import requests

from DDR import WORKBENCH_URL
from DDR import WORKBENCH_USERINFO
from DDR import WORKBENCH_LOGIN_URL
from DDR import WORKBENCH_LOGOUT_URL
from DDR import WORKBENCH_LOGIN_TEST
from DDR import WORKBENCH_NEWCOL_URL
from DDR import WORKBENCH_NEWENT_URL
from DDR import WORKBENCH_REGISTER_EIDS_URL

MESSAGES = {
    'API_LOGIN_NOT_200': 'Error: status code {} on POST', # status code
    'API_LOGIN_INVALID_EMAIL': 'Your email is invalid! Please log in to workbench and enter a valid email!',
    'API_LOGIN_INVALID_NAME': 'Please log in to workbench and enter your first/last name(s).',
}


def session(sessionid, csrftoken):
    """Recreate an ID service session
    
    @param sessionid: str
    @param csrftoken: str
    @returns: requests.session object
    """
    s = requests.Session()
    s.cookies.set('sessionid', sessionid)
    s.cookies.set('csrftoken', csrftoken)
    return s

def _get_csrf_token(session, url):
    """Load page on ID service site, get CSRF token.
    
    @param session: requests.session object
    @param url: 
    @returns: string csrf_token
    """
    if session.cookies.get('csrftoken', None):
        return session.cookies.get('csrftoken')
    r = session.get(url)
    if not (r.status_code == 200):
        raise IOError('Could not get CSRF token (%s:%s on %s)' % (r.status_code, r.reason, url))
    for c in r.cookies:
        if c.name == 'csrftoken':
            return c.value
    raise IOError('No CSRF token in response (%s)' % (url))

def _needs_login(soup):
    """Returns True if page is a login page.
    
    @param soup: a BeautifulSoup object containing page HTML
    @returns: Boolean
    """
    title = None
    if soup.find('title'):
        title = soup.find('title').contents[0].lower()
    if title and ('log in' in title):
        return True
    return False

def login(username, password):
    """Logs in to the workbench server and get user info
    
    git_name and git_mail added as attributes of session object.
    
    @param username: str
    @param password: str
    @returns: requests.Session object
    """
    session = requests.Session()
    # load test page to see if already logged in
    r = session.get(WORKBENCH_LOGIN_TEST)
    soup = BeautifulSoup(r.text)
    titletag = soup.find('title')
    if (r.status_code == 200) and not ('Log in' in titletag.string):
        return session
    # get CSRF token from cookie
    csrf_token = r.cookies['csrftoken']
    # log in
    headers = {'X-CSRFToken': csrf_token}
    cookies = {'csrftoken': csrf_token}
    data = {'csrftoken': csrf_token,
            'username': username,
            'password': password,}
    r1 = session.post(WORKBENCH_LOGIN_URL,
                      headers=headers,
                      cookies=cookies,
                      data=data)
    if r1.status_code != 200:
        raise Exception('ID service login: return HTTP code %s' % r1.status_code)
    # it would be better to look for a success message...
    error_msg = 'Please enter a correct username and password.'
    if r1.text and (error_msg not in r1.text):
        # get user first/last name and email from workbench profile (via API)
        url = WORKBENCH_USERINFO
        r2 = session.get(url)
        logging.debug('r2.status_code %s' % r2.status_code)
        if r2.status_code == 200:
            data = json.loads(r2.text)
            email = data.get('email', None)
            if not email:
                raise Exception(MESSAGES['API_LOGIN_INVALID_EMAIL'])
            firstname = data.get('firstname', '')
            lastname = data.get('lastname', '')
            user_name = '{} {}'.format(firstname, lastname).strip()
            if email and (not user_name):
                user_name = email
                raise Exception(MESSAGES['API_LOGIN_INVALID_NAME'])
            session.git_name = user_name
            session.git_mail = email
            logging.debug('session.git_name %s' % session.git_name)
            logging.debug('session.git_mail %s' % session.git_mail)
        logging.debug('%s is logged in' % username)
        return session
    else:
        raise Exception('ID service login: bad username or password')
    raise Exception('ID service login: unspecified')

def logout():
    """Logs out of the workbench server.
    
    @returns string: 'ok' or error message
    """
    s = requests.Session()
    r = s.get(WORKBENCH_LOGOUT_URL)
    if r.status_code == 200:
        return 'ok'
    return 'error: unspecified'

def _objects_latest(session, url, args, num_objects=1):
    """Get the most recent N entity IDs for the logged-in user.
    
    <table id="collections" class="table table-striped table-bordered table-condensed">
      <tr><td><a class="collection" href="/workbench/kiroku/ddr-densho-1/">ddr-densho-1</a></td></tr>
      <tr><td><a class="collection" href="/workbench/kiroku/ddr-densho-2/">ddr-densho-2</a></td></tr>
    ...
    
    TODO Replace screenscraping with a real API
    
    @param session: requests.session object
    @param url: URL of page to scrape.
    @param args: tuple Tag and class that contains the IDs.
    @param num_objects: int N most recent IDs to get.
    @returns: list of IDs
    """
    objects = []
    r = session.get(url)
    soup = BeautifulSoup(r.text)
    if _needs_login(soup):
        raise Exception('Not logged in. Please try again.')
    ids = []
    for o in soup.find_all(args[0], args[1]):
        ids.append(o.string.strip())
    if num_objects:
        return ids[-num_objects:]
    else:
        return ids

def collections_latest(session, repo, org, num_objects=1):
    """Get the most recent N collection IDs for the logged-in user.
    
    <table id="collections" class="table table-striped table-bordered table-condensed">
      <tr><td><a class="collection" href="/workbench/kiroku/ddr-densho-1/">ddr-densho-1</a></td></tr>
      <tr><td><a class="collection" href="/workbench/kiroku/ddr-densho-2/">ddr-densho-2</a></td></tr>
    ...
    
    TODO Replace screenscraping with a real API
    
    @param session: requests.session object
    @param repo: str Repository keyword
    @param org: str Organization keyword
    @param num_objects: int N most recent IDs to get.
    @returns: list of IDs
    """
    url = '{}/kiroku/{}-{}/'.format(WORKBENCH_URL, repo, org)
    return _objects_latest(session, url, ('a','collection'), num_objects)

def entities_latest(session, repo, org, cid, num_objects=1):
    """Get the most recent N entity IDs for the logged-in user.
    
    <table id="collections" class="table table-striped table-bordered table-condensed">
      <tr><td><a class="collection" href="/workbench/kiroku/ddr-densho-1/">ddr-densho-1</a></td></tr>
      <tr><td><a class="collection" href="/workbench/kiroku/ddr-densho-2/">ddr-densho-2</a></td></tr>
    ...
    
    TODO Replace screenscraping with a real API
    
    @param session: requests.session object
    @param repo: str Repository keyword
    @param org: str Organization keyword
    @param cid: int/str Collection id
    @param num_objects: int N most recent IDs to get.
    @returns: list of IDs
    """
    url = '{}/kiroku/{}-{}-{}/'.format(WORKBENCH_URL, repo, org, cid)
    return _objects_latest(session, url, ('td','eid'), num_objects)

def _objects_next(model, session, new_ids_url, csrf_token_url, tag_class, num_ids=1 ):
    """Generate the next N object IDs.
    
    TODO We're screenscraping when we should be using the API.
    
    @param model: 'collection' or 'entity'
    @param session: requests.session.Session object
    @param new_ids_url: WORKBENCH_NEWCOL_URL
    @param csrf_token_url: url
    @param tag_class: tuple Tag and class containing IDs
    @param num_ids: int The number of new IDs requested.
    @returns: list of IDs or debugging info.
    """
    csrf_token = _get_csrf_token(session, csrf_token_url)
    post_data={
        'csrftoken': csrf_token,
    }
    if model == 'entity':
        post_data['num'] = num_ids
    r = session.post(
        new_ids_url,
        headers={'X-CSRFToken': csrf_token},
        cookies={'csrftoken': csrf_token},
        data=post_data
    )
    if not (r.status_code == 200):
        raise IOError('Could not get new ID(s) (%s:%s on %s)' % (
            r.status_code, r.reason, url))
    return _objects_next_process(new_ids_url, r.text, tag_class, num_ids)

def _objects_next_process(new_ids_url, text, find, num_ids):
    """Extract IDs from page retrieved by _objects_next.
    
    @param new_ids_url: WORKBENCH_NEWCOL_URL
    @param text: HTML
    @param find: tuple Tag and class containing IDs
    @param num_ids: int The number of new IDs requested.
    """
    soup = BeautifulSoup(text)
    if _needs_login(soup):
        raise Exception('Could not get IDs. Please log out and try again.')
    ids = [x.string.strip() for x in soup.find_all(find[0], find[1])]
    if not ids:
        raise Exception('Could not get IDs (not found in page %s)' % new_ids_url)
    object_ids = ids[-num_ids:]
    return object_ids

def collections_next(session, repo, org, num_ids=1):
    """Generate the next N collection IDs for the logged-in user.
    
    @param session: requests.session object
    @param repo: str Repository keyword
    @param org: str Organization keyword
    @param num_ids: int The number of new IDs requested.
    @returns: list of collection_ids or debugging info.
    """
    new_ids_url = WORKBENCH_NEWCOL_URL.replace('REPO',repo).replace('ORG',org)
    csrf_token_url = '{}/kiroku/{}-{}/'.format(WORKBENCH_URL, repo, org)
    tag_class = ['a', 'collection']
    return _objects_next(
        'collection', session, new_ids_url, csrf_token_url, tag_class, num_ids)

def entities_next(session, repo, org, cid, num_ids=1):
    """Generate the next N entity IDs for the logged-in user.
    
    @param session: requests.session object
    @param repo: str Repository keyword
    @param org: str Organization keyword
    @param cid: str Collection ID
    @param num_ids: int The number of new IDs requested.
    @returns: list of entity_ids or debugging info.
    """
    new_ids_url = WORKBENCH_NEWENT_URL.replace('REPO',repo).replace('ORG',org).replace('CID',unicode(cid))
    csrf_token_url = '{}/kiroku/{}-{}/'.format(WORKBENCH_URL, repo, org)
    tag_class = ['td', 'eid']
    return _objects_next(
        'entity', session, new_ids_url, csrf_token_url, tag_class, num_ids)

def register_entity_ids(session, entities):
    """Register the specified entity IDs with the ID service
    
    TODO Replace screenscraping with a real API
    
    @param session: requests.session object
    @param entities: list of Entity objects - all will be added!
    @returns: list of IDs added
    """
    collection_id = entities[0].parent_uid
    entity_ids = '\n'.join([entity.id for entity in entities])
    csrf_token_url = '{}/kiroku/{}/'.format(WORKBENCH_URL, collection_id)
    csrf_token = _get_csrf_token(session, csrf_token_url)
    register_eids_url = WORKBENCH_REGISTER_EIDS_URL.replace('REPO-ORG-CID', collection_id)
    r = session.post(
        register_eids_url,
        headers={'X-CSRFToken': csrf_token},
        cookies={'csrftoken': csrf_token},
        data={
            'csrftoken': csrf_token,
            'entity_ids': entity_ids,
        },
    )
    if not (r.status_code == 200):
        raise IOError('Could not get new object ID(s) (%s:%s on %s)' % (
            r.status_code, r.reason, register_eids_url))
    return entity_ids
