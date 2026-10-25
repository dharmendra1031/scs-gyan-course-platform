from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from config.seo import robots_txt, sitemaps
from config.health import health_check
from django.urls import include, path

urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("management/", include("management.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("account/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("assessments/", include("exams.urls")),
    path("articles/", include("articles.urls")),
    path("", include("pages.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
