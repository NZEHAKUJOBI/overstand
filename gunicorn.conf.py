def post_fork(server, worker):
    from django.conf import settings
    if not settings.configured:
        return
    from django.db import connections
    connections.close_all()
