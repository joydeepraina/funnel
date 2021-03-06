from collections import defaultdict
from urllib.parse import urljoin

import requests

from baseframe import __, statsd

from .. import app, funnelapp, rq
from ..extapi.boxoffice import Boxoffice
from ..extapi.explara import ExplaraAPI
from ..models import EmailAddress, Project, ProjectLocation, TicketClient, db


@rq.job('funnel')
def import_tickets(ticket_client_id):
    with funnelapp.app_context():
        ticket_client = TicketClient.query.get(ticket_client_id)
        if ticket_client:
            if ticket_client.name.lower() == 'explara':
                ticket_list = ExplaraAPI(
                    access_token=ticket_client.client_access_token
                ).get_tickets(ticket_client.client_eventid)
                ticket_client.import_from_list(ticket_list)
            elif ticket_client.name.lower() == 'boxoffice':
                ticket_list = Boxoffice(
                    access_token=ticket_client.client_access_token
                ).get_tickets(ticket_client.client_eventid)
                ticket_client.import_from_list(ticket_list)
            db.session.commit()


@rq.job('funnel')
def tag_locations(project_id):
    if app.config.get('HASCORE_SERVER'):
        with app.test_request_context():
            project = Project.query.get(project_id)
            if not project.location:
                return
            url = urljoin(app.config['HASCORE_SERVER'], '/1/geo/parse_locations')
            response = requests.get(
                url,
                params={
                    'q': project.location,
                    'bias': ['IN', 'US'],
                    'special': ['Internet', 'Online', __('Internet'), __('Online')],
                },
            ).json()

            if response.get('status') == 'ok':
                results = response.get('result', [])
                geonames = defaultdict(dict)
                tokens = []
                for item in results:
                    geoname = item.get('geoname', {})
                    if geoname:
                        geonames[geoname['geonameid']]['geonameid'] = geoname[
                            'geonameid'
                        ]
                        geonames[geoname['geonameid']]['primary'] = geonames[
                            geoname['geonameid']
                        ].get('primary', True)
                        for gtype, related in geoname.get('related', {}).items():
                            if gtype in ['admin2', 'admin1', 'country', 'continent']:
                                geonames[related['geonameid']]['geonameid'] = related[
                                    'geonameid'
                                ]
                                geonames[related['geonameid']]['primary'] = False

                        tokens.append(
                            {
                                'token': item.get('token', ''),
                                'geoname': {
                                    'name': geoname['name'],
                                    'geonameid': geoname['geonameid'],
                                },
                            }
                        )
                    else:
                        tokens.append({'token': item.get('token', '')})

                project.parsed_location = {'tokens': tokens}

                for locdata in geonames.values():
                    loc = ProjectLocation.query.get((project_id, locdata['geonameid']))
                    if loc is None:
                        loc = ProjectLocation(
                            project=project, geonameid=locdata['geonameid']
                        )
                        db.session.add(loc)
                        db.session.flush()
                    loc.primary = locdata['primary']
                for location in project.locations:
                    if location.geonameid not in geonames:
                        db.session.delete(location)
                db.session.commit()


@rq.job('funnel')
def send_auth_client_notice(url, params=None, data=None, method='POST'):
    requests.request(method, url, params=params, data=data)


@rq.job('funnel')
def forget_email(email_hash):
    with app.app_context():
        email_address = EmailAddress.get(email_hash=email_hash)
        if email_address.refcount() == 0:
            app.logger.info("Forgetting email address with hash %s", email_hash)
            email_address.email = None
            db.session.commit()
            statsd.incr('email_address.forgotten')
