from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

DECIMALPLACES = 3
MAXDIGITS = 3 + DECIMALPLACES

# Create your models here.
class Market(models.Model):
	#markets contain multiple options
	name = models.TextField()
	rules = models.TextField()
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	creationdate = models.DateTimeField()

	def save(self, *args, **kwargs):
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

	def __str__(self):
		return self.name

	def mostRecentPrice(self):
		try:
			return Transaction.objects.filter(option=self)[0].price
		except:
			return "-"

	def delete(self,*args,**kwargs):
		#reevaluate all the transactions involving this if an option is deleted
		super().delete(*args,**kwargs)

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
		self.creationdate = timezone.now()
		super().save(*args,**kwargs)

class Portfolio(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	market = models.ForeignKey(Market, on_delete=models.CASCADE)
	balance = models.FloatField()

	def addBalance(self, amount):
		self.balance += amount;
		self.save()

	def __str__(self):
		return "%s's portfolio in %s" %(self.owner, self.market)

def makeNewPortfolioIfNonexistent(newUser,newMarket):
	if len(Portfolio.objects.filter(owner=newUser,market=newMarket)) == 0:
		newPortfolio = Portfolio()
		newPortfolio.owner = newUser;
		newPortfolio.market = newMarket;
		newPortfolio.balance = 1000;
		newPortfolio.save();

from . import signals