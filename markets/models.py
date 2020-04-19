from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

DECIMALPLACES = 3
MAXDIGITS = 3 + DECIMALPLACES

INITIALBALANCE = 1000

# Create your models here.
class Market(models.Model):
	#markets contain multiple options
	name = models.TextField()
	desc = models.TextField(blank=True)
	rules = models.TextField(blank=True)
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	curated = models.BooleanField(default=False)
	creationdate = models.DateTimeField()

	def save(self, *args, **kwargs):
		if not self.id:
			self.creationdate = timezone.now()
		super().save(*args,**kwargs)

	def __str__(self):
		return self.name

class Option(models.Model):
	#each option has some shares associated with it that expire at $1 or $0
	name = models.TextField()
	market = models.ForeignKey(Market, on_delete=models.CASCADE)
	closed = models.BooleanField(default=False)
	resolveprice =  models.DecimalField(default=0, max_digits=MAXDIGITS, decimal_places=DECIMALPLACES)
	tag = models.SlugField(blank=True)

	def __str__(self):
		return self.name

	def mostRecentPrice(self):
		try:
			if not self.closed:
				return Transaction.objects.filter(option=self)[0].price
			else:
				return self.resolveprice
		except:
			return None

	def delete(self,*args,**kwargs):
		#reevaluate all the transactions involving this if an option is deleted
		usersOwningThis = list(User.objects.filter(soldIn__option = self).union(User.objects.filter(boughtIn__option = self)))
		marketTradedIn = self.market

		super().delete(*args,**kwargs)

		for user in usersOwningThis:
			portfolios = Portfolio.objects.filter(market=marketTradedIn).filter(owner=user)
			for p in portfolios:
				p.balance = p.recalculateBalance()
				p.save()
		

	def resolve(self,price):
		self.resolveprice = price;
		self.closed = True;
		self.save()

		#do something with all the portfolios
		tradesInvolvingThis = Transaction.objects.filter(option=self)
		for trade in tradesInvolvingThis:
			marketPortfolio = Portfolio.objects.filter(market=self.market)
			buyerPortfolio = marketPortfolio.get(owner=trade.buyer)
			buyerPortfolio.balance += float(price*trade.amount)
			buyerPortfolio.save()

			sellerPortfolio = marketPortfolio.get(owner=trade.seller)
			sellerPortfolio.balance -= float(price*trade.amount)
			sellerPortfolio.save()

#i'm really sorry about these two models by the way
#i only realised they're literally the same thing after writing them
#i'll merge these guys or make them inherit from the same class or whatever later
#TODO: making these orders should probably bind up some of your capital
class BuyOrder(models.Model):
	maxPrice = models.DecimalField(default=0, max_digits=MAXDIGITS, decimal_places=DECIMALPLACES)
	maxNumber = models.IntegerField(default=0) 
	option = models.ForeignKey(Option, on_delete=models.CASCADE)
	creator = models.ForeignKey(User, on_delete=models.CASCADE)
	creationdate = models.DateTimeField()

	def __str__(self):
		return "Offer to buy %d of %s for %d" %(self.maxNumber, self.option.name, self.maxPrice)

	class Meta:
		ordering = ['-maxPrice','-creationdate']

	def save(self,*args,**kwargs):
		if not self.id:
			self.creationdate = timezone.now()
		makeNewPortfolioIfNonexistent(self.creator,self.option.market)
		super().save(*args,**kwargs)

 
class SellOrder(models.Model):
	minPrice = models.DecimalField(default=0, max_digits=MAXDIGITS, decimal_places=DECIMALPLACES)
	maxNumber = models.IntegerField(default=0) 
	option = models.ForeignKey(Option, on_delete=models.CASCADE)
	creator = models.ForeignKey(User, on_delete=models.CASCADE)
	creationdate = models.DateTimeField()

	def __str__(self):
		return "Offer to sell %d of %s for %d" %(self.maxNumber, self.option.name, self.minPrice)

	class Meta:
		ordering = ['minPrice','-creationdate']

	def save(self,*args,**kwargs):
		if not self.id:
			self.creationdate = timezone.now()
		makeNewPortfolioIfNonexistent(self.creator,self.option.market)
		super().save(*args,**kwargs)

class Transaction(models.Model):
	seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="soldIn")
	buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="boughtIn")
	amount = models.IntegerField(default=0)
	price = models.DecimalField(default=0, max_digits=MAXDIGITS, decimal_places=DECIMALPLACES)
	option = models.ForeignKey(Option, on_delete=models.CASCADE)
	creationdate = models.DateTimeField()
	def __str__(self):
		return "%s sold %d of %s to %s for %d" %(self.seller, self.amount, self.option, self.buyer, self.price) 

	class Meta:
		ordering = ['-creationdate']

	def save(self,*args,**kwargs):
		if not self.id:
			self.creationdate = timezone.now()
		super().save(*args,**kwargs)

class Portfolio(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	market = models.ForeignKey(Market, on_delete=models.CASCADE)
	balance = models.FloatField()

	def addBalance(self, amount):
		self.balance += amount;
		self.save()

	def recalculateBalance(self):
		#recalculates balance from transaction and option resolution history
		transactionsInMarket = Transaction.objects.filter(option__market=self.market)
		purchasesInMarket = transactionsInMarket.filter(buyer=self.owner)
		salesInMarket = transactionsInMarket.filter(seller=self.owner)

		resolvedOptionsInMarket = Option.objects.filter(market=self.market).filter(closed=True)

		bal = INITIALBALANCE
		for transaction in salesInMarket:
			bal += float(transaction.amount * transaction.price)
		for transaction in purchasesInMarket:
			bal -= float(transaction.amount * transaction.price)

		for option in resolvedOptionsInMarket:
			optionPurchases = purchasesInMarket.filter(option=option)
			optionSales = salesInMarket.filter(option=option)
			for transaction in optionPurchases:
				bal += float(option.resolveprice * transaction.amount)
			for transaction in optionSales:
				bal -= float(option.resolveprice * transaction.amount)

		return bal



	def displayNetWorth(self):
		networth = self.balance

		# add expected value of options that have not yet paid out
		transactionsInMarket = Transaction.objects.filter(option__market=self.market)
		for transaction in transactionsInMarket.filter(seller=self.owner):
			if transaction.option.mostRecentPrice() and not transaction.option.closed:
				networth -= float(transaction.amount * transaction.option.mostRecentPrice())

		for transaction in transactionsInMarket.filter(buyer=self.owner):
			if transaction.option.mostRecentPrice() and not transaction.option.closed:
				networth += float(transaction.amount * transaction.option.mostRecentPrice())

		return networth

	def __str__(self):
		return "%s's portfolio in %s" %(self.owner, self.market)

def makeNewPortfolioIfNonexistent(newUser,newMarket):
	if len(Portfolio.objects.filter(owner=newUser,market=newMarket)) == 0:
		newPortfolio = Portfolio()
		newPortfolio.owner = newUser;
		newPortfolio.market = newMarket;
		newPortfolio.balance = INITIALBALANCE;
		newPortfolio.save();

from . import signals