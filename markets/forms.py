from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import Market, Option, BuyOrder, SellOrder

class createMarketForm(forms.ModelForm):
	class Meta:
		model = Market
		fields = ['name', 'desc', 'rules']
		labels = {
			'desc': _('Description')
		}

class createOptionForm(forms.ModelForm):
	class Meta:
		model = Option
		fields = ['name']

class resolveOptionForm(forms.ModelForm):
	class Meta:
		model = Option
		fields = ['resolveprice']
		labels = {
			'resolveprice': _('Resolution Price'),
		}

class buyOfferForm(forms.ModelForm):
	def clean_maxPrice(self):
		data = self.cleaned_data['maxPrice']
		if data <= 0:
			raise ValidationError(_('Price must be positive.'))

		return data

	def clean_maxNumber(self):
		data = self.cleaned_data['maxNumber']
		if data <= 0:
			raise ValidationError(_('Number bought must be positive.'))

		return data

	class Meta:
		model = BuyOrder
		fields = ['maxPrice', 'maxNumber']
		labels = {
			'maxPrice': _('Max Price'),
			'maxNumber': _('Max Number')
		}

class sellOfferForm(forms.ModelForm):
	def clean_maxPrice(self):
		data = self.cleaned_data['minPrice']
		if data <= 0:
			raise ValidationError(_('Price must be positive.'))
		
		return data

	def clean_maxNumber(self):
		data = self.cleaned_data['maxNumber']
		if data <= 0:
			raise ValidationError(_('Number bought must be positive.'))
		
		return data

	class Meta:
		model = SellOrder
		fields = ['minPrice','maxNumber']
		labels = {
			'minPrice': _('Min Price'),
			'maxNumber': _('Max Number'),
		}

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class customUserCreationForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = User
		fields = UserCreationForm.Meta.fields# + ('email',)
