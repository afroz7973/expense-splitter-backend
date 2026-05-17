from django.urls import path
from .views import RegisterView,LoginView,GroupView,ExpenseView,GroupBalanceView,AddMemberView,GroupExpenseView,SettleView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/register/',RegisterView.as_view()),
    path('auth/login/',LoginView.as_view()),
    path('auth/refresh/',TokenRefreshView.as_view()),
    path('groups/',GroupView.as_view()),
    path('expenses/',ExpenseView.as_view()),
    path('groups/<int:group_id>/balances/', GroupBalanceView.as_view()),
    path('groups/<int:group_id>/members/', AddMemberView.as_view()),
    path('groups/<int:group_id>/expenses/', GroupExpenseView.as_view()),
    path('groups/<int:group_id>/settle/', SettleView.as_view()),
]
