from fun_settings import COMMON_WEB_LOGGER_NAME
from web.web_global import api_safe_json_response
from fun_global import get_epoch_time_from_datetime
from datetime import datetime
from web.fun_test.models import Profile
from django.core.exceptions import ObjectDoesNotExist
import logging
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)


def to_dict(instance):
    result = {}
    fields = instance._meta.get_fields()
    for field in fields:
        value = getattr(instance, field.name)
        result[field.name] = value
        if type(value) == datetime:
            result[field.name + "_timestamp"] = get_epoch_time_from_datetime(value)
    return result


@api_safe_json_response
def user_profiles(request):
    result = None
    if request.method == "GET" and request.user:
        if not request.user.is_anonymous():
            try:
                profile = Profile.objects.get(user=request.user)
                result = to_dict(profile)
                user_dict = {"email": profile.user.email,
                             "first_name": profile.user.first_name,
                             "last_name": profile.user.last_name,
                             "is_authenticated": profile.user.is_authenticated(),
                             "is_active": profile.user.is_active,
                             "id": profile.user.id}
                result["user"] = user_dict
            except ObjectDoesNotExist:
                error_message = "Unable to retrieve profile for {}".format(request.user)
                logger.error(error_message)
                raise Exception(error_message)
        else:
            result = {"is_anonymous": True}
    return result

