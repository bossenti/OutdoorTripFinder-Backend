from flask import Blueprint

from app.auth import http_auth
from app.entities.Statistic import Statistic
from app.entities.entity import Session
from app.entities.hike_relations import HikeRelation
from app.main import count
from app.utils import responses
from app.utils.responses import ResponseMessages, create_response


stats = Blueprint('stats', __name__)


@stats.route('/hikes/<act_id>', methods=['GET'])
@http_auth.login_required
def get_no_hikes(act_id):
    res = count(user=http_auth.current_user, class_type=HikeRelation, **{'activity_id': act_id})

    return res


@stats.route('', methods=['GET'])
@http_auth.login_required
def stats_general():

    session = Session()
    statistic = Statistic.instance(session)

    result = {
        'noTours': statistic.no_activities,
        'noCountry': statistic.no_countries,
        'noRegion': statistic.no_regions,
        'noLocation': statistic.no_locations,
        'popCountry': statistic.pop_country.abbreviation,
        'popRegion': statistic.pop_region.name,
        'popActivityType': statistic.pop_activity_type.name,
        'popActivity': statistic.pop_activity.name
    }

    return create_response(result, responses.SUCCESS_200, ResponseMessages.FIND_SUCCESS, None, 200)

