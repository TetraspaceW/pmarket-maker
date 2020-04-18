import datetime

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.urls import reverse,reverse_lazy

from .models import Market, Option, BuyOrder, SellOrder, Portfolio
from .forms import createMarketForm, createOptionForm, buyOfferForm, sellOfferForm, resolveOptionForm, customUserCreationForm

# Create your views here.
def index(request):
	market_list = Market.objects.all()
	context = {
		'market_list': market_list
		}
	return render(request, 'markets/index.html', context)

def marketView(request, marketid):
	market = get_object_or_404(Market, pk=marketid)
	try:
		portfolio = Portfolio.objects.filter(market=market).get(owner=request.user)
	except:
		portfolio = False;


	context = {
		'market': market,
		'portfolio': portfolio
	}

	return render(request, 'markets/detail.html', context)

@login_required
def optionView(request, optionid):
	option = get_object_or_404(Option, pk=optionid)

	sellForm = sellOfferForm()
	buyForm = buyOfferForm()

	if request.method == "POST":
		if 'buyofferbutton' in request.POST:
			buyForm = buyOfferForm(request.POST)

			if buyForm.is_valid():
				newbuyorder = BuyOrder()
				newbuyorder.option = option
				newbuyorder.maxPrice = buyForm.cleaned_data['maxPrice']
				newbuyorder.maxNumber = buyForm.cleaned_data['maxNumber']
				newbuyorder.creator = request.user
				newbuyorder.creationdate = datetime.datetime.now()
				newbuyorder.save()
				return HttpResponseRedirect(reverse('markets:option-detail', args=[optionid]))

		elif 'sellofferbutton' in request.POST:
			sellForm = sellOfferForm(request.POST)

			if sellForm.is_valid():
				newsellorder = SellOrder()
				newsellorder.option = option
				newsellorder.minPrice = sellForm.cleaned_data['minPrice']
				newsellorder.maxNumber = sellForm.cleaned_data['maxNumber']
				newsellorder.creator = request.user
				newsellorder.creationdate = datetime.datetime.now()
				newsellorder.save()
				return HttpResponseRedirect(reverse('markets:option-detail', args=[optionid]))

	try:
		portfolio = Portfolio.objects.filter(market=option.market).get(owner=request.user)
	except:
		portfolio = False;			

	context = {
		'option': option,
		'buyform': buyForm,
		'sellform': sellForm,
		'buyorder_list': option.buyorder_set.all(),
		'sellorder_list': option.sellorder_set.all(),
		'portfolio': portfolio
	}
	return render(request, 'markets/trade.html', context)

def createMarketView(request):

	if request.method == "POST":
		form = createMarketForm(request.POST)

		if form.is_valid():
			newmarket = Market()
			newmarket.name = form.cleaned_data['name']
			newmarket.rules = form.cleaned_data['rules']
			newmarket.owner = request.user
			newmarket.save()
			return HttpResponseRedirect(reverse('markets:market-detail', args=[newmarket.id]))
	else:
		form = createMarketForm()

	context = {
		'form': form
	}

	return render(request, 'markets/market_create.html', context)

def createOptionView(request, marketid):
	if request.method == "POST":
		form = createOptionForm(request.POST)
		if form.is_valid():
			newoption = Option()
			newoption.name = form.cleaned_data['name']
			newoption.market = get_object_or_404(Market, pk=marketid)
			newoption.save()
			return HttpResponseRedirect(reverse('markets:market-detail', args=[marketid]))
	else:
		form = createOptionForm()

	context = {
		'form': form,
		'market': get_object_or_404(Market, pk=marketid)
	}

	return render(request, 'markets/option_create.html', context)

def signUp(request):
	form = customUserCreationForm()
	if request.method == "POST":
		form = customUserCreationForm(request.POST)
		if form.is_valid():
			form.save()
			username = form.cleaned_data['username']
			raw_password = form.cleaned_data['password1']
			email = form.cleaned_data['email']
			user = authenticate(username=username, email=email, password=raw_password)
			login(request, user)
			return HttpResponseRedirect(reverse('markets:index'))

	context = {
		'form':form,
	}
	
	return render(request, 'signup.html', context)

def editMarketView(request, marketid):
	market = get_object_or_404(Market, pk=marketid)
	form = createMarketForm(initial={'name':market.name, 'rules':market.rules})

	if request.method == "POST":
		form = createMarketForm(request.POST)
		if form.is_valid():
			market.name = form.cleaned_date['name']
			market.rules = form.cleaned_date['rules']


	context = {
		'market': market,
		'form': form
		}
	return render(request, 'markets/market_edit.html', context)

def editOptionView(request, optionid):
	option = get_object_or_404(Option, pk=optionid)
	editForm = createOptionForm(initial={'name': option.name})
	resolveForm = resolveOptionForm()

	if request.method == "POST":
		if 'editbutton' in request.POST:
			editForm = createOptionForm(request.POST)
			if editForm.is_valid():
				option.name = editForm.cleaned_data['name']
				option.save()
				return HttpResponseRedirect(reverse('markets:market-detail', args=[option.market.id]))

		elif 'resolvebutton' in request.POST:
			resolveForm = resolveOptionForm(request.POST)
			if resolveForm.is_valid():
				option.resolve(resolveForm.cleaned_data['resolveprice'])
				return HttpResponseRedirect(reverse('markets:market-detail', args=[option.market.id]))

	context = {
		'editForm': editForm,
		'resolveForm': resolveForm,
		'option': option
		}

	return render(request, 'markets/option_edit.html', context)