# import threading

# _thread_locals = threading.local()


# def get_current_user():
#     """
#     Retourne l'utilisateur courant (si connecté), ou None.
#     """
#     return getattr(_thread_locals, "user", None)


# def get_current_request():
#     """
#     Retourne la requête courante (utile pour récupérer IP, headers, etc.).
#     """
#     return getattr(_thread_locals, "request", None)


# def get_current_ip():
#     """
#     Retourne l'adresse IP du client, avec gestion X-Forwarded-For si le site est derrière un proxy.
#     """
#     request = get_current_request()
#     if not request:
#         return None

#     # Si derrière un Nginx / Proxy
#     xff = request.META.get("HTTP_X_FORWARDED_FOR")
#     if xff:
#         # Peut contenir plusieurs IP (client, proxy1, proxy2...)
#         return xff.split(",")[0].strip()

#     # Sinon IP classique
#     return request.META.get("REMOTE_ADDR")


# class CurrentUserMiddleware:
#     """
#     Middleware qui sauvegarde:
#       - request.user (si authentifié)
#       - la requête elle-même (utile pour IP, headers...)
#     dans des thread-locals afin que les signaux puissent l'utiliser.
#     """

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Stocker user et request dans le thread courant
#         _thread_locals.user = request.user if request.user.is_authenticated else None
#         _thread_locals.request = request

#         try:
#             response = self.get_response(request)
#             return response
#         finally:
#             # IMPORTANT : nettoyer pour éviter fuites mémoire ou mélange entre requêtes
#             for attr in ("user", "request"):
#                 if hasattr(_thread_locals, attr):
#                     delattr(_thread_locals, attr)


import threading

_thread_locals = threading.local()


def get_current_user():
    """
    Retourne l'utilisateur courant (User ou AnonymousUser), ou None.
    """
    return getattr(_thread_locals, "user", None)


def get_current_request():
    """
    Retourne la requête courante (utile pour IP, headers, etc.).
    """
    return getattr(_thread_locals, "request", None)


def get_current_ip():
    """
    Retourne l'adresse IP du client, avec gestion X-Forwarded-For si proxy.
    """
    request = get_current_request()
    if not request:
        return None

    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


class CurrentUserMiddleware:
    """
    Middleware qui sauvegarde :
      - request.user (AUTHENTIFIÉ ou ANONYME)
      - la requête courante
    pour utilisation dans les signaux.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 🔥 TOUJOURS stocker request.user, sans condition
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.request = request

        try:
            response = self.get_response(request)
            return response
        finally:
            # 🔒 Nettoyage obligatoire (sécurité mémoire)
            for attr in ("user", "request"):
                if hasattr(_thread_locals, attr):
                    delattr(_thread_locals, attr)
