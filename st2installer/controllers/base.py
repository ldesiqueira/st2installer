import six
from six.moves.urllib import parse as urlparse


class BaseController(object):
    def _parse_query_params(self, request):
        """
        Parse query string for the provided request.

        :rtype: ``dict``
        """
        query_string = request.query_string
        query_params = dict(urlparse.parse_qsl(query_string))

        return query_params

    def _get_query_param_value(self, request, param_name, param_type, default_value=None):
        """
        Return a value for the provided query param and optionally cast it for boolean types.

        If the requested query parameter is not provided, default value is returned instead.

        :param request: Request object.

        :param param_name: Name of the param to retrieve the value for.
        :type param_name: ``str``

        :param param_type: Type of the query param (e.g. "bool").
        :type param_type: ``str``

        :param default_value: Value to return if query param is not provided.
        :type default_value: ``object``
        """
        query_params = self._parse_query_params(request=request)
        value = query_params.get(param_name, default_value)

        if param_type == 'bool' and isinstance(value, six.string_types):
            value = value.lower() in ['1', 'true']

        return value
    pass
