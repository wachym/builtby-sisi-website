"""URL configuration.

The API is versioned in the path from the first commit: /api/v1/. A second
version can be mounted alongside without breaking a deployed frontend.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path

from bbsbackend.api import api

urlpatterns = [
    path(settings.API_PREFIX, api.urls),
    path("admin/", admin.site.urls),
]
