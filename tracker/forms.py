from django import forms
from .models import Category, Expense, Budget

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'amount', 'category', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'limit']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}), # For better styling
            'limit': forms.NumberInput(attrs={'class': 'form-control'}), # For better styling
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Select Category"