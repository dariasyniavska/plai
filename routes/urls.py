from django.urls import path
from . import views

urlpatterns = [
    path('mountain-ranges/', views.MountainRangeList.as_view(), name='range-list'),
    path('mountain-ranges/<int:pk>/', views.MountainRangeDetail.as_view(), name='range-detail'),
    path('mountain-ranges/<int:pk>/routes/', views.MountainRangeRoutesList.as_view()),
    path('starting-points/', views.StartingPointList.as_view(), name='point-list'),
    path('starting-points/<int:pk>/', views.StartingPointDetail.as_view(), name='point-detail'),
    path('routes/', views.RouteList.as_view(), name='route-list'),
    path('routes/<int:pk>/', views.RouteDetail.as_view(), name='route-detail'),
    path('starting-points/<int:pk>/routes/', views.StartingPointRoutesList.as_view()),
]
