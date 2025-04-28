from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'tracker'

urlpatterns = [
    path('expenses/', views.expenses, name='expenses'),
    path('expenses/add/', views.add_expense_modal, name='add_expense_modal'),
    path('set_budget/', views.set_budget, name='set_budget'),
    path('budget/generate_smart/', views.generate_smart_budget, name='generate_smart_budget'),
    path('add_category/', views.add_category, name='add_category'),
    # path('financial_advice/', views.get_financial_advice, name='financial_advice'),
     path('reports/', views.reports, name='report'),
    path('reports/monthly/', views.monthly_report, name='monthly_report'),
    path('reports/annual/', views.annual_report, name='annual_report'),
    path('reports/category/', views.category_report, name='category_report'),
    path('reports/saving_potential/', views.saving_potential_report, name='saving_potential_report'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ai/insights/', views.get_ai_insights, name='get_ai_insights'),
]