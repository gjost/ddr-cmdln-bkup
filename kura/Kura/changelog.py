from datetime import datetime
import logging
import os


MODULE_PATH   = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(MODULE_PATH, 'templates')
CHANGELOG_TEMPLATE    = os.path.join(TEMPLATE_PATH, 'changelog.tpl')
CHANGELOG_DATE_FORMAT = os.path.join(TEMPLATE_PATH, 'changelog-date.tpl')


def load_template(filename):
    template = ''
    with open(filename, 'r') as f:
        template = f.read()
    return template

def write_changelog_entry(path, messages, user, email):
    logging.debug('    write_changelog_entry({})'.format(path))
    template = load_template(CHANGELOG_TEMPLATE)
    date_format = load_template(CHANGELOG_DATE_FORMAT)
    # one line per message
    lines = []
    [lines.append('* {}'.format(m)) for m in messages]
    changes = '\n'.join(lines)
    # render
    entry = template.format(
        changes=changes,
        user=user,
        email=email,
        date=datetime.now().strftime(date_format)
        )
    try:
        preexisting = os.path.getsize(path)
    except:
        preexisting = False
    with open(path, 'a') as changelog:
        if preexisting:
            changelog.write('\n')
        changelog.write(entry)
