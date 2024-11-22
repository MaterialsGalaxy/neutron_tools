from bioblend.galaxy import GalaxyInstance
import pandas as pd
import subprocess
import logging
import os

DEBUG = os.environ.get('DEBUG', "False").lower() == 'true'
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
logging.getLogger("bioblend").setLevel(logging.CRITICAL)
log = logging.getLogger()


def _get_ip():
    """Get IP address for the docker host
    """
    cmd_netstat = ['netstat', '-nr']
    p1 = subprocess.Popen(cmd_netstat, stdout=subprocess.PIPE)
    cmd_grep = ['grep', '^0\.0\.0\.0']
    p2 = subprocess.Popen(cmd_grep, stdin=p1.stdout, stdout=subprocess.PIPE)
    cmd_awk = ['awk', '{ print $2 }']
    p3 = subprocess.Popen(cmd_awk, stdin=p2.stdout, stdout=subprocess.PIPE)
    galaxy_ip = p3.stdout.read()
    log.debug('Host IP determined to be %s', galaxy_ip)
    return galaxy_ip


def get_galaxy_connection(history_id=None, obj=True):
    history_id = history_id or os.environ['HISTORY_ID']
    key = os.environ['API_KEY']

    # Customised/Raw galaxy_url
    galaxy_ip = _get_ip()
    # Failover, fully auto-detected URL
    # Remove trailing slashes
    app_path = os.environ['GALAXY_URL'].rstrip('/')
    # Remove protocol+host:port if included
    app_path = ''.join(app_path.split('/')[3:])

    if 'GALAXY_WEB_PORT' not in os.environ:
        # We've failed to detect a port in the config we were given by
        # galaxy, so we won't be able to construct a valid URL
        raise Exception("No port")
    else:
        # We should be able to find a port to connect to galaxy on via this
        # conf var: galaxy_paster_port
        galaxy_port = os.environ['GALAXY_WEB_PORT']

    built_galaxy_url = 'http://%s:%s/%s' % (galaxy_ip.strip(),
                                            galaxy_port, app_path.strip())
    # url = built_galaxy_url.rstrip('/')
    # url = os.environ['GALAXY_URL'].rstrip('/')
    url = 'http://host-172-16-101-76.nubes.stfc.ac.uk/'
    gi = GalaxyInstance(url=url, key=key)
    # gi.histories.get_histories(history_id)
    return gi


def put(filename, file_type='auto', history_id=None):
    """
        Given a filename of any file accessible to the docker instance, this
        function will upload that file to galaxy using the current history.
        Does not return anything.
    """

    gi = get_galaxy_connection(history_id=history_id)
    history_id = os.environ['HISTORY_ID']
    log.debug('Uploading gx=%s history=%s localpath=%s ft=%s', gi, history_id,
              filename, file_type)
    # history = gi.histories.get(history_id)
    # history.upload_file(filename, file_type=file_type)
    gi.tools.upload_file(filename, history_id)


def updateHist():
    history_id = os.environ['HISTORY_ID']
    gi = get_galaxy_connection(history_id=history_id)
    history = gi.histories.show_history(history_id=history_id, contents=True,
                                        deleted=False, visible=True,
                                        types=['dataset'],
                                        keys=['Id', 'Hid', 'Name'])
    histframe = pd.DataFrame(history)
    histtable = histframe[["hid", "name", "id"]]
    return histtable
