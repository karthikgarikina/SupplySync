from django.core.cache import cache
from rest_framework.throttling import SimpleRateThrottle

from core import constants


class LoginRateLimitThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        return constants.CACHE_KEY_LOGIN_RATE_LIMIT.format(ip_address=self.get_ident(request))

    def allow_request(self, request, view):
        self.key = self.get_cache_key(request, view)
        attempts = cache.get(self.key, 0)
        return attempts < constants.LOGIN_RATE_LIMIT_MAX_ATTEMPTS

    def wait(self):
        return None

    def register_failure(self, request):
        key = constants.CACHE_KEY_LOGIN_RATE_LIMIT.format(ip_address=self.get_ident(request))
        cache.add(key, 0, timeout=constants.LOGIN_RATE_LIMIT_TTL)
        try:
            return cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=constants.LOGIN_RATE_LIMIT_TTL)
            return 1

    def clear(self, request):
        key = constants.CACHE_KEY_LOGIN_RATE_LIMIT.format(ip_address=self.get_ident(request))
        cache.delete(key)
