from django.urls import path
from . import views

app_name = 'markets'
urlpatterns = [
	path('', views.index, name='index'),
	path('create', views.createMarketView, name='create-market'),
	path('<int:marketid>', views.marketView, name='market-detail'),
	path('tradeon/<int:optionid>', views.optionView, name='option-detail'),
	path('<int:marketid>/edit', views.editMarketView, name='market-edit'),
	path('<int:marketid>/newoption', views.createOptionView, name='option-create'),
	path('tradeon/<int:optionid>/edit', views.editOptionView, name='option-edit'),
	path('sign-up', views.signUp, name='sign-up'),
]