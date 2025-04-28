from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ExpenseForm, CategoryForm, BudgetForm
from .models import Expense, Budget, Category
from django.db.models import Sum
import google.generativeai as genai
from django.conf import settings
from django.db.models.functions import TruncMonth, TruncYear
from django import forms
from django.http import JsonResponse
import json
import re

genai.configure(api_key='AIzaSyBQUa463K68FJnD3dG9pIA9snMtYQ-81A8')
model = genai.GenerativeModel('gemini-2.0-flash')

@login_required
def expenses(request):
    user_expenses = Expense.objects.filter(user=request.user).order_by('-date')
    form = ExpenseForm()  # Initialize the form for the modal
    for field_name in form.fields:
        if isinstance(form.fields[field_name], (forms.CharField, forms.ChoiceField, forms.DecimalField, forms.DateField)):
            form.fields[field_name].widget.attrs.update({
                'class': 'shadow border-2 rounded-2xl w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline pl-8'
            })
    
    form.fields['category'].widget.attrs.update({
        'class': 'shadow border-2 rounded-2xl w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline pl-8',
        'placeholder': 'Choose Category'
    })
    form.fields['amount'].widget.attrs.update({
        'class': 'shadow border-2 rounded-2xl w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline pl-8',
        'placeholder': 'Enter Amount'
    })
    form.fields['description'].widget.attrs.update({
        'class': 'shadow border-2 rounded-2xl w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline pl-8',
        'placeholder': 'Enter Description'
    })

    context = {
        'expenses': user_expenses,
        'form': form,
    }
    return render(request, 'tracker/expenses.html', context)

@login_required
def add_expense_modal(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
          # Add class to category field
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('tracker:expenses')  # Redirect back to the expenses page
    return redirect('tracker:expenses') # If not POST, redirect back



@login_required
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')[:10]
    budget_items = Budget.objects.filter(category__expense__user=request.user).distinct()
    category_expenses = Expense.objects.filter(user=request.user).values('category__name').annotate(total=Sum('amount'))

    # Prepare data for monthly expense graph
    monthly_expense_data = Expense.objects.filter(user=request.user).annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')
    monthly_labels = [item['month'].strftime('%b %Y') for item in monthly_expense_data]
    monthly_totals = [float(item['total']) for item in monthly_expense_data]

    # Prepare data for monthly category expense pie chart
    category_labels = [item['category__name'] for item in category_expenses]
    category_totals = [float(item['total']) for item in category_expenses]

    # Prepare data for Gemini
    monthly_expenses_gemini = Expense.objects.filter(user=request.user).values('category__name', 'date__month', 'date__year').annotate(total=Sum('amount')).order_by('-date__year', '-date__month')
    prompt_text = f"Analyze my monthly expenses and provide insights. My expenses are: {monthly_expenses_gemini}"
    try:
        response = model.generate_content(prompt_text)
        gemini_analysis = response.text
    except Exception as e:
        gemini_analysis = f"Error getting Gemini analysis: {e}"

    context = {
        'recent_expenses': expenses,
        'budget_items': budget_items,
        'category_expenses': category_expenses,
        'gemini_analysis': gemini_analysis,
        'monthly_labels': monthly_labels,
        'monthly_totals': monthly_totals,
        'category_labels': category_labels,
        'category_totals': category_totals,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def set_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            # Ensure only one budget per category per user (you might need to adjust this logic)
            existing_budget = Budget.objects.filter(category=budget.category).first()
            if existing_budget:
                existing_budget.limit = budget.limit
                existing_budget.save()
            else:
                budget.save()
            return redirect('tracker:dashboard')
    else:
        form = BudgetForm()
    return render(request, 'tracker/set_budget.html', {'form': form})


@login_required
def generate_smart_budget(request):
    user_expenses = Expense.objects.filter(user=request.user).values('category__name').annotate(total=Sum('amount'))

    if not user_expenses:
        return JsonResponse({'error': 'No spending data available to generate a smart budget.'})

    prompt_text = """Analyze my recent monthly spending: {}. Based on these patterns, suggest a monthly budget allocation for each category. My salary is ₹50,000.
    I want to save 20% of my income. Provide a reasonable budget for each category, ensuring that the total does not exceed my salary after savings.
Return the budget as a valid JSON object with the following structure:
{{
  "Category Name 1": Budget Amount 1,
  "Category Name 2": Budget Amount 2,
  ...
}}

Be reasonable with the budget amounts and consider common budgeting practices. Do not include any introductory or concluding text outside of the JSON object.
""".format(list(user_expenses))

    try:
        response = model.generate_content(prompt_text)
        gemini_output = response.text

        json_match = re.search(r'\{[\s\S]*\}', gemini_output)
        if json_match:
            json_string = json_match.group(0)
            try:
                suggestions = json.loads(json_string)
                return JsonResponse({'suggestions': suggestions})
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Failed to parse the extracted JSON from Gemini AI response.'})
        else:
            return JsonResponse({'error': 'Failed to find a JSON object in Gemini AI response.'})

    except Exception as e:
        return JsonResponse({'error': f'Error communicating with Gemini AI: {e}'})
    
    

@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tracker:add_category') # Redirect to set budget after adding category
    else:
        form = CategoryForm()
    return render(request, 'tracker/add_category.html', {'form': form})

# @login_required
# def get_financial_advice(request):
#     advice = "Personalized financial advice powered by Gemini AI will appear here."
#     return render(request, 'tracker/financial_advice.html', {'advice': advice})

# ... (your report generation views remain the same for now) ...

@login_required
def monthly_report(request):
    user_expenses = Expense.objects.filter(user=request.user)
    monthly_data = user_expenses.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('-month')

    prompt_text = f"Analyze my monthly expenses: {list(monthly_data)}. Provide a summary and identify any trends."
    try:
        response = model.generate_content(prompt_text)
        report_analysis = response.text
    except Exception as e:
        report_analysis = f"Error generating monthly report analysis: {e}"

    context = {
        'report_data': monthly_data,
        'report_analysis': report_analysis,
        'report_type': 'Monthly',
    }
    return render(request, 'tracker/report_detail.html', context)

@login_required
def annual_report(request):
    user_expenses = Expense.objects.filter(user=request.user)
    annual_data = user_expenses.annotate(year=TruncYear('date')).values('year').annotate(total=Sum('amount')).order_by('-year')

    prompt_text = f"Analyze my annual expenses: {list(annual_data)}. Provide a summary and identify any trends."
    try:
        response = model.generate_content(prompt_text)
        report_analysis = response.text
    except Exception as e:
        report_analysis = f"Error generating annual report analysis: {e}"

    context = {
        'report_data': annual_data,
        'report_analysis': report_analysis,
        'report_type': 'Annual',
    }
    return render(request, 'tracker/report_detail.html', context)

@login_required
def category_report(request):
    user_expenses = Expense.objects.filter(user=request.user)
    category_data = user_expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')

    prompt_text = f"Analyze my expenses by category: {list(category_data)}. Identify the highest and lowest spending categories."
    try:
        response = model.generate_content(prompt_text)
        report_analysis = response.text
    except Exception as e:
        report_analysis = f"Error generating category report analysis: {e}"

    context = {
        'report_data': category_data,
        'report_analysis': report_analysis,
        'report_type': 'Category',
    }
    return render(request, 'tracker/report_detail.html', context)

@login_required
def saving_potential_report(request):
    user_expenses = Expense.objects.filter(user=request.user)
    monthly_income = 10000  # Replace with actual income source or user input
    monthly_spent = user_expenses.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('-month').first()

    saving_potential = monthly_income - (monthly_spent['total'] if monthly_spent else 0)

    prompt_text = f"Based on a monthly income of {monthly_income} and monthly spending of {monthly_spent}, what is my saving potential and how can I improve it?"
    try:
        response = model.generate_content(prompt_text)
        report_analysis = response.text
    except Exception as e:
        report_analysis = f"Error generating saving potential report analysis: {e}"

    context = {
        'saving_potential': saving_potential,
        'report_analysis': report_analysis,
        'report_type': 'Saving Potential',
    }
    return render(request, 'tracker/saving_potential_report.html', context)

@login_required
def reports(request):
    return render(request, 'tracker/report.html')


@login_required
def get_ai_insights(request):
    user_expenses = Expense.objects.filter(user=request.user)
    monthly_spending = user_expenses.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('-month')
    category_spending = user_expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')

    # Hypothetical monthly salary (you might want to get this from user profile or settings)
    hypothetical_salary = 50000  # Example salary in INR

    expense_data_prompt = f"""
Monthly Spending: {list(monthly_spending)}. 
Spending by Category: {list(category_spending)}.
The user’s total monthly spending exceeds their income. This will help to assess the overall spending patterns.
"""
    # Prepare prompts for both insights and advice
    insights_prompt = f"""
Analyze the following expense data:
- Monthly Spending: {list(monthly_spending)}
- Spending by Category: {list(category_spending)}

Provide 2-3 key insights about the user's spending habits. Each insight should have:
1. A title that summarizes the insight.
2. A description that explains the context or details about the insight.

Format:
[
  {{
    "title": "Insight Title",
    "content": "Insight Description"
  }},
  ...
]
"""
    
    advice_prompt = f"""
Based on the following data:
- Monthly Spending: {list(monthly_spending)}
- Spending by Category: {list(category_spending)}
- Monthly Salary: {hypothetical_salary} INR

Provide 2-3 concise points of financial advice, focusing on actionable strategies for optimizing spending, reducing expenses, and balancing the budget based on income. Each piece of advice should include:
1. A title that summarizes the advice.
2. A description that explains how the advice can be implemented.

Format:
[
  {{
    "title": "Advice Title",
    "content": "Advice Description"
  }},
  ...
]
"""

    
    try:
        insights_response = model.generate_content(insights_prompt)
        insights_text = insights_response.text.strip().split('\n')
        insights = [insight.lstrip('- ') for insight in insights_text if insight.strip()]
    except Exception as e:
        insights = [f"Error getting spending insights: {e}"]

    try:
        advice_response = model.generate_content(advice_prompt)
        advice_text = advice_response.text.strip()
    except Exception as e:
        advice_text = f"Error getting financial advice: {e}"

    return JsonResponse({'insights': insights, 'advice': advice_text})